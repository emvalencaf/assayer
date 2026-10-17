"""LangSmithAdapter: exports an Experiment to LangSmith as an experiment project.

The Cases become examples of a dataset, the Experiment becomes a project that references that
dataset, each Trajectory becomes a run tree (one root run, one child run per Step) linked to its
example, and each Score becomes feedback. Run ids, trace ids and `dotted_order` are generated
here, because the SDK queues runs in the background and does not return them.
"""

import datetime as dt
import os
import time
import uuid
from collections.abc import Callable
from types import TracebackType
from typing import Any, Self

import langsmith
from langsmith.utils import (
    LangSmithAPIError,
    LangSmithAuthError,
    LangSmithConflictError,
    LangSmithConnectionError,
    LangSmithError,
    LangSmithNotFoundError,
    LangSmithRateLimitError,
    LangSmithUserError,
)

from assayer.adapters import (
    AdapterCallError,
    AdapterConfigError,
    ExportReport,
    PlannedItem,
    export_experiment,
    step_id,
    step_key,
    trajectory_id,
)
from assayer.adapters.export import Delivery
from assayer.models import Experiment

_RUN_TYPES = {"model": "llm", "tool": "tool", "retrieval": "retriever", "other": "chain"}
_API_KEY_VARIABLES = ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY")


class LangSmithAdapter:
    """Exports an Experiment to LangSmith. Sync only, not thread-safe: one export at a time.

    Trajectories carry no timing, so runs get a synthetic one: every run of an export starts at
    the time of the Adapter's first export of that Experiment, offset by one microsecond per
    Step so that `dotted_order` keeps the Steps in order. Exporting again from the same Adapter
    reuses that time. Model Steps carry their tokens (and cost, when known) as `usage_metadata`,
    and a Trajectory's totals are in the `assayer.usage` metadata of its root run.

    Args:
        client: A `langsmith.Client`. It is left open by `close`. Without it, one is built from
            `api_key` or the environment.
        api_key: Key for the client the Adapter builds itself. Defaults to `LANGSMITH_API_KEY`,
            then `LANGCHAIN_API_KEY`.
        dataset_name: Name of the LangSmith dataset the Cases go to, created when missing and
            reused otherwise. Defaults to the Experiment's name.
        name: Name of the Adapter. Must be non-empty.
        clock: Gives the current time; injected so tests are deterministic.
        sleep: Waits between retries; pass a no-op in tests.

    Raises:
        AdapterConfigError: If name or dataset_name is empty, or there is no client and no key.
    """

    def __init__(
        self,
        client: langsmith.Client | None = None,
        *,
        api_key: str | None = None,
        dataset_name: str | None = None,
        name: str = "langsmith",
        clock: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.UTC),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not name.strip():
            raise AdapterConfigError("name must not be empty")
        if dataset_name is not None and not dataset_name.strip():
            raise AdapterConfigError("dataset_name must not be empty")
        self._owns_client = client is None
        if client is None:
            key = api_key or next(filter(None, map(os.environ.get, _API_KEY_VARIABLES)), None)
            if not key:
                raise AdapterConfigError(
                    "no LangSmith credentials: set LANGSMITH_API_KEY (or LANGCHAIN_API_KEY), "
                    "pass api_key, or pass a langsmith.Client"
                )
            try:
                client = langsmith.Client(api_key=key)
            except LangSmithError as error:
                raise AdapterConfigError(f"could not build a LangSmith client: {error}") from error
        self.name = name
        self.client = client
        self._dataset_name = dataset_name
        self._clock = clock
        self._sleep = sleep
        self._started: dict[str, dt.datetime] = {}

    def export(self, experiment: Experiment, *, include_content: bool = True) -> ExportReport:
        """Export the Experiment.

        Args:
            experiment: What to export.
            include_content: When False, only structure, Scores and metadata are sent. An
                example that already exists keeps the inputs and references it has.

        Returns:
            The report. Cases and Scores are confirmed; runs are queued in the SDK and flushed
            at the end of the export.
        """
        started = self._started.setdefault(experiment.name, self._clock())
        session = _Export(
            self.client,
            experiment,
            self._dataset_name or experiment.name,
            started,
            include_content,
        )
        report = export_experiment(
            experiment, session.send, include_content=include_content, sleep=self._sleep
        )
        report.notes.extend(session.notes)
        try:
            self.client.flush()
        except Exception as error:
            report.notes.append(f"flushing the queued runs failed: {type(error).__name__}: {error}")
        return report

    def close(self) -> None:
        """Close the client the Adapter built; one passed in is left open."""
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()


class _Export:
    """The state of one export: the dataset and project, and the runs sent so far."""

    def __init__(
        self,
        client: langsmith.Client,
        experiment: Experiment,
        dataset_name: str,
        started: dt.datetime,
        include_content: bool,
    ) -> None:
        self._client = client
        self._experiment = experiment
        self._dataset_name = dataset_name
        self._started = started
        self._include_content = include_content
        self.notes: list[str] = []
        self._dataset_id: uuid.UUID | None = None
        self._project_id: uuid.UUID | None = None
        self._case_inputs: dict[str, dict[str, Any]] = {}
        self._runs: dict[str, tuple[uuid.UUID, str]] = {}  # item id -> (trace id, dotted order)
        self._step_count: dict[str, int] = {}
        self._step_index: dict[str, int] = {}
        for trajectory in experiment.trajectories or []:
            t_id = trajectory_id(experiment.name, trajectory.case_id, trajectory.repetition)
            self._step_count[t_id] = len(trajectory.steps)
            for index in range(len(trajectory.steps)):
                self._step_index.setdefault(step_id(t_id, step_key(trajectory, index)), index)

    def send(self, entry: PlannedItem) -> Delivery | None:
        """Send one planned item, turning the SDK's errors into `AdapterCallError`."""
        send = {
            "case": self._send_case,
            "trajectory": self._send_trajectory,
            "step": self._send_step,
            "score": self._send_score,
        }[entry.item.target_kind]
        try:
            return send(entry.payload)
        except LangSmithError as error:
            raise _call_error(error) from error

    def _ensure_project(self) -> uuid.UUID:
        if self._dataset_id is None:
            if self._client.has_dataset(dataset_name=self._dataset_name):
                dataset = self._client.read_dataset(dataset_name=self._dataset_name)
            else:
                dataset = self._client.create_dataset(
                    self._dataset_name, description="Cases exported by assayer"
                )
            self._dataset_id = dataset.id
        if self._project_id is None:
            project = self._client.create_project(
                self._experiment.name,
                reference_dataset_id=self._dataset_id,
                metadata={"source": "assayer"},
                upsert=True,
            )
            self._project_id = project.id
        return self._project_id

    def _send_case(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_project()
        example_id = uuid.UUID(payload["id"])
        metadata = {"case_id": payload["case_id"], "assayer.experiment": self._experiment.name}
        fields: dict[str, Any] = {"metadata": metadata}
        if "input" in payload:  # content was left out otherwise
            inputs = _as_dict(payload["input"], "input")
            self._case_inputs[payload["id"]] = inputs
            outputs = {
                ("output" if name == "expected_output" else name): payload[name]
                for name in payload
                if name.startswith(("expected_", "reference_")) and payload[name] is not None
            }
            fields.update(inputs=inputs, outputs=outputs or None)
        try:
            self._client.create_example(
                example_id=example_id,
                dataset_id=self._dataset_id,
                **({"inputs": {}} | fields),
            )
        except LangSmithConflictError:
            self._client.update_example(example_id, dataset_id=self._dataset_id, **fields)
        return "confirmed"

    def _send_trajectory(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_project()
        run_id = uuid.UUID(payload["id"])
        start = self._started
        end = start + dt.timedelta(microseconds=self._step_count.get(payload["id"], 0) + 1)
        metadata = {
            "assayer.experiment": self._experiment.name,
            "assayer.case_id": payload["case_id"],
            "assayer.repetition": payload["repetition"],
            "assayer.usage": payload["usage"],
            "assayer.synthetic_timing": True,
        }
        if payload["session_id"] is not None:
            metadata["thread_id"] = payload["session_id"]
        outputs = None
        if "final_output" in payload:
            outputs = {"output": payload["final_output"], "state": payload["final_state"]}
        dotted_order = _stamp(start) + str(run_id)
        self._client.create_run(
            self._experiment.name,
            self._case_inputs.get(payload["case"], {}),
            "chain",
            project_name=self._experiment.name,
            id=run_id,
            trace_id=run_id,
            parent_run_id=None,
            dotted_order=dotted_order,
            start_time=start,
            end_time=end,
            outputs=outputs,
            extra={"metadata": metadata},
            reference_example_id=(
                uuid.UUID(payload["case"]) if payload["case"] is not None else None
            ),
        )
        self._runs[payload["id"]] = (run_id, dotted_order)
        return "queued"

    def _send_step(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_project()
        root = payload["trajectory_id"]
        parent = payload["parent_id"]
        if parent is not None and parent not in self._runs and root in self._runs:
            self.notes.append(
                f"step {payload['id']} names a parent that was not exported, "
                "so it hangs from its trajectory"
            )
            parent = None
        parent = parent or root
        if parent not in self._runs:
            raise AdapterCallError("validation", "the run it belongs to was not exported")
        trace_id, parent_order = self._runs[parent]

        run_id = uuid.UUID(payload["id"])
        start = self._started + dt.timedelta(microseconds=self._step_index[payload["id"]] + 1)
        dotted_order = f"{parent_order}.{_stamp(start)}{run_id}"
        outputs: dict[str, Any] = {}
        if "output" in payload:
            outputs["output"] = payload["output"]
        metadata: dict[str, Any] = {"assayer.kind": payload["kind"]}
        usage = payload["usage"]
        if usage is not None:
            outputs["usage_metadata"] = {
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "total_tokens": usage["input_tokens"] + usage["output_tokens"],
                **({"total_cost": usage["cost_usd"]} if usage["cost_usd"] is not None else {}),
            }
        if payload["model"] is not None:
            metadata["ls_model_name"] = payload["model"]
        self._client.create_run(
            payload["name"] or payload["model"] or payload["kind"],
            _as_dict(payload.get("input"), "input"),
            _RUN_TYPES[payload["kind"]],
            project_name=self._experiment.name,
            id=run_id,
            trace_id=trace_id,
            parent_run_id=uuid.UUID(parent),
            dotted_order=dotted_order,
            start_time=start,
            end_time=start,
            outputs=outputs or None,
            error=payload["error"],
            extra={"metadata": metadata},
        )
        self._runs[payload["id"]] = (trace_id, dotted_order)
        return "queued"

    def _send_score(self, payload: dict[str, Any]) -> Delivery | None:
        project_id = self._ensure_project()
        field = payload["field"]
        extra = {**payload["metadata"], "assayer.target": payload["target"]}
        if field is not None:
            extra["field"] = field
        target_id = payload["target_id"]
        if target_id is None:  # an Experiment-level Score, or one that could not be linked
            where: dict[str, Any] = {"project_id": project_id}
            if payload["target"] != "experiment":
                extra["target"] = payload["target"]
        else:
            where = {"run_id": uuid.UUID(target_id), "session_id": project_id}
        feedback_id = uuid.UUID(payload["id"])
        try:
            self._client.create_feedback(
                key=f"{payload['name']}.{field}" if field is not None else payload["name"],
                score=payload["value"],
                value=payload["label"],
                comment=payload["comment"],
                extra=extra,
                feedback_id=feedback_id,
                **where,
            )
        except LangSmithConflictError:
            self._client.update_feedback(
                feedback_id,
                score=payload["value"],
                value=payload["label"],
                comment=payload["comment"],
            )
        return "confirmed"


def _as_dict(value: Any, key: str) -> dict[str, Any]:
    if value is None:
        return {}
    return value if isinstance(value, dict) else {key: value}


def _stamp(moment: dt.datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%S%fZ")


def _call_error(error: LangSmithError) -> AdapterCallError:
    message = f"{type(error).__name__}: {error}"
    if isinstance(error, LangSmithAuthError):
        return AdapterCallError("auth", message)
    if isinstance(error, LangSmithRateLimitError):
        return AdapterCallError("rate_limited", message)
    if isinstance(error, LangSmithConnectionError | LangSmithAPIError):
        return AdapterCallError("transport", message)
    if isinstance(error, LangSmithNotFoundError | LangSmithUserError | LangSmithConflictError):
        return AdapterCallError("validation", message)
    return AdapterCallError("unknown", message)

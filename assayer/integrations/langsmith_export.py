"""One export of an Experiment to LangSmith: the dataset, the project and the calls per item."""

import datetime as dt
import uuid
from collections.abc import Callable
from typing import Any, NamedTuple

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
    Delivery,
    PlannedItem,
    step_id,
    step_key,
    trajectory_id,
)
from assayer.models import Experiment

_RUN_TYPES = {"model": "llm", "tool": "tool", "retrieval": "retriever", "other": "chain"}


class RunRef(NamedTuple):
    """Where a run sits in its trace, so its children can be placed under it."""

    trace_id: uuid.UUID
    dotted_order: str


class LangSmithExport:
    """The state of one export: the dataset and project, and the runs sent so far.

    Args:
        client: The LangSmith client.
        experiment: What is being exported.
        dataset_name: Name of the dataset the Cases go to.
        started: Start of every run of the export; Steps are offset from it by microseconds.
    """

    def __init__(
        self,
        client: langsmith.Client,
        experiment: Experiment,
        dataset_name: str,
        started: dt.datetime,
    ) -> None:
        self._client = client
        self._experiment = experiment
        self._dataset_name = dataset_name
        self._started = started
        self.notes: list[str] = []
        self._dataset_id: uuid.UUID | None = None
        self._project_id: uuid.UUID | None = None
        self._case_inputs: dict[str, dict[str, Any]] = {}
        self._runs: dict[str, RunRef] = {}  # exported item id -> its place in the trace
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

    def _ensure_dataset_and_project(self) -> uuid.UUID:
        """Create the dataset and the experiment project when missing; returns the project id."""
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
        self._ensure_dataset_and_project()
        example_id = uuid.UUID(payload["id"])
        fields: dict[str, Any] = {
            "metadata": {"case_id": payload["case_id"], "assayer.experiment": self._experiment.name}
        }
        if "input" in payload:  # content was left out otherwise
            inputs = _as_dict(payload["input"], "input")
            self._case_inputs[payload["id"]] = inputs
            outputs = {
                ("output" if name == "expected_output" else name): payload[name]
                for name in payload
                if name.startswith(("expected_", "reference_")) and payload[name] is not None
            }
            fields.update(inputs=inputs, outputs=outputs or None)
        _upsert(
            lambda: self._client.create_example(
                example_id=example_id,
                dataset_id=self._dataset_id,
                **({"inputs": {}} | fields),
            ),
            lambda: self._client.update_example(example_id, dataset_id=self._dataset_id, **fields),
        )
        return "confirmed"

    def _send_trajectory(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_dataset_and_project()
        run_id = uuid.UUID(payload["id"])
        start = self._started
        end = start + dt.timedelta(microseconds=self._step_count.get(payload["id"], 0) + 1)
        metadata = {
            "assayer.case_id": payload["case_id"],
            "assayer.repetition": payload["repetition"],
            "assayer.usage": payload["usage"],
        }
        if payload["session_id"] is not None:
            metadata["thread_id"] = payload["session_id"]
        outputs = None
        if "final_output" in payload:
            outputs = {"output": payload["final_output"], "state": payload["final_state"]}
        case = payload["case"]
        self._create_run(
            self._experiment.name,
            self._case_inputs.get(case, {}),
            "chain",
            run_id=run_id,
            trace_id=run_id,
            parent=None,
            parent_order="",
            start=start,
            end=end,
            outputs=outputs,
            metadata=metadata,
            reference_example_id=uuid.UUID(case) if case is not None else None,
        )
        return "queued"

    def _send_step(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_dataset_and_project()
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

        start = self._started + dt.timedelta(microseconds=self._step_index[payload["id"]] + 1)
        outputs: dict[str, Any] = {}
        if "output" in payload:
            outputs["output"] = payload["output"]
        if payload["usage"] is not None:
            outputs["usage_metadata"] = _usage_metadata(payload["usage"])
        metadata: dict[str, Any] = {"assayer.kind": payload["kind"]}
        if payload["model"] is not None:
            metadata["ls_model_name"] = payload["model"]
        self._create_run(
            payload["name"] or payload["model"] or payload["kind"],
            _as_dict(payload.get("input"), "input"),
            _RUN_TYPES[payload["kind"]],
            run_id=uuid.UUID(payload["id"]),
            trace_id=self._runs[parent].trace_id,
            parent=uuid.UUID(parent),
            parent_order=self._runs[parent].dotted_order,
            start=start,
            end=start,
            outputs=outputs or None,
            metadata=metadata,
            error=payload["error"],
        )
        return "queued"

    def _create_run(
        self,
        name: str,
        inputs: dict[str, Any],
        run_type: str,
        *,
        run_id: uuid.UUID,
        trace_id: uuid.UUID,
        parent: uuid.UUID | None,
        parent_order: str,
        start: dt.datetime,
        end: dt.datetime,
        outputs: dict[str, Any] | None,
        metadata: dict[str, Any],
        **extra: Any,
    ) -> None:
        segment = f"{_stamp(start)}{run_id}"
        dotted_order = f"{parent_order}.{segment}" if parent_order else segment
        self._client.create_run(
            name,
            inputs,
            run_type,
            project_name=self._experiment.name,
            id=run_id,
            trace_id=trace_id,
            parent_run_id=parent,
            dotted_order=dotted_order,
            start_time=start,
            end_time=end,
            outputs=outputs,
            extra={"metadata": {"assayer.synthetic_timing": True, **metadata}},
            **extra,
        )
        self._runs[run_id.hex] = RunRef(trace_id, dotted_order)

    def _send_score(self, payload: dict[str, Any]) -> Delivery | None:
        project_id = self._ensure_dataset_and_project()
        field = payload["field"]
        extra = {**payload["metadata"], "assayer.target": payload["target"]}
        if field is not None:
            extra["field"] = field
        target_id = payload["target_id"]
        if target_id is None:  # an Experiment-level Score, or one that could not be linked
            attach: dict[str, Any] = {"project_id": project_id}
        else:
            attach = {"run_id": uuid.UUID(target_id), "session_id": project_id}
        feedback_id = uuid.UUID(payload["id"])
        _upsert(
            lambda: self._client.create_feedback(
                key=f"{payload['name']}.{field}" if field is not None else payload["name"],
                score=payload["value"],
                value=payload["label"],
                comment=payload["comment"],
                extra=extra,
                feedback_id=feedback_id,
                **attach,
            ),
            lambda: self._client.update_feedback(
                feedback_id,
                score=payload["value"],
                value=payload["label"],
                comment=payload["comment"],
            ),
        )
        return "confirmed"


def _upsert(create: Callable[[], object], update: Callable[[], object]) -> None:
    """Create, or update when the backend says it exists."""
    try:
        create()
    except LangSmithConflictError:
        update()


def _usage_metadata(usage: dict[str, Any]) -> dict[str, Any]:
    metadata = {
        "input_tokens": usage["input_tokens"],
        "output_tokens": usage["output_tokens"],
        "total_tokens": usage["input_tokens"] + usage["output_tokens"],
    }
    if usage["cost_usd"] is not None:
        metadata["total_cost"] = usage["cost_usd"]
    return metadata


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

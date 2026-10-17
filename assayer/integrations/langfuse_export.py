"""One export of an Experiment to Langfuse: the dataset, the OTLP spans and the scores."""

import datetime as dt
import hashlib
import inspect
import json
from typing import Any

import httpx
from langfuse import Langfuse
from langfuse.api.core.api_error import ApiError
from langfuse.api.core.request_options import RequestOptions
from langfuse.api.opentelemetry import (
    OtelAttribute,
    OtelAttributeValue,
    OtelResource,
    OtelResourceSpan,
    OtelScope,
    OtelScopeSpan,
    OtelSpan,
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

_OBSERVATION_TYPES = {
    "model": "generation",
    "tool": "tool",
    "retrieval": "retriever",
    "other": "span",
}
# Experiment (dataset run) attributes and the environment Langfuse gives SDK experiments.
_EXPERIMENT_ENVIRONMENT = "sdk-experiment"
_INGESTION_VERSION: RequestOptions = {"additional_headers": {"x-langfuse-ingestion-version": "4"}}
_STATUS_ERROR = {"code": 2}
_OBSERVATION = "langfuse.observation."
_TRACE = "langfuse.trace."


class _Run:
    """What the observations of one Trajectory share: its dataset run and where it started."""

    def __init__(self, trace_id: str, root_span_id: str, attributes: dict[str, Any]) -> None:
        self.trace_id = trace_id
        self.root_span_id = root_span_id
        self.attributes = attributes
        self.spans: set[str] = {root_span_id}


class LangfuseExport:
    """The state of one export: the dataset, the runs sent so far and what had to be dropped.

    Args:
        client: The Langfuse client.
        experiment: What is being exported.
        dataset_name: Name of the dataset the Cases go to.
        started: Start of every observation of the export; Steps are offset from it by
            microseconds.
    """

    def __init__(
        self,
        client: Langfuse,
        experiment: Experiment,
        dataset_name: str,
        started: dt.datetime,
    ) -> None:
        self._client = client
        self._experiment = experiment
        self._dataset_name = dataset_name
        self._started = started
        self.notes: list[str] = []
        self._dataset_id: str | None = None
        self._project_id: str | None = None
        self._case_inputs: dict[str, Any] = {}
        self._runs: dict[str, _Run] = {}  # trajectory export id -> its run
        self._run_ids: dict[str, str] = {}  # dataset run name -> its experiment id
        self._step_trace: dict[str, str] = {}  # step export id -> its trajectory export id
        self._step_count: dict[str, int] = {}
        self._step_index: dict[str, int] = {}
        for trajectory in experiment.trajectories or []:
            t_id = trajectory_id(experiment.name, trajectory.case_id, trajectory.repetition)
            self._step_count[t_id] = len(trajectory.steps)
            for index in range(len(trajectory.steps)):
                key = step_id(t_id, step_key(trajectory, index))
                self._step_index.setdefault(key, index)
                self._step_trace.setdefault(key, t_id)
        self._repetitions = sorted({t.repetition for t in experiment.trajectories or []})
        self._score_metadata = "metadata" in inspect.signature(client.create_score).parameters
        self._noted_metadata = False

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
        except (ApiError, httpx.TransportError) as error:
            raise _call_error(error) from error

    def _ensure_dataset(self) -> str:
        """Create the dataset when missing (Langfuse upserts by name); returns its id."""
        if self._dataset_id is None:
            dataset = self._client.create_dataset(
                name=self._dataset_name,
                description="Cases exported by assayer",
                metadata={"source": "assayer"},
            )
            self._dataset_id = dataset.id
        return self._dataset_id

    def _project(self) -> str:
        if self._project_id is None:
            projects = self._client.api.projects.get().data
            if not projects:
                raise AdapterCallError("validation", "could not resolve the Langfuse project id")
            self._project_id = projects[0].id
        return self._project_id

    def _run_id(self, run_name: str) -> str:
        """The id Langfuse derives for a dataset run, which groups its traces."""
        if run_name not in self._run_ids:
            payload = json.dumps(
                ["langfuse-experiment-v1", self._project(), self._ensure_dataset(), run_name],
                separators=(",", ":"),
                ensure_ascii=False,
            )
            self._run_ids[run_name] = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self._run_ids[run_name]

    def _send_case(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_dataset()
        fields: dict[str, Any] = {}
        if "input" in payload:  # content was left out otherwise
            self._case_inputs[payload["id"]] = payload["input"]
            fields["input"] = payload["input"]
            expected = {
                ("output" if name == "expected_output" else name): payload[name]
                for name in payload
                if name.startswith(("expected_", "reference_")) and payload[name] is not None
            }
            if set(expected) == {"output"}:
                fields["expected_output"] = expected["output"]
            elif expected:
                fields["expected_output"] = expected
        self._client.create_dataset_item(
            dataset_name=self._dataset_name,
            id=payload["case_id"],
            metadata={
                "case_id": payload["case_id"],
                "assayer.id": payload["id"],
                "assayer.experiment": self._experiment.name,
            },
            **fields,
        )
        return "confirmed"

    def _send_trajectory(self, payload: dict[str, Any]) -> Delivery | None:
        dataset_id = self._ensure_dataset()
        t_id = payload["id"]
        run_name = f"{self._experiment.name}/rep-{payload['repetition']}"
        span_id = t_id[:16]
        shared = {
            "langfuse.environment": _EXPERIMENT_ENVIRONMENT,
            "langfuse.experiment.id": self._run_id(run_name),
            "langfuse.experiment.name": run_name,
            "langfuse.experiment.item.root_observation_id": span_id,
        }
        if payload["case_id"] is not None:
            shared["langfuse.experiment.dataset.id"] = dataset_id
            shared["langfuse.experiment.item.id"] = payload["case_id"]
        else:  # no dataset item exists for it, so the run must not point at one
            shared["langfuse.experiment.item.id"] = t_id
        metadata = {
            "assayer.id": t_id,
            "assayer.case_id": payload["case_id"],
            "assayer.repetition": payload["repetition"],
            "assayer.usage": payload["usage"],
        }
        attributes: dict[str, Any] = {
            **shared,
            _OBSERVATION + "type": "span",
            _TRACE + "name": self._experiment.name,
        }
        if payload["session_id"] is not None:
            attributes["session.id"] = payload["session_id"]
        if "final_output" in payload:  # content was left out otherwise
            metadata["final_output"] = payload["final_output"]
            metadata["final_state"] = payload["final_state"]
            attributes[_OBSERVATION + "output"] = _text(payload["final_output"])
            case_input = self._case_inputs.get(payload["case"])
            if case_input is not None:
                attributes[_OBSERVATION + "input"] = _text(case_input)
        self._export(
            name=self._experiment.name,
            trace_id=t_id,
            span_id=span_id,
            parent_span_id=None,
            start=self._started,
            end=self._started + dt.timedelta(microseconds=self._step_count.get(t_id, 0) + 1),
            attributes=attributes,
            metadata=metadata,
            trace_metadata=metadata,
        )
        self._runs[t_id] = _Run(t_id, span_id, shared)
        return "confirmed"

    def _send_step(self, payload: dict[str, Any]) -> Delivery | None:
        self._ensure_dataset()
        root = payload["trajectory_id"]
        run = self._runs.get(root)
        if run is None:
            raise AdapterCallError("validation", "the trajectory it belongs to was not exported")
        parent = payload["parent_id"]
        if parent is not None and parent[:16] not in run.spans:
            self.notes.append(
                f"step {payload['id']} names a parent that was not exported, "
                "so it hangs from its trajectory"
            )
            parent = None
        parent_span_id = parent[:16] if parent is not None else run.root_span_id
        span_id = payload["id"][:16]
        run.spans.add(span_id)

        start = self._started + dt.timedelta(microseconds=self._step_index[payload["id"]] + 1)
        kind = payload["kind"]
        attributes: dict[str, Any] = {
            **run.attributes,
            _OBSERVATION + "type": _OBSERVATION_TYPES[kind],
        }
        if "input" in payload and payload["input"] is not None:
            attributes[_OBSERVATION + "input"] = _text(payload["input"])
        if payload.get("output") is not None:
            attributes[_OBSERVATION + "output"] = _text(payload["output"])
        if payload["model"] is not None:
            attributes[_OBSERVATION + "model.name"] = payload["model"]
        usage = payload["usage"]
        if usage is not None:
            attributes[_OBSERVATION + "usage_details"] = _text(
                {
                    "input": usage["input_tokens"],
                    "output": usage["output_tokens"],
                    "total": usage["input_tokens"] + usage["output_tokens"],
                }
            )
            if usage["cost_usd"] is not None:
                attributes[_OBSERVATION + "cost_details"] = _text({"total": usage["cost_usd"]})
        error = payload["error"]
        if error is not None:
            attributes[_OBSERVATION + "level"] = "ERROR"
            attributes[_OBSERVATION + "status_message"] = error
        self._export(
            name=payload["name"] or payload["model"] or kind,
            trace_id=root,
            span_id=span_id,
            parent_span_id=parent_span_id,
            start=start,
            end=start,
            attributes=attributes,
            metadata={"assayer.id": payload["id"], "assayer.kind": kind},
            status={**_STATUS_ERROR, "message": error} if error is not None else None,
        )
        return "confirmed"

    def _export(
        self,
        *,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: str | None,
        start: dt.datetime,
        end: dt.datetime,
        attributes: dict[str, Any],
        metadata: dict[str, Any],
        trace_metadata: dict[str, Any] | None = None,
        status: dict[str, Any] | None = None,
    ) -> None:
        attributes = dict(attributes)
        for key, value in {"assayer.synthetic_timing": True, **metadata}.items():
            attributes[f"{_OBSERVATION}metadata.{key}"] = value
        for key, value in (trace_metadata or {}).items():
            attributes[f"{_TRACE}metadata.{key}"] = value
        span = OtelSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=name,
            kind=1,
            start_time_unix_nano=str(_nanos(start)),
            end_time_unix_nano=str(_nanos(end)),
            attributes=[
                OtelAttribute(key=key, value=_attribute(value))
                for key, value in attributes.items()
                if value is not None
            ],
            status=status,
        )
        self._client.api.opentelemetry.export_traces(
            resource_spans=[
                OtelResourceSpan(
                    resource=OtelResource(
                        attributes=[
                            OtelAttribute(
                                key="service.name",
                                value=OtelAttributeValue(string_value="assayer"),
                            )
                        ]
                    ),
                    scope_spans=[OtelScopeSpan(scope=OtelScope(name="assayer"), spans=[span])],
                )
            ],
            request_options=_INGESTION_VERSION,
        )

    def _send_score(self, payload: dict[str, Any]) -> Delivery | None:
        field = payload["field"]
        name = f"{payload['name']}.{field}" if field is not None else payload["name"]
        metadata = {
            **payload["metadata"],
            "assayer.id": payload["id"],
            "assayer.target": payload["target"],
        }
        if field is not None:
            metadata["field"] = field
        if payload["label"] is not None:
            metadata["label"] = payload["label"]
        target = payload["target_id"]
        step_trace = self._step_trace.get(target) if payload["target"] == "step" else None
        if target is None:  # an Experiment-level Score, or one that could not be linked
            attachments = [
                (
                    f"{payload['id']}-rep-{n}",
                    {"dataset_run_id": self._run_id(f"{self._experiment.name}/rep-{n}")},
                )
                for n in self._repetitions
            ]
            if not attachments:
                raise AdapterCallError("validation", "the Experiment has no dataset run to score")
        elif payload["target"] == "step":
            # Langfuse links a score to its trace by id, even if the trace arrives later
            attachments = [(payload["id"], {"trace_id": step_trace, "observation_id": target[:16]})]
        else:
            attachments = [(payload["id"], {"trace_id": target})]

        extra: dict[str, Any] = {}
        if self._score_metadata:
            extra["metadata"] = metadata
        elif not self._noted_metadata:
            self._noted_metadata = True
            self.notes.append(
                "this Langfuse SDK does not accept `metadata` on create_score, so it is dropped "
                "from every Score (including the label, the field and the Case)"
            )
        for score_id, attach in attachments:
            self._client.create_score(
                name=name,
                value=payload["value"],
                score_id=score_id,
                data_type="NUMERIC",
                comment=payload["comment"],
                **attach,
                **extra,
            )
        return "queued"


def _nanos(moment: dt.datetime) -> int:
    delta = moment - dt.datetime(1970, 1, 1, tzinfo=dt.UTC)
    return (delta.days * 86_400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1_000


def _text(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value, default=str)


def _attribute(value: Any) -> OtelAttributeValue:
    if isinstance(value, bool):
        return OtelAttributeValue(bool_value=value)
    if isinstance(value, int):
        return OtelAttributeValue(int_value=value)
    if isinstance(value, float):
        return OtelAttributeValue(double_value=value)
    return OtelAttributeValue(string_value=_text(value))


def _call_error(error: ApiError | httpx.TransportError) -> AdapterCallError:
    if isinstance(error, httpx.TransportError):  # connection failures and timeouts
        return AdapterCallError("transport", f"{type(error).__name__}: {error}")
    message = f"{type(error).__name__}: {error}"
    status = error.status_code
    if status in (401, 403):
        return AdapterCallError("auth", message)
    if status == 429:
        return AdapterCallError("rate_limited", message, retry_after=_retry_after(error))
    if status == 408 or (status is not None and status >= 500):
        return AdapterCallError("transport", message)
    if status is not None and 400 <= status < 500:
        return AdapterCallError("validation", message)
    return AdapterCallError("unknown", message)


def _retry_after(error: ApiError) -> float | None:
    for key, value in (error.headers or {}).items():
        if key.lower() == "retry-after":
            try:
                return float(value)
            except ValueError:
                return None
    return None

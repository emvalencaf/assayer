"""What every Adapter needs to export an Experiment: the items to send and the loop that sends them.

`plan_export` turns an Experiment into the ordered items (Cases, then each Trajectory with its
Steps, then Scores) with deterministic ids. `run_export` sends them one by one, retrying
transient failures and collecting the outcome in an `ExportReport`, so an Adapter only has to
say how to send one item.
"""

import dataclasses
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal

from assayer.adapters.errors import AdapterCallError
from assayer.adapters.ids import (
    case_export_id,
    score_ids,
    score_occurrences,
    step_id,
    step_key,
    trajectory_id,
)
from assayer.adapters.report import ExportFailure, ExportItem, ExportReport
from assayer.adapters.retry import call_with_retry
from assayer.models import Case, Experiment, Step, Trajectory

Delivery = Literal["confirmed", "queued"]


@dataclass(frozen=True)
class PlannedItem:
    """An item to send: what it is and the payload to send for it."""

    item: ExportItem
    payload: dict[str, Any]


@dataclass(frozen=True)
class ExportPlan:
    """What exporting an Experiment sends, and what could not be linked or was left out."""

    items: list[PlannedItem]
    notes: list[str]


_CASE_CONTENT = (
    "input",
    "expected_output",
    "expected_tool_calls",
    "expected_steps",
    "expected_outcome",
    "expected_state",
    "reference_contexts",
    "reference_context_ids",
)


def plan_export(experiment: Experiment, *, include_content: bool = True) -> ExportPlan:
    """List what exporting the Experiment sends, in order.

    Args:
        experiment: The Experiment to export.
        include_content: When False, payloads leave out what the target saw and produced
            (Case inputs and references, Step inputs, outputs and errors, final output and
            state, Score comments) and keep structure, Score values and metadata.

    Returns:
        The items (Cases, then each Trajectory followed by its Steps, then Scores) and notes
        on Scores and Trajectories that could not be linked to what they refer to.
    """
    planned = [_case_item(experiment, case, include_content) for case in experiment.cases]

    notes: list[str] = []
    by_case: dict[str | None, list[str]] = {}
    step_ids: dict[str, str] = {}
    for trajectory in experiment.trajectories:
        t_id = trajectory_id(experiment.name, trajectory.case_id, trajectory.repetition)
        if trajectory.case_id is None:
            notes.append(f"trajectory {t_id} has no case_id, so it is not linked to a Case")
        by_case.setdefault(trajectory.case_id, []).append(t_id)
        planned.append(_trajectory_item(experiment, trajectory, t_id, include_content))
        for index, step in enumerate(trajectory.steps):
            key = step_key(trajectory, index)
            step_ids.setdefault(key, step_id(t_id, key))
            planned.append(_step_item(trajectory, t_id, step, key, include_content))

    ids = score_ids(experiment)
    occurrences = score_occurrences(experiment)
    for score, s_id, occurrence in zip(experiment.scores, ids, occurrences, strict=True):
        target_id, owner = None, None  # owner: the Trajectory a trajectory Score belongs to
        if score.target == "step":
            target_id = step_ids.get(score.target_id)
        elif score.target == "trajectory":
            owners = by_case.get(score.target_id, [])
            owner = owners[occurrence] if occurrence < len(owners) else None
            target_id = owner
        if score.target != "experiment" and target_id is None:
            notes.append(f"score {s_id} ({score.name}) could not be linked to its {score.target}")
        planned.append(
            PlannedItem(
                ExportItem("score", s_id),
                {
                    "id": s_id,
                    "experiment": experiment.name,
                    "name": score.name,
                    "value": score.value,
                    "field": score.field,
                    "label": score.label,
                    "comment": score.comment if include_content else None,
                    "metadata": score.metadata,
                    "target": score.target,
                    "target_id": target_id,
                },
            )
        )
    return ExportPlan(planned, notes)


def run_export(
    plan: ExportPlan,
    send: Callable[[PlannedItem], Delivery | None],
    *,
    sleep: Callable[[float], None] = time.sleep,
) -> ExportReport:
    """Send each planned item and report the outcome; never raises for an item's failure.

    Transient failures are retried by the retry policy. An `auth` failure stops the export and
    lists the items not yet tried as skipped.

    Args:
        plan: What `plan_export` returned.
        send: Sends one item. Returns "queued" when the SDK only buffered it, otherwise it is
            taken as confirmed. Raises `AdapterCallError` to report a failure; any other
            exception is reported as `unknown`.
        sleep: Waits between retries.

    Returns:
        The report.
    """
    planned = plan.items
    report = ExportReport(notes=list(plan.notes))
    for position, entry in enumerate(planned):
        try:
            delivery = call_with_retry(lambda entry=entry: send(entry), sleep=sleep)
        except AdapterCallError as error:
            failure = ExportFailure(
                entry.item.target_kind,
                entry.item.target_id,
                error.kind,
                error.message,
                error.retryable,
            )
        except Exception as error:
            failure = ExportFailure(
                entry.item.target_kind,
                entry.item.target_id,
                "unknown",
                f"{type(error).__name__}: {error}",
            )
        else:
            (report.queued if delivery == "queued" else report.confirmed).append(entry.item)
            continue
        report.failed.append(failure)
        if failure.kind == "auth":
            report.skipped.extend(p.item for p in planned[position + 1 :])
            break
    return report


def _case_item(experiment: Experiment, case: Case, include_content: bool) -> PlannedItem:
    c_id = case_export_id(experiment.name, case.id)
    payload: dict[str, Any] = {"id": c_id, "case_id": case.id, "dataset": experiment.name}
    if include_content:
        payload.update({name: getattr(case, name) for name in _CASE_CONTENT})
    return PlannedItem(ExportItem("case", c_id), payload)


def _trajectory_item(
    experiment: Experiment, trajectory: Trajectory, t_id: str, include_content: bool
) -> PlannedItem:
    usage = trajectory.total_usage(experiment.pricing)
    payload: dict[str, Any] = {
        "id": t_id,
        "experiment": experiment.name,
        "case_id": trajectory.case_id,
        "case": (
            case_export_id(experiment.name, trajectory.case_id)
            if trajectory.case_id is not None
            else None
        ),
        "repetition": trajectory.repetition,
        "session_id": trajectory.session_id,
        "usage": dataclasses.asdict(usage),
    }
    if include_content:
        payload["final_output"] = trajectory.final_output
        payload["final_state"] = trajectory.final_state
    return PlannedItem(ExportItem("trajectory", t_id), payload)


def _step_item(
    trajectory: Trajectory, t_id: str, step: Step, key: str, include_content: bool
) -> PlannedItem:
    s_id = step_id(t_id, key)
    payload: dict[str, Any] = {
        "id": s_id,
        "trajectory_id": t_id,
        "parent_id": step_id(t_id, step.parent_id) if step.parent_id is not None else None,
        "kind": step.kind,
        "name": step.name,
        "model": step.model,
        "error": step.error if include_content else None,
        "usage": dataclasses.asdict(step.usage) if step.usage is not None else None,
    }
    if include_content:
        payload["input"] = step.input
        payload["output"] = step.output
    return PlannedItem(ExportItem("step", s_id), payload)


def export_experiment(
    experiment: Experiment,
    send: Callable[[PlannedItem], Delivery | None],
    *,
    include_content: bool = True,
    sleep: Callable[[float], None] = time.sleep,
) -> ExportReport:
    """Plan and send an Experiment; an Experiment that cannot be planned is a failure, not a raise.

    Args:
        experiment: What to export.
        send: Sends one item; see `run_export`.
        include_content: See `plan_export`.
        sleep: Waits between retries.

    Returns:
        The report. A planning error appears as one `validation` failure of kind "experiment".
    """
    try:
        plan = plan_export(experiment, include_content=include_content)
    except Exception as error:
        failure = ExportFailure(
            "experiment", experiment.name, "validation", f"{type(error).__name__}: {error}"
        )
        return ExportReport(failed=[failure])
    return run_export(plan, send, sleep=sleep)

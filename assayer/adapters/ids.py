"""Deterministic ids, so exporting an Experiment again updates what is there."""

import uuid

from assayer.models import Experiment, Score, Trajectory

_NAMESPACE = uuid.UUID("5f0f2b6e-3c1d-4a57-9c1e-7a1d6f0b2e11")


def _derive(*parts: object) -> str:
    return uuid.uuid5(_NAMESPACE, "\x1f".join(str(p) for p in parts)).hex


def case_export_id(experiment_name: str, case_id: str) -> str:
    """The id of a Case in a backend."""
    return _derive("case", experiment_name, case_id)


def trajectory_id(experiment_name: str, case_id: str | None, repetition: int) -> str:
    """The id of a Trajectory: stable for the same Experiment name, Case and repetition."""
    return _derive("trajectory", experiment_name, case_id, repetition)


def step_key(trajectory: Trajectory, index: int) -> str:
    """The Step's own id, or its position when it has none."""
    own = trajectory.steps[index].id
    return own if own is not None else f"{trajectory.case_id}/{trajectory.repetition}/{index}"


def step_id(trajectory_export_id: str, key: str) -> str:
    """The id of a Step inside the exported Trajectory `trajectory_export_id`."""
    return _derive("step", trajectory_export_id, key)


def score_occurrences(experiment: Experiment) -> list[int]:
    """For each Score, how many Scores with the same target, metric and Field come before it."""
    seen: dict[tuple, int] = {}
    occurrences = []
    for score in experiment.scores:
        key = _score_key(score)
        occurrences.append(seen.get(key, 0))
        seen[key] = occurrences[-1] + 1
    return occurrences


def score_ids(experiment: Experiment) -> list[str]:
    """One id per Score of the Experiment, in order.

    A Score is identified by its target, metric and Field. Several Scores sharing those
    (one per repetition of a Case, for instance) are told apart by their order among them.
    """
    return [
        _derive("score", experiment.name, *_score_key(score), occurrence)
        for score, occurrence in zip(experiment.scores, score_occurrences(experiment), strict=True)
    ]


def _score_key(score: Score) -> tuple:
    return (score.target, score.target_id, score.name, score.field)

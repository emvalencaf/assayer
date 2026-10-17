"""Scores one Field of a Trajectory: a plain Field, or a list Field after Alignment."""

import dataclasses
from collections import defaultdict
from typing import Any

from assayer.alignment import (
    Alignment,
    align_best_match,
    align_by_key,
    align_positional,
)
from assayer.metrics import MetricOutcome
from assayer.models import Case, EvaluationFailure, Experiment, Score, Trajectory
from assayer.path import resolve
from assayer.runner.field_map.field_metric import FieldMetric
from assayer.runner.field_map.list_field import ListSpec

LIST_SCORES = ("list_precision", "list_recall", "list_f1")


def score_field(
    entry: FieldMetric | ListSpec, trajectory: Trajectory, case: Case, prefix: str = ""
) -> MetricOutcome:
    """Score one entry of the field map against a Trajectory and its Case.

    Args:
        entry: A metric for a Field, or a list Field.
        trajectory: Its `final_output` holds the Field, relative to `prefix`.
        case: Its `expected_output` holds the expected Field.
        prefix: Dotted path of the container the paths of `entry` are relative to.

    Returns:
        The Scores and evaluation failures, with their `field` set to the full path.
    """
    field = f"{prefix}.{entry.path}" if prefix else entry.path
    predicted = resolve(trajectory.final_output, entry.path)
    expected = resolve(case.expected_output, entry.path)
    if isinstance(entry, ListSpec):
        return _score_list(entry, trajectory, case, field, predicted, expected)
    item_trajectory, item_case = _cut(trajectory, case, predicted, expected)
    return entry.metric.evaluate(
        item_trajectory,
        item_case,
        field=field,
        params=entry.params,
    )


def score_experiment_field(entry: FieldMetric, experiment: Experiment) -> MetricOutcome:
    """Score one Field over a whole Experiment with an Experiment-level metric.

    The metric sees an Experiment cut down to the Field: each Trajectory's
    `final_output` and each Case's `expected_output` are the Field's values, and
    only the Scores already computed for that Field remain.

    Args:
        entry: An Experiment-level metric for a Field.
        experiment: The Experiment holding the Trajectories, Cases and Scores.

    Returns:
        The Score or evaluation failure, with `field` set to the path.
    """
    view = dataclasses.replace(
        experiment,
        trajectories=[
            dataclasses.replace(t, final_output=resolve(t.final_output, entry.path))
            for t in experiment.trajectories
        ],
        cases=[
            dataclasses.replace(c, expected_output=resolve(c.expected_output, entry.path))
            for c in experiment.cases
        ],
        scores=[s for s in experiment.scores if s.field == entry.path],
    )
    return entry.metric.evaluate(view, field=entry.path, params=entry.params)


def _cut(
    trajectory: Trajectory, case: Case, predicted: Any, expected: Any
) -> tuple[Trajectory, Case]:
    """Narrow a Trajectory and its Case down to one Field's (or item's) values."""
    return (
        dataclasses.replace(trajectory, final_output=predicted),
        dataclasses.replace(case, expected_output=expected),
    )


def _score_list(
    spec: ListSpec,
    trajectory: Trajectory,
    case: Case,
    field: str,
    predicted: Any,
    expected: Any,
) -> MetricOutcome:
    if not isinstance(expected, list):
        error = (
            "missing required input: expected_output"
            if expected is None
            else (f"expected_output must be a list, got {type(expected).__name__}")
        )
        return MetricOutcome(
            failures=[EvaluationFailure("list_alignment", error, trajectory.case_id, field)]
        )
    if not isinstance(predicted, list):
        predicted = []  # no answer, or not a list: nothing was predicted

    cache: dict[tuple[int, int], MetricOutcome] = {}

    def outcome_of(e: int, p: int) -> MetricOutcome:
        if (e, p) not in cache:
            cache[e, p] = _score_item(
                spec.properties, trajectory, case, field, predicted[p], expected[e]
            )
        return cache[e, p]

    def similarity(e: int, p: int) -> float:
        return _similarity(outcome_of(e, p), spec, field)

    alignment = _align(spec, expected, predicted, similarity)

    outcome = MetricOutcome()
    for item in cache.values():  # every pair tried to align costs, paired or not
        outcome.add_judge(item)
    grouped: dict[tuple[str | None, str], list[Score]] = defaultdict(list)
    for e, p in alignment.pairs:
        item = outcome_of(e, p)
        outcome.failures.extend(item.failures)
        for score in item.scores:
            grouped[score.field, score.name].append(_within(score, [e, p]))
    outcome.scores.extend(_mean(group, trajectory.case_id) for group in grouped.values())
    outcome.scores.extend(_list_scores(alignment, len(expected), len(predicted), field, trajectory))
    return outcome


def _align(spec: ListSpec, expected: list, predicted: list, similarity) -> Alignment:
    if spec.align == "key":
        return align_by_key(expected, predicted, spec.key)
    if spec.align == "positional":
        return align_positional(len(expected), len(predicted))
    return align_best_match(len(expected), len(predicted), similarity, spec.threshold)


def _score_item(
    properties: list[FieldMetric | ListSpec],
    trajectory: Trajectory,
    case: Case,
    field: str,
    predicted: Any,
    expected: Any,
) -> MetricOutcome:
    item_trajectory, item_case = _cut(trajectory, case, predicted, expected)
    outcome = MetricOutcome()
    for child in properties:
        result = score_field(child, item_trajectory, item_case, prefix=field)
        outcome.scores.extend(result.scores)
        outcome.failures.extend(result.failures)
        outcome.add_judge(result)
    return outcome


def _similarity(item: MetricOutcome, spec: ListSpec, field: str) -> float:
    """Mean of the item's property Scores; a nested list counts as its `list_f1`."""
    values = []
    for child in spec.properties:
        child_field = f"{field}.{child.path}"
        wanted = "list_f1" if isinstance(child, ListSpec) else child.metric.name
        values.extend(s.value for s in item.scores if s.field == child_field and s.name == wanted)
    return sum(values) / len(values) if values else 0.0


def _within(score: Score, pair: list[int]) -> Score:
    """Tag a nested list-level Score with the pair of the outer list it was computed in."""
    if score.name not in LIST_SCORES:
        return score
    alignments = score.metadata.get("alignments") or [score.metadata["alignment"]]
    tagged = [{**a, "within": [pair, *a.get("within", [])]} for a in alignments]
    return dataclasses.replace(score, metadata={"alignments": tagged})


def _mean(scores: list[Score], case_id: str | None) -> Score:
    first = scores[0]
    metadata: dict[str, Any] = {"aligned_pairs": len(scores)}
    if first.name in LIST_SCORES:
        metadata = {"alignments": [a for s in scores for a in s.metadata["alignments"]]}
    return Score(
        name=first.name,
        value=sum(s.value for s in scores) / len(scores),
        field=first.field,
        target=first.target,
        target_id=case_id,
        metadata=metadata,
    )


def _list_scores(
    alignment: Alignment, n_expected: int, n_predicted: int, field: str, trajectory: Trajectory
) -> list[Score]:
    matched = len(alignment.pairs)
    precision = matched / n_predicted if n_predicted else 1.0
    recall = matched / n_expected if n_expected else 1.0
    if not n_expected and not n_predicted:
        f1 = 1.0
    elif precision + recall:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0
    return [
        Score(
            name=name,
            value=value,
            field=field,
            target_id=trajectory.case_id,
            metadata={"alignment": alignment.as_dict()},
            comment=f"{matched} paired, {len(alignment.unmatched_expected)} missing, "
            f"{len(alignment.unmatched_predicted)} extra",
        )
        for name, value in zip(LIST_SCORES, (precision, recall, f1), strict=True)
    ]

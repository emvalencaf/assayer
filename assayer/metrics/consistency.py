"""Consistency metrics: how stable a target's answers are across repetitions of a Case.

Run the Runner with `repetitions=k` and these Experiment-level metrics: each Case's
k Trajectories are measured on their own and the Score is the mean over Cases, so
one Case with erratic answers lowers it. Run per Field, they see that Field only.
"""

import math
import statistics
from collections import Counter
from collections.abc import Callable
from typing import Any

from assayer.metrics.metric import Metric
from assayer.models import Experiment


def _groups(experiment: Experiment) -> list[tuple[list[Any], Any]]:
    """The outputs of each Case's repetitions, with the Case's reference."""
    outputs: dict[str, list[Any]] = {}
    for trajectory in experiment.trajectories:
        outputs.setdefault(trajectory.case_id, []).append(trajectory.final_output)
    return [(outputs[c.id], c.expected_output) for c in experiment.cases if c.id in outputs]


def _mean_over_cases(per_case: Callable[[list[Any], Any], float]) -> Callable:
    def metric(experiment: Experiment, case=None) -> float:
        values = [per_case(*group) for group in _groups(experiment)]
        return statistics.mean(values) if values else 0.0

    return metric


def _is_multilabel(outputs: list[Any]) -> bool:
    return any(isinstance(o, (list, set)) for o in outputs)


def _number_text(value: Any) -> str:
    """Text of a value, with a whole float written as an integer (`1.0` is `1`)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _agreement_rate(outputs: list[Any], reference: Any) -> float:
    """Share of the repetitions that gave the most frequent answer."""
    return Counter(map(str, outputs)).most_common(1)[0][1] / len(outputs)


def _entropy(outputs: list[Any], reference: Any) -> float:
    """Shannon entropy of the answers, as a share of the most `len(outputs)` allow."""
    counts = Counter(map(str, outputs))
    if len(outputs) <= 1 or len(counts) == 1:
        return 0.0
    bits = -sum(c / len(outputs) * math.log2(c / len(outputs)) for c in counts.values())
    return bits / math.log2(len(outputs))


def _correct_rate(outputs: list[Any], reference: Any) -> float:
    """Share of the repetitions that equal the reference (as sets for multi-label)."""
    if _is_multilabel(outputs):
        try:
            wanted = set(reference)
            return sum(_as_set(o) == wanted for o in outputs) / len(outputs)
        except TypeError:
            return 0.0
    return sum(_number_text(o) == _number_text(reference) for o in outputs) / len(outputs)


def _as_set(output: Any) -> set | None:
    try:
        return set(output)
    except TypeError:
        return None


def _pass_at_k(outputs: list[Any], reference: Any) -> float:
    """1 if at least one repetition equals the reference, else 0."""
    return float(_correct_rate(outputs, reference) > 0)


def _recall_at_k(outputs: list[Any], reference: Any) -> float:
    """Share of the reference labels covered by the union of the repetitions."""
    if _is_multilabel(outputs):
        try:
            wanted = set(reference)
        except TypeError:
            return 0.0
        if not wanted:
            return 0.0
        covered = set().union(*(_as_set(o) or set() for o in outputs))
        return len(covered & wanted) / len(wanted)
    return float(str(reference) in {str(o) for o in outputs})


def make_score_std(of: str | None = None) -> Metric:
    """Create the metric for how much a metric's Scores vary across a Case's repetitions.

    The sample standard deviation of the Scores that metric `of` gave the k
    Trajectories of a Case, averaged over Cases; 0 for a Case with fewer than two.
    The metric `of` must run before this one.

    Args:
        of: Name of the trajectory-level metric whose Scores are measured. Without
            it, the only trajectory-level metric that scored the output is used.

    Returns:
        The Experiment-level Metric.
    """

    def score_std(experiment: Experiment, case=None) -> float:
        scores = [s for s in experiment.scores if s.target == "trajectory"]
        name = of
        if name is None:
            names = sorted({s.name for s in scores})
            if len(names) != 1:
                raise ValueError(
                    "score_std needs the metric to measure: make_score_std(of=...); "
                    f"trajectory-level Scores so far: {names}"
                )
            name = names[0]
        by_case: dict[str, list[float]] = {}
        for score in scores:
            if score.name == name:
                by_case.setdefault(score.target_id, []).append(score.value)
        if not by_case:
            raise ValueError(f"no Scores of metric {name!r} to take the spread of")
        return statistics.mean(
            statistics.stdev(values) if len(values) > 1 else 0.0 for values in by_case.values()
        )

    return Metric(name="score_std", level="experiment", fn=score_std)


def register_consistency_metrics(registry) -> None:
    """Register the consistency metrics into a registry.

    Registers agreement_rate, entropy (in bits over `log2(k)`, so within [0, 1]),
    correct_rate, pass_at_k, recall_at_k and score_std (of the only metric that
    scored the output; use `make_score_std` to name one).

    Args:
        registry: The Registry to fill.

    Raises:
        KeyError: If one of the names is already registered.
    """
    plain = {"agreement_rate": _agreement_rate, "entropy": _entropy}
    referenced = {
        "correct_rate": _correct_rate,
        "pass_at_k": _pass_at_k,
        "recall_at_k": _recall_at_k,
    }
    for name, per_case in plain.items():
        registry.register(Metric(name=name, level="experiment", fn=_mean_over_cases(per_case)))
    for name, per_case in referenced.items():
        registry.register(
            Metric(
                name=name,
                level="experiment",
                fn=_mean_over_cases(per_case),
                requires=("expected_output",),
            )
        )
    registry.register(make_score_std())

"""Comparison of two Experiments."""

from collections import defaultdict
from collections.abc import Callable
from statistics import fmean

from assayer.models import Comparison, Experiment, TokenUsage


def compare(experiment_a: Experiment, experiment_b: Experiment) -> Comparison:
    """Report how the second Experiment differs from the first.

    The cost uses the `pricing` each Experiment carries, so the two sides may
    use different models. The Judge's usage is never part of it.

    Args:
        experiment_a: The baseline.
        experiment_b: The Experiment compared with the baseline.

    Returns:
        The deltas (b minus a) per (metric, Field) and the mean token and cost
        deltas per Case; repetitions of a Case are averaged inside it first. The
        usage deltas cover only the Cases both Experiments have, and the others
        are listed in `only_in_a` and `only_in_b`. A
        token or cost delta is None when either side has no recorded usage, and
        the cost one also when either side has no pricing.
    """
    means_a = _mean_scores(experiment_a)
    means_b = _mean_scores(experiment_b)
    metric_deltas = {
        key: means_b[key] - means_a[key] if key in means_a and key in means_b else None
        for key in sorted(means_a.keys() | means_b.keys(), key=lambda k: (k[0], k[1] or ""))
    }

    cases_a = {t.case_id for t in experiment_a.trajectories}
    cases_b = {t.case_id for t in experiment_b.trajectories}
    shared = cases_a & cases_b
    inputs_a, outputs_a, cost_a = _mean_usage_per_case(experiment_a, shared)
    inputs_b, outputs_b, cost_b = _mean_usage_per_case(experiment_b, shared)
    return Comparison(
        metric_deltas=metric_deltas,
        input_tokens_delta=_delta(inputs_a, inputs_b),
        output_tokens_delta=_delta(outputs_a, outputs_b),
        cost_usd_delta=_delta(cost_a, cost_b),
        only_in_a=sorted(cases_a - cases_b, key=str),
        only_in_b=sorted(cases_b - cases_a, key=str),
    )


def _delta(a: float | None, b: float | None) -> float | None:
    return b - a if a is not None and b is not None else None


def _mean_scores(experiment: Experiment) -> dict[tuple[str, str | None], float]:
    values: dict[tuple[str, str | None], list[float]] = defaultdict(list)
    for score in experiment.scores:
        values[(score.name, score.field)].append(score.value)
    return {key: fmean(vals) for key, vals in values.items()}


def _mean_usage_per_case(
    experiment: Experiment, cases: set[str | None]
) -> tuple[float | None, float | None, float | None]:
    """Mean input tokens, output tokens and cost per Case, None where unknown.

    Only the given Cases count.

    Nothing is known when no Step recorded usage (e.g. outputs scored after the
    fact), which is different from having used zero tokens.
    """
    trajectories = [t for t in experiment.trajectories if t.case_id in cases]
    if not any(step.usage is not None for t in trajectories for step in t.steps):
        return None, None, None
    per_case: dict[str | None, list[TokenUsage]] = defaultdict(list)
    for trajectory in trajectories:
        per_case[trajectory.case_id].append(trajectory.total_usage(experiment.pricing))

    def mean(value: Callable[[TokenUsage], float | None]) -> float | None:
        return fmean(fmean(value(u) for u in usages) for usages in per_case.values())  # type: ignore[misc]

    cost = mean(lambda u: u.cost_usd) if experiment.pricing is not None else None
    return mean(lambda u: u.input_tokens), mean(lambda u: u.output_tokens), cost

"""Experiment comparison functionality.

This module provides functions to compare two ExperimentResult objects,
computing metric deltas and token cost differences.

The compare_experiments function can be used standalone, and this module
also monkey-patches the ExperimentResult.compare method when imported.
"""

from collections import defaultdict
from statistics import fmean
from typing import Any

from assayer.models import (
    Comparison,
    Experiment,
    ExperimentResult,
    PricingConfig,
    RunResult,
)


def compare_experiments(
    baseline: ExperimentResult,
    candidate: ExperimentResult,
) -> dict[str, Any]:
    """Compare two experiment results and compute deltas.

    Args:
        baseline: The baseline experiment to compare against.
        candidate: The candidate experiment to compare with the baseline.

    Returns:
        A dictionary containing:
        - metric_deltas: Dict mapping metric names to deltas (candidate - baseline).
          Returns None for metrics present in only one experiment.
        - avg_token_cost_delta: Dict with input_tokens, output_tokens, and cost_usd
          deltas. cost_usd is None when either experiment lacks pricing data.

    Note:
        For empty datasets (zero runs), token deltas may be None when averages
        cannot be computed.
    """
    # Compute metric deltas
    metric_deltas: dict[str, float | None] = {}
    all_metrics = set(baseline.metrics) | set(candidate.metrics)
    for m in all_metrics:
        b = baseline.metrics.get(m)
        c = candidate.metrics.get(m)
        metric_deltas[m] = (c - b) if (b is not None and c is not None) else None

    def _avg(runs: list[RunResult], field: str) -> float | None:
        """Compute average of token usage field values.

        Args:
            runs: List of run results.
            field: Field name to average (e.g., 'input_tokens', 'output_tokens', 'cost_usd').

        Returns:
            Average value or None if no runs, or if any run has None for the field
            and the field is 'cost_usd' (requires complete pricing data).
        """
        if not runs:
            return None

        vals = [getattr(r.token_usage, field) for r in runs]

        # For cost_usd, require all runs to have pricing data
        if field == "cost_usd" and any(val is None for val in vals):
            return None

        # For other fields, filter out None values
        non_none_vals = [val for val in vals if val is not None]
        return sum(non_none_vals) / len(non_none_vals) if non_none_vals else None

    # Compute token usage averages
    b_input = _avg(baseline.runs, "input_tokens")
    c_input = _avg(candidate.runs, "input_tokens")
    b_output = _avg(baseline.runs, "output_tokens")
    c_output = _avg(candidate.runs, "output_tokens")
    b_cost = _avg(baseline.runs, "cost_usd")
    c_cost = _avg(candidate.runs, "cost_usd")

    # Compute deltas, handling None values gracefully
    input_delta = (c_input - b_input) if (b_input is not None and c_input is not None) else None
    output_delta = (
        (c_output - b_output) if (b_output is not None and c_output is not None) else None
    )
    cost_delta = (c_cost - b_cost) if (b_cost is not None and c_cost is not None) else None

    return {
        "metric_deltas": metric_deltas,
        "avg_token_cost_delta": {
            "input_tokens": input_delta,
            "output_tokens": output_delta,
            "cost_usd": cost_delta,
        },
    }


def compare(
    experiment_a: Experiment, experiment_b: Experiment, pricing: PricingConfig | None = None
) -> Comparison:
    """Report how the second Experiment differs from the first.

    Args:
        experiment_a: The baseline.
        experiment_b: The Experiment compared with the baseline.
        pricing: Token prices. Without it, the cost delta is None.

    Returns:
        The deltas (b minus a) per (metric, Field) and the mean token and cost
        deltas per Case. Repetitions of a Case are averaged inside it first.
    """
    means_a = _mean_scores(experiment_a)
    means_b = _mean_scores(experiment_b)
    metric_deltas = {
        key: means_b[key] - means_a[key] if key in means_a and key in means_b else None
        for key in sorted(means_a.keys() | means_b.keys(), key=lambda k: (k[0], k[1] or ""))
    }

    usage_a = _mean_usage_per_case(experiment_a, pricing)
    usage_b = _mean_usage_per_case(experiment_b, pricing)
    deltas = [
        b - a if a is not None and b is not None else None
        for a, b in zip(usage_a, usage_b, strict=True)
    ]
    return Comparison(metric_deltas, *deltas)


def _mean_scores(experiment: Experiment) -> dict[tuple[str, str | None], float]:
    values: dict[tuple[str, str | None], list[float]] = defaultdict(list)
    for score in experiment.scores:
        values[(score.name, score.field)].append(score.value)
    return {key: fmean(vals) for key, vals in values.items()}


def _mean_usage_per_case(
    experiment: Experiment, pricing: PricingConfig | None
) -> tuple[float | None, float | None, float | None]:
    per_case: dict[str | None, list] = defaultdict(list)
    for trajectory in experiment.trajectories:
        per_case[trajectory.case_id].append(trajectory.total_usage(pricing))
    if not per_case:
        return None, None, None
    inputs = fmean(fmean(u.input_tokens for u in usages) for usages in per_case.values())
    outputs = fmean(fmean(u.output_tokens for u in usages) for usages in per_case.values())
    cost = None
    if pricing is not None:
        cost = fmean(fmean(u.cost_usd for u in usages) for usages in per_case.values())
    return inputs, outputs, cost


def _compare_method_impl(self: ExperimentResult, other: ExperimentResult) -> dict[str, Any]:
    """Implementation of ExperimentResult.compare method.

    This function serves as the actual implementation that gets monkey-patched
    onto ExperimentResult.compare when enabled.

    Args:
        self: The baseline experiment to compare against.
        other: The candidate experiment to compare with the baseline.

    Returns:
        A dictionary containing comparison results.
    """
    return compare_experiments(self, other)


def enable_comparison():
    """Enable ExperimentResult.compare() functionality by monkey-patching the method.

    This function replaces the default NotImplementedError implementation
    with the actual comparison functionality. Call this to enable comparison
    features from the runner module.
    """
    ExperimentResult.compare = _compare_method_impl


# Auto-enable comparison when this module is imported
enable_comparison()

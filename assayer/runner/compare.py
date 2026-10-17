"""Experiment comparison functionality.

This module provides functions to compare two ExperimentResult objects,
computing metric deltas and token cost differences.

The compare_experiments function can be used standalone, and this module
also monkey-patches the ExperimentResult.compare method when imported.
"""

from typing import Any

from assayer.models import ExperimentResult, RunResult


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

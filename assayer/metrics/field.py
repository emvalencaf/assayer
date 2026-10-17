"""Metrics for comparing one Field of a structured output.

Each is a trajectory-level metric that sees the Field's value as `final_output` and
the Case's value as `expected_output`, so it runs in a field map, including inside
the items of a list Field.
"""

import re
from numbers import Real

from assayer.metrics.metric import Metric
from assayer.models import Case, Trajectory


def exact_match(trajectory: Trajectory, case: Case) -> float:
    """Score 1 when the value equals the expected one, else 0."""
    return float(trajectory.final_output == case.expected_output)


def _normalize(value):
    return re.sub(r"\s+", " ", value).strip().casefold() if isinstance(value, str) else value


def normalized_exact_match(trajectory: Trajectory, case: Case) -> float:
    """Score 1 when the values are equal ignoring case and surrounding or repeated whitespace.

    Non-string values are compared as they are.
    """
    return float(_normalize(trajectory.final_output) == _normalize(case.expected_output))


def numeric_tolerance(trajectory: Trajectory, case: Case, tolerance: float = 0.0) -> float:
    """Score 1 when the number is within an absolute tolerance of the expected one, else 0.

    Args:
        trajectory: Its `final_output` is the predicted number.
        case: Its `expected_output` is the expected number.
        tolerance: Largest absolute difference that still counts as a match.

    Returns:
        1.0 or 0.0; a value that is not a number (a boolean is not one) scores 0.
    """
    predicted, expected = trajectory.final_output, case.expected_output
    if any(isinstance(v, bool) or not isinstance(v, Real) for v in (predicted, expected)):
        return 0.0
    return float(abs(predicted - expected) <= tolerance)


def list_f1(trajectory: Trajectory, case: Case) -> float:
    """Score a list by the F1 of its items against the expected ones, ignoring order.

    Items are matched by equality and a repeated item must be repeated to match.
    Two empty lists score 1; a value that is not a list scores 0.
    """
    predicted, expected = trajectory.final_output, case.expected_output
    if not isinstance(predicted, list) or not isinstance(expected, list):
        return 0.0
    if not predicted and not expected:
        return 1.0
    remaining = list(expected)
    matched = 0
    for item in predicted:
        if item in remaining:
            remaining.remove(item)
            matched += 1
    if matched == 0:
        return 0.0
    precision, recall = matched / len(predicted), matched / len(expected)
    return 2 * precision * recall / (precision + recall)


def register_field_metrics(registry) -> None:
    """Register the field-level metrics into a registry.

    Registers exact_match, normalized_exact_match, numeric_tolerance and list_f1.

    Args:
        registry: The Registry to fill.

    Raises:
        KeyError: If one of the names is already registered.
    """
    for fn in (exact_match, normalized_exact_match, numeric_tolerance, list_f1):
        registry.register(
            Metric(name=fn.__name__, level="trajectory", fn=fn, requires=("expected_output",))
        )

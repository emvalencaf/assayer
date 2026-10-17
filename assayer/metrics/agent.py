"""Metrics over what an agent did, scored on its Trajectory."""

from assayer.metrics.metric import Metric
from assayer.models import Case, Trajectory

_COUNTED_KINDS = ("model", "tool")


def step_efficiency(trajectory: Trajectory, case: Case) -> float:
    """Score how close the run stayed to the expected number of Steps.

    Computes `min(1, expected_steps / actual_steps)`, where `expected_steps` is
    the length of `Case.expected_steps` and `actual_steps` counts only the
    `model` and `tool` Steps of the Trajectory. A run that took no such Step
    scores 0 unless none was expected, which scores 1.

    Args:
        trajectory: The Trajectory to score.
        case: The Case holding the expected Steps.

    Returns:
        A value in [0, 1]; 1 means no more Steps than expected.
    """
    expected = len(case.expected_steps or [])
    actual = sum(step.kind in _COUNTED_KINDS for step in trajectory.steps)
    if actual == 0:
        return 1.0 if expected == 0 else 0.0
    return min(1.0, expected / actual)


def register_agent_metrics(registry) -> None:
    """Register the agent metrics into a registry.

    Args:
        registry: The Registry to fill.
    """
    registry.register(
        Metric(
            name="step_efficiency",
            level="trajectory",
            requires=("expected_steps",),
            fn=step_efficiency,
        )
    )

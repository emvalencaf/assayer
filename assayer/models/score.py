from dataclasses import dataclass, field
from typing import Any, Literal

ScoreTarget = Literal["step", "trajectory", "experiment"]
SCORE_TARGETS = ("step", "trajectory", "experiment")


@dataclass
class Score:
    """A single named result in [0, 1] of applying a metric.

    Args:
        name: Name of the metric.
        value: Result in the range 0 to 1. Booleans are mapped to 0.0 or 1.0.
        field: Name of the output Field the Score refers to, if any.
        label: Optional categorical label.
        comment: Optional explanation.
        metadata: Free-form extra data.
        target: What was scored: "step", "trajectory" or "experiment".
        target_id: Id of the targeted Step or Trajectory, if any.

    Raises:
        ValueError: If value is not a number, is outside [0, 1], target is
            unknown, or target is 'step' without target_id.
    """

    name: str
    value: float
    metadata: dict[str, Any] = field(default_factory=dict)  # before `field`, which it shadows
    field: str | None = None
    label: str | None = None
    comment: str | None = None
    target: ScoreTarget = "trajectory"
    target_id: str | None = None

    def __post_init__(self) -> None:
        """Normalize booleans and validate value and target.

        Raises:
            ValueError: If value is not a number, is outside [0, 1], target is
            unknown, or target is 'step' without target_id.
        """
        if not isinstance(self.value, (int, float)):
            raise ValueError("value must be a number or a boolean")

        self.value = float(self.value)

        if not 0.0 <= self.value <= 1.0:
            raise ValueError("value must be between 0 and 1")

        if self.target not in SCORE_TARGETS:
            raise ValueError(f"target must be one of {SCORE_TARGETS}")

        if self.target == "step" and self.target_id is None:
            raise ValueError("target_id is required when target is 'step'")

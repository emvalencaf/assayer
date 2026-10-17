from dataclasses import dataclass
from dataclasses import field as dataclass_field
from typing import Any

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
        ValueError: If value is outside [0, 1] or target is unknown.
    """

    name: str
    value: float
    field: str | None = None
    label: str | None = None
    comment: str | None = None
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)
    target: str = "trajectory"
    target_id: str | None = None

    def __post_init__(self) -> None:
        """Normalize booleans and validate value and target.

        Raises:
            ValueError: If value is outside [0, 1] or target is unknown.
        """
        self.value = float(self.value)

        if not 0.0 <= self.value <= 1.0:
            raise ValueError("value must be between 0 and 1")

        if self.target not in SCORE_TARGETS:
            raise ValueError(f"target must be one of {SCORE_TARGETS}")

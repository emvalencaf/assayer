from dataclasses import dataclass
from typing import Any

from assayer.models.token_usage import TokenUsage

STEP_KINDS = ("model", "tool", "retrieval", "other")


@dataclass
class Step:
    """One unit of work inside a Trajectory.

    Args:
        kind: One of "model", "tool", "retrieval" or "other".
        id: Identifier of the Step, used by Scores and by `parent_id`.
        parent_id: Id of the Step that contains this one, if any.
        name: Name of the tool or operation.
        model: Model name, for model Steps.
        input: What the Step received.
        output: What the Step produced.
        error: Error message recorded as data; it never invalidates the Trajectory.
        usage: Token usage, allowed on model Steps only.

    Raises:
        ValueError: If kind is unknown or usage is given on a non-model Step.
    """

    kind: str
    id: str | None = None
    parent_id: str | None = None
    name: str | None = None
    model: str | None = None
    input: Any = None
    output: Any = None
    error: str | None = None
    usage: TokenUsage | None = None

    def __post_init__(self) -> None:
        """Validate kind and usage.

        Raises:
            ValueError: If kind is unknown or usage is given on a non-model Step.
        """
        if self.kind not in STEP_KINDS:
            raise ValueError(f"kind must be one of {STEP_KINDS}")

        if self.usage is not None and self.kind != "model":
            raise ValueError("usage is only allowed on model steps")

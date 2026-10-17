from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldEvaluation:
    """Represents the evaluation result for a single output field.

    This dataclass encapsulates the evaluation of a specific field from a target
    function's output, including the expected vs obtained values, score, and metadata
    about the evaluation method used.

    Args:
        field_name: Name of the output field being evaluated. Must be non-empty.
        evaluator_method: Identifier of the evaluation method used (e.g., "bleu",
            "llm_judge"). Must be non-empty.
        expected_value: Ground-truth value for comparison.
        obtained_value: Value produced by the target function.
        score: Evaluation score, normalized to the range [0.0, 1.0].
        prompt_hash: SHA-256 hash of the judge prompt when applicable. None for
            non-judge evaluators.
        metadata: Arbitrary key-value pairs for extensibility. Defaults to empty dict.

    Raises:
        ValueError: If field_name is empty, evaluator_method is empty, or score
            is outside [0.0, 1.0].
    """

    field_name: str
    evaluator_method: str
    expected_value: Any
    obtained_value: Any
    score: float
    prompt_hash: str | None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate field values after dataclass initialization.

        Raises:
            ValueError: If any field value violates the validation constraints.
        """
        if not self.field_name or not self.field_name.strip():
            raise ValueError("field_name must not be empty")

        if not self.evaluator_method or not self.evaluator_method.strip():
            raise ValueError("evaluator_method must not be empty")

        if self.score < 0.0 or self.score > 1.0:
            raise ValueError("score must be in the range [0.0, 1.0]")

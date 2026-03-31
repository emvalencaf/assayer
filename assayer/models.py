"""Core domain models for the assayer framework.

This module contains foundational data structures used throughout the system
for carrying evaluation results, token usage data, and experiment-level aggregations.
"""

from dataclasses import dataclass, field
from typing import Union, Any


@dataclass
class TokenUsage:
    """Tracks token consumption and cost for LLM API calls.

    This dataclass represents the token usage metrics for a single LLM API call,
    including input tokens, output tokens, and optional cost estimation.

    Args:
        input_tokens: Number of input tokens consumed. Must be non-negative.
        output_tokens: Number of output tokens generated. Must be non-negative.
        cost_usd: Estimated USD cost of the API call. None when no pricing
            table is available. When provided, must be non-negative.

    Raises:
        ValueError: If input_tokens < 0, output_tokens < 0, or cost_usd < 0.
    """

    input_tokens: int
    output_tokens: int
    cost_usd: Union[float, None]

    def __post_init__(self) -> None:
        """Validate field values after dataclass initialization.

        Raises:
            ValueError: If any field value violates the validation constraints.
        """
        if self.input_tokens < 0:
            raise ValueError("input_tokens must be non-negative")

        if self.output_tokens < 0:
            raise ValueError("output_tokens must be non-negative")

        if self.cost_usd is not None and self.cost_usd < 0:
            raise ValueError("cost_usd must be non-negative when provided")


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
    prompt_hash: Union[str, None]
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
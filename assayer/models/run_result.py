
from dataclasses import dataclass, field
from typing import Any

from assayer.models.field_evaluation import FieldEvaluation
from assayer.models.token_usage import TokenUsage


@dataclass
class RunResult:
    """Wraps a single example execution with input, output, evaluations, and token usage.

    This dataclass represents the complete result of executing a target function
    on a single input, including the raw input/output, evaluation results for
    each output field, and token usage metrics.

    Args:
        input: The input passed to the target function.
        output: The raw output returned by the target function.
        token_usage: Token consumption metrics for this execution.
        evaluations: Per-field evaluation results. Defaults to empty list.
    """

    input: Any
    output: Any
    token_usage: TokenUsage
    evaluations: list[FieldEvaluation] = field(default_factory=list)

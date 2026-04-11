"""ConsistencyRunResult dataclass for storing per-run consistency evaluation results."""

from dataclasses import dataclass
from typing import Any

from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation


@dataclass
class ConsistencyRunResult:
    """Result of evaluating a single dataset input for consistency across multiple runs.

    Stores the original input alongside a mapping from field names to their
    respective consistency evaluation outcomes.

    Args:
        input: The dataset input that was evaluated. Can be any type.
        per_field_evaluations: Mapping from field name to the consistency
            evaluation result for that field.
    """

    input: Any
    per_field_evaluations: dict[str, ConsistencyFieldEvaluation]

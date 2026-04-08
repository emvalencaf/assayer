"""Consistency evaluation models for the assayer framework.

This module contains data structures that carry consistency evaluation results
for groups of repeated evaluations, supporting both field-level and dataset-level
aggregations.
"""

from dataclasses import dataclass, field
from typing import Union

from assayer.models import FieldEvaluation

__all__ = ["ConsistencyFieldEvaluation"]


@dataclass
class ConsistencyFieldEvaluation:
    """Represents consistency measurement for a single group across multiple runs.

    This dataclass captures the consistency evaluation results for one input case
    evaluated across k runs, including agreement rates, entropy, standard deviation,
    and pass@k metrics.

    Args:
        group_key: Value of the group_by field. None in live mode where there is no
            dataset group key.
        n: Number of runs in this group. Must be >= 1.
        agreement_rate: Proportion of runs that agree with the dominant result.
            Range: [0.0, 1.0].
        dominant_label: Most frequent label across runs. None when labels are
            unavailable (e.g., numeric-only evaluators).
        entropy: Information entropy of the label distribution. Range: [0.0, log₂(n_distinct_labels)].
            Must be >= 0.0.
        score_std: Standard deviation of scores across runs. Range: [0.0, ∞).
            Will be 0.0 when n == 1.
        correct_rate: Proportion of runs that matched the reference exactly.
            Range: [0.0, 1.0].
        pass_at_k: True if any run matched the reference exactly.
        recall_at_k: Best recall achieved across all runs. Range: [0.0, 1.0].
        raw_results: Individual evaluator outputs for each run. Defaults to empty list.

    Raises:
        ValueError: If n < 1, agreement_rate outside [0.0, 1.0], entropy < 0.0,
            score_std < 0.0, correct_rate outside [0.0, 1.0], or recall_at_k
            outside [0.0, 1.0].
    """

    group_key: Union[str, None]
    n: int
    agreement_rate: float
    dominant_label: Union[str, None]
    entropy: float
    score_std: float
    correct_rate: float
    pass_at_k: bool
    recall_at_k: float
    raw_results: list[FieldEvaluation] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate field values after dataclass initialization.

        Raises:
            ValueError: If any field value violates the validation constraints.
        """
        if self.n < 1:
            raise ValueError("n must be >= 1")

        if self.agreement_rate < 0.0 or self.agreement_rate > 1.0:
            raise ValueError("agreement_rate must be in the range [0.0, 1.0]")

        if self.entropy < 0.0:
            raise ValueError("entropy must be >= 0.0")

        if self.score_std < 0.0:
            raise ValueError("score_std must be >= 0.0")

        if self.correct_rate < 0.0 or self.correct_rate > 1.0:
            raise ValueError("correct_rate must be in the range [0.0, 1.0]")

        if self.recall_at_k < 0.0 or self.recall_at_k > 1.0:
            raise ValueError("recall_at_k must be in the range [0.0, 1.0]")
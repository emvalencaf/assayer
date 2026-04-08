from dataclasses import dataclass, field

from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation


@dataclass
class ConsistencySummary:
    """Aggregates multiple ConsistencyFieldEvaluation instances from evaluate_dataset.

    This dataclass provides dataset-level aggregation of consistency evaluation results,
    including mean metrics across groups and identification of worst-performing groups.

    Args:
        per_group: List of ConsistencyFieldEvaluation instances, one per group after
            min_k filtering. Defaults to empty list.
        mean_agreement_rate: Average agreement rate across all groups. Range: [0.0, 1.0].
        mean_entropy: Average entropy across all groups. Range: [0.0, ∞).
        mean_score_std: Average standard deviation of scores across all groups. Range: [0.0, ∞).
        mean_correct_rate: Average correct rate across all groups. Range: [0.0, 1.0].
        pass_at_k_rate: Proportion of groups where pass_at_k is True. Range: [0.0, 1.0].
        mean_recall_at_k: Average recall@k across all groups. Range: [0.0, 1.0].
        worst_groups: List of ConsistencyFieldEvaluation instances representing the
            top-10 worst-performing groups by ascending agreement_rate. Defaults to empty list.

    Raises:
        ValueError: If pass_at_k_rate, mean_correct_rate, mean_recall_at_k, or
            mean_agreement_rate are outside [0.0, 1.0].
    """

    mean_agreement_rate: float
    mean_entropy: float
    mean_score_std: float
    mean_correct_rate: float
    pass_at_k_rate: float
    mean_recall_at_k: float
    per_group: list[ConsistencyFieldEvaluation] = field(default_factory=list)
    worst_groups: list[ConsistencyFieldEvaluation] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate field values after dataclass initialization.

        Raises:
            ValueError: If any field value violates the validation constraints.
        """
        if self.pass_at_k_rate < 0.0 or self.pass_at_k_rate > 1.0:
            raise ValueError("pass_at_k_rate must be in the range [0.0, 1.0]")

        if self.mean_correct_rate < 0.0 or self.mean_correct_rate > 1.0:
            raise ValueError("mean_correct_rate must be in the range [0.0, 1.0]")

        if self.mean_recall_at_k < 0.0 or self.mean_recall_at_k > 1.0:
            raise ValueError("mean_recall_at_k must be in the range [0.0, 1.0]")

        if self.mean_agreement_rate < 0.0 or self.mean_agreement_rate > 1.0:
            raise ValueError("mean_agreement_rate must be in the range [0.0, 1.0]")
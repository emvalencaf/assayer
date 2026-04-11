"""ConsistencyReport dataclass for storing experiment-level consistency results."""

from dataclasses import dataclass

from assayer.models.consistency_run_result import ConsistencyRunResult
from assayer.models.consistency_summary import ConsistencySummary


@dataclass
class ConsistencyReport:
    """Aggregated consistency evaluation results for a complete experiment.

    Holds experiment-level metadata along with per-field summaries and
    per-run detailed results produced by a consistency evaluation pipeline.

    Args:
        experiment_name: Human-readable name identifying the experiment.
            Must not be empty or whitespace-only.
        k: Number of repetitions used per input during evaluation.
            Must be greater than or equal to 1.
        per_field: Mapping from field name to its aggregated
            ConsistencySummary across all dataset inputs.
        runs: List of ConsistencyRunResult instances, one per dataset input.

    Raises:
        ValueError: If experiment_name is empty or contains only whitespace.
        ValueError: If k is less than 1.
    """

    experiment_name: str
    k: int
    per_field: dict[str, ConsistencySummary]
    runs: list[ConsistencyRunResult]

    def __post_init__(self) -> None:
        """Validate field values after dataclass initialization.

        Raises:
            ValueError: If experiment_name is empty or whitespace-only.
            ValueError: If k is less than 1.
        """
        if not self.experiment_name.strip():
            raise ValueError("experiment_name must not be empty or whitespace-only.")
        if self.k < 1:
            raise ValueError("k must be greater than or equal to 1.")

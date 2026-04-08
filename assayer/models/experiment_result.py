
from dataclasses import dataclass, field

from assayer.models.run_result import RunResult


@dataclass
class ExperimentResult:
    """Represents the results of an experiment containing multiple runs.

    This dataclass aggregates the results of multiple runs of a target function
    across different inputs, providing a named collection for experiment tracking
    and comparison.

    Args:
        experiment_name: Human-readable experiment name. Must be non-empty and
            non-whitespace-only.
        runs: Collection of run results. Defaults to empty list.
        metrics: Dictionary mapping metric names to computed aggregated values.
            Defaults to empty dict.

    Raises:
        ValueError: If experiment_name is empty or whitespace-only after stripping.
    """

    experiment_name: str
    runs: list[RunResult] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate field values after dataclass initialization.

        Raises:
            ValueError: If experiment_name is empty or whitespace-only.
        """
        if not self.experiment_name.strip():
            raise ValueError("experiment_name must not be empty")

    def compare(self, other: "ExperimentResult") -> dict:
        """Compare this experiment result with another experiment result.

        Args:
            other: The other ExperimentResult to compare against.

        Returns:
            A dictionary containing comparison results.

        Raises:
            NotImplementedError: This method is implemented in the runner spec.
        """
        raise NotImplementedError("compare() is implemented in the runner spec")
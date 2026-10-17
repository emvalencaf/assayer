from dataclasses import dataclass, field

from assayer.models.evaluation_failure import EvaluationFailure
from assayer.models.pricing_config import PricingConfig
from assayer.models.score import Score
from assayer.models.token_usage import TokenUsage
from assayer.models.trajectory import Trajectory


@dataclass
class Experiment:
    """The Trajectories and Scores produced by running one target over a Dataset.

    Args:
        name: Human-readable name. Must be non-empty and non-whitespace-only.
        trajectories: One Trajectory per repetition of each Case.
        scores: Scores of Steps, Trajectories and the Experiment as a whole.
        failures: Metrics that could not be computed.
        judge_usage: Token usage of the Judge, kept apart from the target's totals.

    Raises:
        ValueError: If name is empty or whitespace-only.
    """

    name: str
    trajectories: list[Trajectory] = field(default_factory=list)
    scores: list[Score] = field(default_factory=list)
    failures: list[EvaluationFailure] = field(default_factory=list)
    judge_usage: TokenUsage | None = None

    def __post_init__(self) -> None:
        """Validate name.

        Raises:
            ValueError: If name is empty or whitespace-only.
        """
        if not self.name.strip():
            raise ValueError("name must not be empty")

    def total_usage(self, pricing: PricingConfig | None = None) -> TokenUsage:
        """Sum the token usage of all Trajectories, excluding the Judge.

        Args:
            pricing: Token prices. Without it, `cost_usd` of the result is None.

        Returns:
            The summed usage, with cost only when pricing is given.
        """
        total = TokenUsage(input_tokens=0, output_tokens=0, cost_usd=0.0 if pricing else None)
        for trajectory in self.trajectories:
            total = total + trajectory.total_usage(pricing)
        return total

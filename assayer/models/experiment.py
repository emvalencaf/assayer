from dataclasses import dataclass, field

from assayer.models.case import Case
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
        judge_calls: How many calls were made to the Judge.
        cases: The Cases the target ran over, each with the id its Trajectories carry as
            `case_id`; the references that Experiment-level metrics compare them to.
        pricing: Prices of the target's model, kept so the cost can be recomputed
            and compared. They never apply to `judge_usage`, whose model is
            another one: price that with `total_judge_usage(pricing)`.

    Raises:
        ValueError: If name is empty or whitespace-only.
    """

    name: str
    trajectories: list[Trajectory] = field(default_factory=list)
    scores: list[Score] = field(default_factory=list)
    failures: list[EvaluationFailure] = field(default_factory=list)
    judge_usage: TokenUsage | None = None
    judge_calls: int = 0
    pricing: PricingConfig | None = None
    cases: list[Case] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate name.

        Raises:
            ValueError: If name is empty or whitespace-only.
        """
        if not self.name.strip():
            raise ValueError("name must not be empty")

    def scores_by_field(self) -> dict[str | None, list[Score]]:
        """Group the Scores by the output Field they refer to.

        Returns:
            The Scores per Field path, in the order they were computed. Scores of
            the whole output are under the key None.
        """
        grouped: dict[str | None, list[Score]] = {}
        for score in self.scores:
            grouped.setdefault(score.field, []).append(score)
        return grouped

    def total_usage(self, pricing: PricingConfig | None = None) -> TokenUsage:
        """Sum the token usage of all Trajectories, excluding the Judge.

        Args:
            pricing: Token prices. Defaults to the Experiment's own; without any,
                `cost_usd` of the result is None.

        Returns:
            The summed usage, with cost only when pricing is known.
        """
        pricing = pricing or self.pricing
        total = TokenUsage(input_tokens=0, output_tokens=0, cost_usd=0.0 if pricing else None)
        for trajectory in self.trajectories:
            total = total + trajectory.total_usage(pricing)
        return total

    def total_judge_usage(self, pricing: PricingConfig | None = None) -> TokenUsage | None:
        """Return the Judge's token usage, priced when prices are given.

        Args:
            pricing: Prices of the Judge model. Without it, `cost_usd` of the
                result is None.

        Returns:
            The Judge usage, or None when no Judge was used.
        """
        if self.judge_usage is None:
            return None

        usage = self.judge_usage
        cost = None
        if pricing is not None:
            cost = pricing.cost(usage.input_tokens, usage.output_tokens)
        return TokenUsage(usage.input_tokens, usage.output_tokens, cost)

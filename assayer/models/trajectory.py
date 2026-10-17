from dataclasses import dataclass, field
from typing import Any

from assayer.models.pricing_config import PricingConfig
from assayer.models.step import Step
from assayer.models.token_usage import TokenUsage


@dataclass
class Trajectory:
    """The ordered record of what an agent did for one input.

    Args:
        steps: Ordered Steps. May be empty.
        session_id: Identifier of the session the Trajectory belongs to.
        final_output: The final answer, if any.
        final_state: The end state observed after the run, if any.
        case_id: Id of the Case this Trajectory was produced for.
        repetition: Index of the repetition of the Case. Defaults to 0.
    """

    steps: list[Step] = field(default_factory=list)
    session_id: str | None = None
    final_output: Any = None
    final_state: Any = None
    case_id: str | None = None
    repetition: int = 0

    def total_usage(self, pricing: PricingConfig | None = None) -> TokenUsage:
        """Sum the token usage of the model Steps.

        Args:
            pricing: Token prices. Without it, `cost_usd` of the result is None.

        Returns:
            The summed usage, with cost only when pricing is given.
        """
        usages = [step.usage for step in self.steps if step.usage is not None]
        input_tokens = sum(usage.input_tokens for usage in usages)
        output_tokens = sum(usage.output_tokens for usage in usages)
        cost = None
        if pricing is not None:
            cost = pricing.cost(input_tokens, output_tokens)
        return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=cost)

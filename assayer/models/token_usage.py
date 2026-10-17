from dataclasses import dataclass


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
    cost_usd: float | None

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

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Sum two usages; the cost is None unless both costs are known.

        Args:
            other: The usage to add.

        Returns:
            A new TokenUsage with the summed tokens and cost.
        """
        cost = None
        if self.cost_usd is not None and other.cost_usd is not None:
            cost = self.cost_usd + other.cost_usd

        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cost_usd=cost,
        )

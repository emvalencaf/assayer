from dataclasses import dataclass


@dataclass
class PricingConfig:
    """Configuration for LLM token pricing.

    This dataclass holds the cost per token for input and output tokens,
    used to calculate the total cost of LLM API calls during evaluation.

    Args:
        cost_per_input_token: Cost per input token in the pricing unit (e.g., USD).
        cost_per_output_token: Cost per output token in the pricing unit (e.g., USD).
    """

    cost_per_input_token: float
    cost_per_output_token: float

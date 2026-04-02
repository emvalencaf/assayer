"""Token usage extraction utilities for LLM evaluation runs.

This module provides functions to extract token usage information from
LangChain-compatible result objects and compute optional costs based on
pricing configuration.
"""

from typing import Any

from assayer.models import TokenUsage
from assayer.runner.pricing import PricingConfig


def extract_token_usage(
    result: Any,
    pricing_config: PricingConfig | None,
) -> TokenUsage:
    """Extract token counts from a LangChain-compatible result object.

    Looks for a `usage_metadata` attribute with `input_tokens` and
    `output_tokens` keys. Defaults to 0 if not found. Computes cost
    using pricing configuration if provided.

    Args:
        result: Return value from the target function. Should contain
            a `usage_metadata` attribute with token count information.
        pricing_config: Optional pricing configuration for cost calculation.
            If provided, cost_usd will be computed using the formula:
            input_tokens * cost_per_input_token + output_tokens * cost_per_output_token.

    Returns:
        A populated TokenUsage instance with extracted token counts and
        optional cost information.
    """
    metadata = getattr(result, "usage_metadata", None) or {}
    input_tokens = int(metadata.get("input_tokens", 0))
    output_tokens = int(metadata.get("output_tokens", 0))
    cost_usd: float | None = None
    if pricing_config is not None:
        cost_usd = (
            input_tokens * pricing_config.cost_per_input_token
            + output_tokens * pricing_config.cost_per_output_token
        )
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
    )
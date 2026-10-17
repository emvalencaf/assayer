"""Tests for PricingConfig."""

from assayer.models import PricingConfig


class TestPricingConfig:
    def test_cost_prices_input_and_output_tokens(self):
        pricing = PricingConfig(cost_per_input_token=0.5, cost_per_output_token=2.0)

        assert pricing.cost(10, 3) == 11.0

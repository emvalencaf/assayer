"""Tests for PricingConfig and its compatibility alias in the runner."""

from assayer.models import PricingConfig
from assayer.runner.pricing import PricingConfig as RunnerPricingConfig


class TestPricingConfig:
    def test_runner_pricing_still_exposes_the_same_class(self):
        assert RunnerPricingConfig is PricingConfig

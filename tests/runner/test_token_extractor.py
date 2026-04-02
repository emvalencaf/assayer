"""Tests for assayer.runner.token_extractor module.

Tests for the extract_token_usage function that extracts token usage data
from LangChain-compatible result objects and computes optional costs.
"""

import pytest

from assayer.models import TokenUsage
from assayer.runner.pricing import PricingConfig
from assayer.runner.token_extractor import extract_token_usage


class TestExtractTokenUsage:
    """Test cases for extract_token_usage function."""

    def test_extracts_tokens_from_usage_metadata_dict(self):
        """Test extraction of input_tokens and output_tokens from result.usage_metadata dict."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 150, "output_tokens": 75})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 150
        assert token_usage.output_tokens == 75
        assert token_usage.cost_usd == 0.30  # 150 * 0.001 + 75 * 0.002

    def test_defaults_to_zero_when_usage_metadata_absent(self):
        """Test defaults to 0 when usage_metadata attribute is absent."""
        # Arrange
        class MockResult:
            pass  # No usage_metadata attribute

        result = MockResult()
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd == 0.0

    def test_defaults_to_zero_when_usage_metadata_is_none(self):
        """Test defaults to 0 when usage_metadata attribute is None."""
        # Arrange
        class MockResult:
            def __init__(self):
                self.usage_metadata = None

        result = MockResult()
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd == 0.0

    def test_defaults_to_zero_when_keys_missing_from_metadata(self):
        """Test defaults to 0 when usage_metadata dict is missing required keys."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"some_other_key": "value"})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd == 0.0

    def test_handles_partial_metadata_with_missing_input_tokens(self):
        """Test handles partial metadata dict missing input_tokens key."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"output_tokens": 50})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 50
        assert token_usage.cost_usd == 0.10  # 0 * 0.001 + 50 * 0.002

    def test_handles_partial_metadata_with_missing_output_tokens(self):
        """Test handles partial metadata dict missing output_tokens key."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 100})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 100
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd == 0.10  # 100 * 0.001 + 0 * 0.002

    def test_cost_calculation_when_pricing_config_provided(self):
        """Test cost_usd calculation formula when PricingConfig is provided."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 1000, "output_tokens": 500})
        pricing_config = PricingConfig(cost_per_input_token=0.0015, cost_per_output_token=0.003)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        expected_cost = 1000 * 0.0015 + 500 * 0.003  # 1.5 + 1.5 = 3.0
        assert token_usage.input_tokens == 1000
        assert token_usage.output_tokens == 500
        assert token_usage.cost_usd == expected_cost

    def test_cost_is_none_when_no_pricing_config(self):
        """Test cost_usd is None when no PricingConfig is provided."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 200, "output_tokens": 100})

        # Act
        token_usage = extract_token_usage(result, None)

        # Assert
        assert token_usage.input_tokens == 200
        assert token_usage.output_tokens == 100
        assert token_usage.cost_usd is None

    def test_converts_string_token_values_to_int(self):
        """Test conversion of string token values to integers."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": "250", "output_tokens": "125"})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 250
        assert token_usage.output_tokens == 125
        assert token_usage.cost_usd == 0.50  # 250 * 0.001 + 125 * 0.002

    def test_handles_zero_token_values(self):
        """Test handling of zero token values."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 0, "output_tokens": 0})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd == 0.0

    def test_handles_float_token_values_converts_to_int(self):
        """Test conversion of float token values to integers."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 300.7, "output_tokens": 150.9})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert token_usage.input_tokens == 300  # int() truncates
        assert token_usage.output_tokens == 150  # int() truncates
        assert token_usage.cost_usd == 0.60  # 300 * 0.001 + 150 * 0.002

    def test_with_different_pricing_rates(self):
        """Test cost calculation with different pricing rates."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 500, "output_tokens": 300})

        # Higher cost for output tokens
        pricing_config = PricingConfig(cost_per_input_token=0.0005, cost_per_output_token=0.01)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        expected_cost = 500 * 0.0005 + 300 * 0.01  # 0.25 + 3.0 = 3.25
        assert token_usage.input_tokens == 500
        assert token_usage.output_tokens == 300
        assert token_usage.cost_usd == expected_cost

    def test_returns_token_usage_instance(self):
        """Test that function returns a TokenUsage instance."""
        # Arrange
        class MockResult:
            def __init__(self, usage_metadata):
                self.usage_metadata = usage_metadata

        result = MockResult({"input_tokens": 100, "output_tokens": 50})
        pricing_config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        # Act
        token_usage = extract_token_usage(result, pricing_config)

        # Assert
        assert isinstance(token_usage, TokenUsage)
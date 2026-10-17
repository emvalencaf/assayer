"""Tests for TokenUsage dataclass from assayer.models module."""

import pytest

from assayer.models import TokenUsage


class TestTokenUsage:
    """Test cases for TokenUsage dataclass."""

    def test_token_usage_instantiation_with_valid_values(self):
        """Test AC-SPEC-001: TokenUsage can be instantiated with valid values; attributes return provided values."""
        # Test with all fields provided
        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.025)

        assert token_usage.input_tokens == 100
        assert token_usage.output_tokens == 50
        assert token_usage.cost_usd == 0.025

    def test_token_usage_with_none_cost_usd(self):
        """Test that TokenUsage can be instantiated with cost_usd=None."""
        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=None)

        assert token_usage.input_tokens == 100
        assert token_usage.output_tokens == 50
        assert token_usage.cost_usd is None

    def test_token_usage_with_zero_tokens_and_none_cost(self):
        """Test that TokenUsage(input_tokens=0, output_tokens=0, cost_usd=None) succeeds."""
        token_usage = TokenUsage(input_tokens=0, output_tokens=0, cost_usd=None)

        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd is None

    def test_token_usage_with_zero_tokens_and_zero_cost(self):
        """Test that TokenUsage(input_tokens=0, output_tokens=0, cost_usd=0.0) succeeds."""
        token_usage = TokenUsage(input_tokens=0, output_tokens=0, cost_usd=0.0)

        assert token_usage.input_tokens == 0
        assert token_usage.output_tokens == 0
        assert token_usage.cost_usd == 0.0

    def test_negative_input_tokens_raises_value_error(self):
        """Test AC-SPEC-002: TokenUsage.__post_init__ raises ValueError for negative input_tokens."""
        with pytest.raises(ValueError, match="input_tokens"):
            TokenUsage(input_tokens=-1, output_tokens=50, cost_usd=0.025)

    def test_negative_output_tokens_raises_value_error(self):
        """Test AC-SPEC-002: TokenUsage.__post_init__ raises ValueError for negative output_tokens."""
        with pytest.raises(ValueError, match="output_tokens"):
            TokenUsage(input_tokens=100, output_tokens=-1, cost_usd=0.025)

    def test_negative_cost_usd_raises_value_error(self):
        """Test AC-SPEC-002: TokenUsage.__post_init__ raises ValueError for negative cost_usd."""
        with pytest.raises(ValueError, match="cost_usd"):
            TokenUsage(input_tokens=100, output_tokens=50, cost_usd=-0.01)

    def test_multiple_negative_values_raises_value_error(self):
        """Test that multiple validation errors are caught (first one encountered)."""
        with pytest.raises(ValueError):
            TokenUsage(input_tokens=-1, output_tokens=-1, cost_usd=-0.01)

    def test_edge_case_large_token_counts(self):
        """Test with large but valid token counts."""
        token_usage = TokenUsage(input_tokens=1000000, output_tokens=500000, cost_usd=100.0)

        assert token_usage.input_tokens == 1000000
        assert token_usage.output_tokens == 500000
        assert token_usage.cost_usd == 100.0

    def test_edge_case_fractional_cost(self):
        """Test with very small fractional cost values."""
        token_usage = TokenUsage(input_tokens=1, output_tokens=1, cost_usd=0.0001)

        assert token_usage.input_tokens == 1
        assert token_usage.output_tokens == 1
        assert token_usage.cost_usd == 0.0001


class TestTokenUsageAddition:
    """Test cases for summing TokenUsage values."""

    def test_tokens_are_summed_and_cost_kept_when_both_known(self):
        total = TokenUsage(1, 2, 0.5) + TokenUsage(3, 4, 0.25)

        assert (total.input_tokens, total.output_tokens, total.cost_usd) == (4, 6, 0.75)

    def test_cost_is_none_when_either_cost_is_unknown(self):
        assert (TokenUsage(1, 2, 0.5) + TokenUsage(3, 4, None)).cost_usd is None

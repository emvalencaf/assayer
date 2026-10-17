"""Tests for the Step model."""

import pytest

from assayer.models import Step, TokenUsage


class TestStep:
    @pytest.mark.parametrize("kind", ["model", "tool", "retrieval", "other"])
    def test_known_kinds_are_accepted(self, kind):
        assert Step(kind=kind).kind == kind

    def test_unknown_kind_is_rejected(self):
        with pytest.raises(ValueError):
            Step(kind="span")

    def test_usage_is_accepted_on_model_steps(self):
        usage = TokenUsage(input_tokens=1, output_tokens=1, cost_usd=None)

        assert Step(kind="model", usage=usage).usage is usage

    def test_usage_is_rejected_on_non_model_steps(self):
        with pytest.raises(ValueError):
            Step(kind="tool", usage=TokenUsage(1, 1, None))

    def test_error_is_data_on_the_step(self):
        assert Step(kind="tool", error="timeout").error == "timeout"

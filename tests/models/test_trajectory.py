"""Tests for the Trajectory and Step models."""

import pytest

from assayer.models import PricingConfig, Step, TokenUsage, Trajectory


def _model_step(input_tokens: int, output_tokens: int) -> Step:
    return Step(
        kind="model",
        model="m",
        usage=TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=None),
    )


class TestTrajectory:
    def test_empty_trajectory_without_final_output_is_valid(self):
        trajectory = Trajectory()

        assert trajectory.steps == []
        assert trajectory.final_output is None

    def test_step_error_does_not_invalidate_trajectory(self):
        trajectory = Trajectory(steps=[Step(kind="tool", error="timeout")])

        assert trajectory.steps[0].error == "timeout"

    def test_optional_fields_are_kept(self):
        trajectory = Trajectory(
            session_id="s1", final_output="a", final_state={"k": 1}, case_id="c1", repetition=2
        )

        assert (trajectory.session_id, trajectory.final_output) == ("s1", "a")
        assert (trajectory.final_state, trajectory.case_id, trajectory.repetition) == (
            {"k": 1},
            "c1",
            2,
        )

    def test_totals_come_from_model_steps_only(self):
        trajectory = Trajectory(steps=[_model_step(10, 5), Step(kind="tool"), _model_step(3, 2)])

        total = trajectory.total_usage()

        assert (total.input_tokens, total.output_tokens) == (13, 7)

    def test_cost_is_none_without_prices(self):
        assert Trajectory(steps=[_model_step(10, 5)]).total_usage().cost_usd is None

    def test_cost_is_derived_when_prices_given(self):
        pricing = PricingConfig(cost_per_input_token=0.01, cost_per_output_token=0.1)

        total = Trajectory(steps=[_model_step(10, 5)]).total_usage(pricing)

        assert total.cost_usd == pytest.approx(0.6)

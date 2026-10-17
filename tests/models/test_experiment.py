"""Tests for the Experiment model."""

import pytest

from assayer.models import (
    EvaluationFailure,
    Experiment,
    PricingConfig,
    Score,
    Step,
    TokenUsage,
    Trajectory,
)


def _trajectory(input_tokens: int, output_tokens: int) -> Trajectory:
    usage = TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens, cost_usd=None)
    return Trajectory(steps=[Step(kind="model", usage=usage), Step(kind="tool")])


class TestExperiment:
    def test_empty_experiment_is_valid(self):
        experiment = Experiment(name="e")

        assert experiment.trajectories == []
        assert experiment.scores == []
        assert experiment.failures == []
        assert experiment.judge_usage is None

    def test_name_must_not_be_blank(self):
        with pytest.raises(ValueError):
            Experiment(name=" ")

    def test_totals_are_derived_from_trajectories(self):
        experiment = Experiment(name="e", trajectories=[_trajectory(10, 5), _trajectory(1, 2)])

        total = experiment.total_usage()

        assert (total.input_tokens, total.output_tokens, total.cost_usd) == (11, 7, None)

    def test_cost_appears_only_when_prices_given(self):
        experiment = Experiment(name="e", trajectories=[_trajectory(10, 5), _trajectory(10, 5)])
        pricing = PricingConfig(cost_per_input_token=0.01, cost_per_output_token=0.1)

        assert experiment.total_usage(pricing).cost_usd == pytest.approx(1.2)

    def test_judge_usage_is_kept_apart_from_trajectory_totals(self):
        judge = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=None)
        experiment = Experiment(name="e", trajectories=[_trajectory(1, 1)], judge_usage=judge)

        assert experiment.total_usage().input_tokens == 1
        assert experiment.judge_usage is judge

    def test_scores_and_failures_are_kept(self):
        experiment = Experiment(
            name="e",
            scores=[Score(name="pass^k", value=0.5, target="experiment")],
            failures=[EvaluationFailure(metric="m", error="boom", target_id="t1")],
        )

        assert experiment.scores[0].value == 0.5
        assert experiment.failures[0].error == "boom"

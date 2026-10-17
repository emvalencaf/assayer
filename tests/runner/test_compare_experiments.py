"""Tests for comparing two Experiments."""

import pytest

from assayer.models import Experiment, PricingConfig, Score, Step, TokenUsage, Trajectory
from assayer.runner import compare


def _trajectory(case_id, tokens=None):
    steps = [Step(kind="model", usage=TokenUsage(*tokens, None))] if tokens else []
    return Trajectory(steps=steps, case_id=case_id)


class TestMetricDeltas:
    def test_delta_per_metric_and_field_is_b_minus_a(self):
        a = Experiment(
            "a",
            scores=[
                Score("f1", 0.5, field="name"),
                Score("f1", 0.7, field="name"),
                Score("f1", 0.2, field="date"),
            ],
        )
        b = Experiment("b", scores=[Score("f1", 0.9, field="name"), Score("f1", 0.2, field="date")])

        result = compare(a, b)

        assert result.metric_deltas[("f1", "name")] == pytest.approx(0.3)
        assert result.metric_deltas[("f1", "date")] == pytest.approx(0.0)

    def test_metric_on_one_side_only_is_none(self):
        a = Experiment("a", scores=[Score("exact", 1.0)])
        b = Experiment("b", scores=[Score("rouge", 0.5)])

        deltas = compare(a, b).metric_deltas

        assert deltas == {("exact", None): None, ("rouge", None): None}

    def test_same_metric_on_another_field_is_a_separate_key(self):
        a = Experiment("a", scores=[Score("f1", 0.5, field="x")])
        b = Experiment("b", scores=[Score("f1", 0.5)])

        assert compare(a, b).metric_deltas == {("f1", "x"): None, ("f1", None): None}


class TestUsageDeltas:
    def test_mean_tokens_per_case(self):
        a = Experiment(
            "a", trajectories=[_trajectory("c1", (100, 10)), _trajectory("c2", (300, 30))]
        )
        b = Experiment(
            "b", trajectories=[_trajectory("c1", (50, 10)), _trajectory("c2", (150, 50))]
        )

        result = compare(a, b)

        assert result.input_tokens_delta == pytest.approx(-100)
        assert result.output_tokens_delta == pytest.approx(10)

    def test_repetitions_are_averaged_inside_their_case(self):
        a = Experiment("a", trajectories=[_trajectory("c1", (100, 0)), _trajectory("c1", (300, 0))])
        b = Experiment("b", trajectories=[_trajectory("c1", (100, 0))])

        assert compare(a, b).input_tokens_delta == pytest.approx(-100)

    def test_cost_needs_pricing(self):
        a = Experiment("a", trajectories=[_trajectory("c1", (1000, 0))])
        b = Experiment("b", trajectories=[_trajectory("c1", (3000, 0))])

        assert compare(a, b).cost_usd_delta is None
        priced = compare(a, b, pricing=PricingConfig(0.001, 0.002))
        assert priced.cost_usd_delta == pytest.approx(2.0)

    def test_no_trajectories_gives_none(self):
        a = Experiment("a")
        b = Experiment("b", trajectories=[_trajectory("c1", (1, 1))])

        result = compare(a, b, pricing=PricingConfig(1, 1))

        assert result.input_tokens_delta is None
        assert result.output_tokens_delta is None
        assert result.cost_usd_delta is None

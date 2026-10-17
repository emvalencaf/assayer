"""Tests for the agent metrics."""

import pytest

from assayer.metrics import register_agent_metrics
from assayer.models import Case, Step, Trajectory
from assayer.registries import Registry


def _evaluate(registry, name, trajectory, case):
    return registry.get(name).evaluate(trajectory, case)


class TestStepEfficiency:
    @pytest.mark.parametrize(
        ("kinds", "expected", "value"),
        [
            (["model", "tool"], 4, 1.0),  # fewer steps than expected is capped at 1
            (["model", "tool", "tool", "model"], 4, 1.0),
            (["model", "tool", "tool", "model", "tool", "tool", "model", "model"], 4, 0.5),
            (["model", "retrieval", "other", "tool"], 1, 0.5),  # only model and tool count
            ([], 2, 0.0),  # no steps taken: no answer
            ([], 0, 1.0),
        ],
    )
    def test_documented_formula(self, kinds, expected, value):
        case = Case(input="q", id="c1", expected_steps=["s"] * expected)
        trajectory = Trajectory(steps=[Step(kind=k) for k in kinds], case_id="c1")
        registry = Registry()
        register_agent_metrics(registry)

        outcome = _evaluate(registry, "step_efficiency", trajectory, case)

        assert [(s.name, s.value) for s in outcome.scores] == [("step_efficiency", value)]

    def test_missing_expected_steps_is_a_failure_not_zero(self):
        registry = Registry()
        register_agent_metrics(registry)

        outcome = _evaluate(
            registry, "step_efficiency", Trajectory(steps=[Step(kind="model")]), Case(input="q")
        )

        assert outcome.scores == []
        assert outcome.failures[0].metric == "step_efficiency"

    def test_raw_measurements_never_become_scores(self):
        registry = Registry()
        register_agent_metrics(registry)
        case = Case(input="q", expected_steps=["s"])
        trajectory = Trajectory(steps=[Step(kind="model"), Step(kind="tool")])

        outcome = _evaluate(registry, "step_efficiency", trajectory, case)

        assert {s.name for s in outcome.scores} == {"step_efficiency"}

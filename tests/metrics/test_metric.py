"""Tests for the Metric contract."""

import pytest

from assayer.metrics import Metric, register_agent_metrics
from assayer.models import Case, Step, Trajectory
from assayer.registries import Registry


def _exact_match(trajectory, case):
    return trajectory.final_output == case.expected_output


def _exact_match_metric() -> Metric:
    return Metric(
        name="exact_match",
        level="trajectory",
        requires=("expected_output",),
        fn=_exact_match,
    )


def _evaluate(registry: Registry, name: str, trajectory: Trajectory, case: Case):
    return registry.get(name).evaluate(trajectory, case)


class TestMetricContract:
    def test_missing_required_input_emits_no_score_and_a_failure(self):
        registry = Registry()
        registry.register(_exact_match_metric())
        trajectory = Trajectory(final_output="a", case_id="c1")

        outcome = _evaluate(registry, "exact_match", trajectory, Case(input="q", id="c1"))

        assert outcome.scores == []
        assert len(outcome.failures) == 1
        assert outcome.failures[0].metric == "exact_match"
        assert "expected_output" in outcome.failures[0].error

    def test_no_answer_scores_zero(self):
        registry = Registry()
        registry.register(_exact_match_metric())
        trajectory = Trajectory(final_output="", case_id="c1")
        case = Case(input="q", id="c1", expected_output="a")

        outcome = _evaluate(registry, "exact_match", trajectory, case)

        assert outcome.failures == []
        assert [(s.name, s.value) for s in outcome.scores] == [("exact_match", 0.0)]

    def test_custom_metric_runs_like_a_built_in(self):
        registry = Registry()
        register_agent_metrics(registry)
        registry.register(_exact_match_metric())
        case = Case(input="q", id="c1", expected_output="a", expected_steps=["x"])
        trajectory = Trajectory(steps=[Step(kind="model")], final_output="a", case_id="c1")

        custom = _evaluate(registry, "exact_match", trajectory, case)
        built_in = _evaluate(registry, "step_efficiency", trajectory, case)

        assert custom.scores[0].value == 1.0
        assert built_in.scores[0].value == 1.0
        assert custom.scores[0].target == built_in.scores[0].target == "trajectory"
        assert registry.list_metrics() == ["exact_match", "step_efficiency"]

    def test_metric_that_raises_becomes_a_failure(self):
        def boom(trajectory, case):
            raise RuntimeError("judge unreachable")

        metric = Metric(name="boom", level="trajectory", fn=boom)

        outcome = metric.evaluate(Trajectory(case_id="c1"), Case(input="q"))

        assert outcome.scores == []
        assert outcome.failures[0].error == "judge unreachable"

    def test_step_level_metric_scores_each_step(self):
        metric = Metric(name="no_error", level="step", fn=lambda step, case: step.error is None)
        trajectory = Trajectory(
            steps=[Step(kind="tool", id="s1"), Step(kind="tool", id="s2", error="x")]
        )

        scores = [metric.evaluate(step, Case(input="q")).scores[0] for step in trajectory.steps]

        assert [(s.target, s.target_id, s.value) for s in scores] == [
            ("step", "s1", 1.0),
            ("step", "s2", 0.0),
        ]

    def test_requires_is_checked_on_the_subject_too(self):
        metric = Metric(
            name="m", level="trajectory", requires=("final_state",), fn=lambda t, c: 1.0
        )

        outcome = metric.evaluate(Trajectory(case_id="c1"), Case(input="q"))

        assert outcome.scores == []
        assert "final_state" in outcome.failures[0].error

    def test_judge_based_metric_is_flagged(self):
        metric = Metric(name="j", level="trajectory", kind="judge", fn=lambda t, c: 1.0)

        assert metric.kind == "judge"
        assert _exact_match_metric().kind == "deterministic"

    def test_rejects_invalid_declarations(self):
        with pytest.raises(ValueError):
            Metric(name=" ", level="trajectory", fn=lambda t, c: 1.0)
        with pytest.raises(ValueError):
            Metric(name="m", level="galaxy", fn=lambda t, c: 1.0)
        with pytest.raises(ValueError):
            Metric(name="m", level="trajectory", kind="magic", fn=lambda t, c: 1.0)
        with pytest.raises(ValueError):
            Metric(name="m", level="trajectory", requires=("nope",), fn=lambda t, c: 1.0)
        with pytest.raises(TypeError):
            Metric(name="m", level="trajectory", fn="not callable")


class TestRobustness:
    def test_wrong_subject_becomes_a_failure_instead_of_raising(self):
        metric = Metric(name="m", level="step", fn=lambda step, case: 1.0)

        outcome = metric.evaluate(None, Case(input="q"))

        assert outcome.scores == []
        assert outcome.failures[0].metric == "m"

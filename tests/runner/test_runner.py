"""Tests for the Runner, through a fake target."""

import json

import pytest

from assayer.metrics.metric import Metric
from assayer.models import (
    Case,
    Dataset,
    Experiment,
    PricingConfig,
    Step,
    TokenUsage,
    Trajectory,
)
from assayer.runner import Runner


def _exact(trajectory, case):
    return trajectory.final_output == case.expected_output


EXACT = Metric(name="exact", level="trajectory", fn=_exact, requires=("expected_output",))


def _echo(value):
    return value


class TestRunTarget:
    def test_plain_value_is_wrapped_in_one_model_step(self):
        dataset = Dataset("d", [Case(input="a", id="c1", expected_output="a")])

        experiment = Runner(_echo, [EXACT]).run(dataset)

        assert isinstance(experiment, Experiment)
        (trajectory,) = experiment.trajectories
        assert [s.kind for s in trajectory.steps] == ["model"]
        assert trajectory.steps[0].input == "a"
        assert trajectory.steps[0].output == "a"
        assert trajectory.final_output == "a"
        assert trajectory.case_id == "c1"
        assert trajectory.repetition == 0

    def test_trajectory_is_kept_and_tagged_with_its_case(self):
        def target(value):
            return Trajectory(
                steps=[Step(kind="tool", name="t"), Step(kind="model")], final_output=value
            )

        dataset = Dataset("d", [Case(input="a", id="c1", expected_output="a")])

        (trajectory,) = Runner(target, [EXACT]).run(dataset).trajectories

        assert [s.kind for s in trajectory.steps] == ["tool", "model"]
        assert trajectory.case_id == "c1"

    def test_repetitions_keep_each_trajectory(self):
        dataset = Dataset("d", [Case(input="a", id="c1"), Case(input="b", id="c2")])

        experiment = Runner(_echo, [], repetitions=3).run(dataset)

        assert len(experiment.trajectories) == 6
        c1 = [t for t in experiment.trajectories if t.case_id == "c1"]
        assert sorted(t.repetition for t in c1) == [0, 1, 2]

    def test_a_shared_trajectory_is_not_overwritten_by_repetitions(self):
        shared = Trajectory(steps=[Step(kind="tool")])

        experiment = Runner(lambda value: shared, [], repetitions=3).run(
            Dataset("d", [Case(input="a")])
        )

        assert [t.repetition for t in experiment.trajectories] == [0, 1, 2]

    def test_repetitions_must_be_positive(self):
        with pytest.raises(ValueError):
            Runner(_echo, [], repetitions=0)

    def test_case_without_id_gets_its_position(self):
        experiment = Runner(_echo, []).run(Dataset("d", [Case(input="a"), Case(input="b")]))

        assert [t.case_id for t in experiment.trajectories] == ["0", "1"]

    def test_target_error_is_recorded_not_raised(self):
        def target(value):
            raise RuntimeError("boom")

        (trajectory,) = (
            Runner(target, []).run(Dataset("d", [Case(input="a", id="c1")])).trajectories
        )

        assert trajectory.steps[0].error == "RuntimeError: boom"
        assert trajectory.final_output is None

    def test_experiment_is_named_after_the_dataset(self):
        assert Runner(_echo, []).run(Dataset("my-data", [])).name == "my-data"


class TestScoring:
    def test_trajectory_scores_and_failures_land_on_the_experiment(self):
        dataset = Dataset(
            "d",
            [
                Case(input="a", id="c1", expected_output="a"),
                Case(input="b", id="c2", expected_output="x"),
            ],
        )
        boom = Metric(name="boom", level="trajectory", fn=lambda t, c: 1 / 0)

        experiment = Runner(_echo, [EXACT, boom]).run(dataset)

        assert [(s.name, s.value, s.target_id) for s in experiment.scores] == [
            ("exact", 1.0, "c1"),
            ("exact", 0.0, "c2"),
        ]
        assert [(f.metric, f.target_id) for f in experiment.failures] == [
            ("boom", "c1"),
            ("boom", "c2"),
        ]

    def test_step_metrics_score_every_step_even_without_ids(self):
        metric = Metric(name="ok", level="step", fn=lambda s, c: s.error is None)
        target = lambda v: Trajectory(steps=[Step(kind="tool"), Step(kind="tool", id="mine")])

        experiment = Runner(target, [metric]).run(Dataset("d", [Case(input="a", id="c1")]))

        assert experiment.failures == []
        assert len(experiment.scores) == 2
        assert "mine" in [s.target_id for s in experiment.scores]

    def test_experiment_metrics_run_once(self):
        metric = Metric(name="n", level="experiment", fn=lambda e, c: len(e.trajectories) / 10)

        experiment = Runner(_echo, [metric], repetitions=2).run(Dataset("d", [Case(input="a")]))

        assert [(s.name, s.value, s.target) for s in experiment.scores] == [
            ("n", 0.2, "experiment")
        ]


class TestLoading:
    def test_list_source_builds_a_dataset(self):
        source = [{"input": "a", "expected_output": "a"}]

        experiment = Runner(_echo, [EXACT]).run(source)

        assert experiment.scores[0].value == 1.0

    def test_json_source(self, tmp_path):
        path = tmp_path / "d.json"
        path.write_text(json.dumps([{"input": "a", "expected_output": "a"}]))

        experiment = Runner(_echo, [EXACT]).run(str(path))

        assert experiment.name == "d"
        assert len(experiment.trajectories) == 1

    def test_fails_only_for_fields_the_metrics_require(self):
        source = [{"input": "a"}]

        with pytest.raises(ValueError, match="expected_output"):
            Runner(_echo, [EXACT]).run(source)

        assert len(Runner(_echo, []).run(source).trajectories) == 1

    def test_input_is_always_required(self):
        with pytest.raises(ValueError, match="input"):
            Runner(_echo, []).run([{"expected_output": "a"}])

    def test_unknown_keys_are_rejected(self):
        with pytest.raises(ValueError, match="nope"):
            Runner(_echo, []).run([{"input": "a", "nope": 1}])


class TestScoreCollectedOutputs:
    def test_plain_outputs_are_scored_without_a_target(self):
        dataset = Dataset(
            "d",
            [
                Case(input="a", id="c1", expected_output="a"),
                Case(input="b", id="c2", expected_output="x"),
            ],
        )

        experiment = Runner(metrics=[EXACT]).score(dataset, ["a", "b"])

        assert [(s.name, s.value, s.target_id) for s in experiment.scores] == [
            ("exact", 1.0, "c1"),
            ("exact", 0.0, "c2"),
        ]
        assert [t.final_output for t in experiment.trajectories] == ["a", "b"]
        assert experiment.trajectories[0].steps[0].input == "a"

    def test_collected_trajectories_are_kept_and_tagged(self):
        collected = Trajectory(steps=[Step(kind="tool", name="t")], final_output="a")
        dataset = Dataset("d", [Case(input="a", id="c1", expected_output="a")])

        experiment = Runner(metrics=[EXACT]).score(dataset, [collected])

        (trajectory,) = experiment.trajectories
        assert trajectory.case_id == "c1"
        assert trajectory.steps[0].id == "c1/0/0"
        assert collected.case_id is None  # the caller's object is untouched
        assert experiment.scores[0].value == 1.0

    def test_loads_a_list_source_like_run(self):
        experiment = Runner(metrics=[EXACT]).score([{"input": "a", "expected_output": "a"}], ["a"])

        assert experiment.scores[0].value == 1.0

    def test_one_output_per_case(self):
        with pytest.raises(ValueError, match="outputs"):
            Runner(metrics=[EXACT]).score(Dataset("d", [Case(input="a")]), [])

    def test_run_needs_a_target(self):
        with pytest.raises(ValueError, match="target"):
            Runner(metrics=[]).run(Dataset("d", []))


class TestPricing:
    def test_pricing_is_kept_on_the_experiment_for_run_and_score(self):
        pricing = PricingConfig(0.001, 0.002)
        dataset = Dataset("d", [Case(input="a")])

        assert Runner(_echo, pricing=pricing).run(dataset).pricing == pricing
        assert Runner(pricing=pricing).score(dataset, ["a"]).pricing == pricing

    def test_total_usage_defaults_to_the_experiment_pricing(self):
        usage = TokenUsage(1000, 0, None)
        target = lambda v: Trajectory(steps=[Step(kind="model", usage=usage)])

        experiment = Runner(target, pricing=PricingConfig(0.001, 0)).run(
            Dataset("d", [Case(input="a")])
        )

        assert experiment.total_usage().cost_usd == pytest.approx(1.0)
        assert experiment.total_judge_usage() is None

    def test_the_target_pricing_is_never_applied_to_the_judge(self):
        experiment = Experiment(
            "e", pricing=PricingConfig(1, 1), judge_usage=TokenUsage(10, 10, None)
        )

        assert experiment.total_judge_usage().cost_usd is None


class TestCaseIds:
    def test_duplicate_case_ids_are_rejected_before_any_target_call(self):
        calls = []
        dataset = Dataset("d", [Case(input="a", id="c1"), Case(input="b", id="c1")])

        with pytest.raises(ValueError, match="c1"):
            Runner(calls.append).run(dataset)

        assert calls == []

    def test_a_position_id_cannot_collide_with_an_explicit_one(self):
        dataset = Dataset("d", [Case(input="a"), Case(input="b", id="0")])

        with pytest.raises(ValueError, match="'0'"):
            Runner(_echo).run(dataset)

    def test_score_rejects_duplicate_case_ids_too(self):
        dataset = Dataset("d", [Case(input="a", id="c1"), Case(input="b", id="c1")])

        with pytest.raises(ValueError, match="c1"):
            Runner().score(dataset, ["a", "b"])

"""Tests for the Runner, through a fake target."""

import json

import pytest

from assayer.metrics.metric import Metric
from assayer.models import Case, Dataset, Experiment, Step, Trajectory
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

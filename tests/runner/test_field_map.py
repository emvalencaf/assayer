"""Tests for per-Field measurement through the Runner's field map."""

import pytest

from assayer.metrics.metric import Metric
from assayer.models import Case, Dataset
from assayer.runner import Runner


def _exact(trajectory, case):
    return trajectory.final_output == case.expected_output


EXACT = Metric(name="exact", level="trajectory", fn=_exact, requires=("expected_output",))


def _within(trajectory, case, tolerance=0.0):
    return abs(trajectory.final_output - case.expected_output) <= tolerance


WITHIN = Metric(name="within", level="trajectory", fn=_within, requires=("expected_output",))

CASE = Case(
    input="x",
    id="c1",
    expected_output={"label": "spam", "meta": {"score": 10, "tags": ["a", "b"]}},
)


def _target(_):
    return {"label": "spam", "meta": {"score": 12, "tags": ["a", "z"]}}


class TestFieldMap:
    def test_each_field_is_scored_on_its_own_and_carries_its_field(self):
        runner = Runner(_target, field_metrics={"label": [EXACT], "meta.score": [EXACT]})

        experiment = runner.run(Dataset("d", [CASE]))

        by_field = {s.field: s.value for s in experiment.scores}
        assert by_field == {"label": 1.0, "meta.score": 0.0}
        assert {s.name for s in experiment.scores} == {"exact"}
        assert all(s.target_id == "c1" for s in experiment.scores)

    def test_scores_are_grouped_per_field_on_the_experiment(self):
        runner = Runner(_target, [EXACT], field_metrics={"label": [EXACT]})

        experiment = runner.run(Dataset("d", [CASE]))

        grouped = experiment.scores_by_field()
        assert set(grouped) == {None, "label"}
        assert [s.value for s in grouped["label"]] == [1.0]
        assert [s.value for s in grouped[None]] == [0.0]

    def test_nested_and_indexed_paths_are_addressable(self):
        runner = Runner(_target, field_metrics={"meta.tags.0": [EXACT], "meta.tags.1": [EXACT]})

        experiment = runner.run(Dataset("d", [CASE]))

        assert {s.field: s.value for s in experiment.scores} == {
            "meta.tags.0": 1.0,
            "meta.tags.1": 0.0,
        }

    def test_per_pair_parameters_are_honoured(self):
        runner = Runner(
            _target,
            field_metrics={
                "meta.score": [(WITHIN, {"tolerance": 5})],
                "label": [],
            },
        )
        loose = runner.run(Dataset("d", [CASE]))
        strict = Runner(_target, field_metrics={"meta.score": [(WITHIN, {"tolerance": 1})]}).run(
            Dataset("d", [CASE])
        )

        assert loose.scores[0].value == 1.0
        assert strict.scores[0].value == 0.0

    def test_a_metric_without_a_field_scores_the_whole_output(self):
        runner = Runner(_target, [EXACT])

        experiment = runner.run(Dataset("d", [CASE]))

        (score,) = experiment.scores
        assert score.field is None
        assert score.value == 0.0

    def test_a_field_missing_from_the_expected_output_is_an_evaluation_failure(self):
        runner = Runner(_target, field_metrics={"meta.absent": [EXACT]})

        experiment = runner.run(Dataset("d", [CASE]))

        assert experiment.scores == []
        (failure,) = experiment.failures
        assert failure.field == "meta.absent"
        assert "expected_output" in failure.error

    def test_a_field_missing_from_the_prediction_reaches_the_metric_as_none(self):
        seen = []

        def spy(trajectory, case):
            seen.append(trajectory.final_output)
            return 0.0

        metric = Metric(name="spy", level="trajectory", fn=spy)
        Runner(_target, field_metrics={"meta.absent": [metric]}).run(Dataset("d", [CASE]))

        assert seen == [None]

    def test_field_metrics_work_on_scored_outputs(self):
        runner = Runner(field_metrics={"label": [EXACT]})

        experiment = runner.score(Dataset("d", [CASE]), [_target("x")])

        assert [(s.field, s.value) for s in experiment.scores] == [("label", 1.0)]

    def test_loaded_cases_are_validated_against_the_field_metrics_requires(self):
        runner = Runner(_target, field_metrics={"label": [EXACT]})

        with pytest.raises(ValueError, match="expected_output"):
            runner.run([{"input": "x"}])


class TestInvalidFieldMap:
    @pytest.mark.parametrize("path", ["", " ", "a..b", ".a", "a.", 3])
    def test_a_malformed_path_is_rejected(self, path):
        with pytest.raises(ValueError, match="field"):
            Runner(_target, field_metrics={path: [EXACT]})

    def test_a_non_metric_entry_is_rejected(self):
        with pytest.raises(TypeError, match="Metric"):
            Runner(_target, field_metrics={"a": ["exact"]})

    def test_malformed_parameters_are_rejected(self):
        with pytest.raises(TypeError, match="parameters"):
            Runner(_target, field_metrics={"a": [(EXACT, "tolerance")]})

    def test_a_metric_that_is_not_trajectory_level_is_rejected(self):
        step_metric = Metric(name="s", level="step", fn=lambda s, c: 1.0)
        with pytest.raises(ValueError, match="trajectory"):
            Runner(_target, field_metrics={"a": [step_metric]})

    def test_a_bare_list_instead_of_a_map_is_rejected(self):
        with pytest.raises(TypeError, match="mapping"):
            Runner(_target, field_metrics=[EXACT])

    def test_the_target_is_never_called_when_the_map_is_invalid(self):
        calls = []

        def target(value):
            calls.append(value)
            return value

        with pytest.raises(ValueError):
            Runner(target, field_metrics={"a..b": [EXACT]}).run(Dataset("d", [CASE]))

        assert calls == []

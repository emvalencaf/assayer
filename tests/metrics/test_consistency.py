"""Tests for the consistency metrics: an Experiment with repetitions, grouped by Case."""

import math
import statistics

import pytest

from assayer.evaluators import consistency_metrics as legacy
from assayer.metrics import Metric, make_score_std, register_consistency_metrics
from assayer.models import Case, Dataset, FieldEvaluation
from assayer.registries import Registry
from assayer.runner import Runner


def _registry():
    registry = Registry()
    register_consistency_metrics(registry)
    return registry


def _target(runs):
    """A target answering `runs[input]` one repetition at a time."""
    queues = {key: iter(values) for key, values in runs.items()}
    return lambda value: next(queues[value])


def _exact(trajectory, case):
    return trajectory.final_output == case.expected_output


EXACT = Metric(name="exact", level="trajectory", fn=_exact, requires=("expected_output",))


def _legacy(values, scores=None):
    scores = scores or [0.0] * len(values)
    return [FieldEvaluation("f", "m", None, v, s, None) for v, s in zip(values, scores)]


RUNS = {
    "a": ["x", "x", "y", "x"],
    "b": ["p", "q", "r", "s"],
    "c": ["z", "z", "z", "z"],
}
REFERENCES = {"a": "x", "b": "q", "c": "w"}
DATASET = Dataset("d", [Case(input=k, id=k, expected_output=REFERENCES[k]) for k in RUNS])


def _run(*metrics, field_metrics=None):
    return Runner(_target(RUNS), list(metrics), repetitions=4, field_metrics=field_metrics).run(
        DATASET
    )


def _value(experiment, name, field=None):
    (score,) = [s for s in experiment.scores if s.name == name and s.field == field]
    assert (score.target, score.target_id) == ("experiment", None)
    return score.value


class TestGroupedByCase:
    def test_agreement_rate_is_the_mean_over_cases_of_the_dominant_share(self):
        experiment = _run(_registry().get("agreement_rate"))

        expected = statistics.mean(
            legacy.compute_agreement_rate(_legacy(v))[0] for v in RUNS.values()
        )
        assert _value(experiment, "agreement_rate") == pytest.approx(expected)
        assert expected == pytest.approx((0.75 + 0.25 + 1.0) / 3)

    def test_entropy_is_in_bits_scaled_by_the_most_the_repetitions_allow(self):
        experiment = _run(_registry().get("entropy"))

        bits = [legacy.compute_entropy(_legacy(v)) for v in RUNS.values()]
        assert bits[1] == pytest.approx(math.log2(4))  # four distinct answers
        assert _value(experiment, "entropy") == pytest.approx(statistics.mean(b / 2 for b in bits))

    @pytest.mark.parametrize(
        ("name", "legacy_fn"),
        [
            ("correct_rate", legacy.compute_correct_rate),
            ("pass_at_k", legacy.compute_pass_at_k),
            ("recall_at_k", legacy.compute_recall_at_k),
        ],
    )
    def test_reference_metrics_match_the_legacy_functions(self, name, legacy_fn):
        experiment = _run(_registry().get(name))

        expected = statistics.mean(float(legacy_fn(_legacy(RUNS[k]), REFERENCES[k])) for k in RUNS)
        assert _value(experiment, name) == pytest.approx(expected)
        assert 0 < expected < 1

    def test_multi_label_outputs_are_compared_as_sets(self):
        runs = {"a": [["x"], ["y"]], "b": [["x", "y"], ["y", "x"]]}
        refs = {"a": ["x", "y", "z"], "b": ["y", "x"]}
        dataset = Dataset("d", [Case(input=k, id=k, expected_output=refs[k]) for k in runs])
        registry = _registry()
        names = ["correct_rate", "pass_at_k", "recall_at_k"]

        experiment = Runner(_target(runs), [registry.get(n) for n in names], repetitions=2).run(
            dataset
        )

        legacy_fns = [
            legacy.compute_correct_rate,
            legacy.compute_pass_at_k,
            legacy.compute_recall_at_k,
        ]
        for name, fn in zip(names, legacy_fns):
            expected = statistics.mean(float(fn(_legacy(runs[k]), refs[k])) for k in runs)
            assert _value(experiment, name) == pytest.approx(expected)

    def test_score_std_is_the_spread_of_the_scores_of_a_metric_over_the_repetitions(self):
        experiment = _run(EXACT, make_score_std("exact"))

        per_case = {k: [float(v == REFERENCES[k]) for v in RUNS[k]] for k in RUNS}
        expected = statistics.mean(
            legacy.compute_score_std(_legacy(RUNS[k], per_case[k])) for k in RUNS
        )
        assert _value(experiment, "score_std") == pytest.approx(expected)
        assert expected > 0

    def test_score_std_without_scores_to_take_the_spread_of_is_a_failure(self):
        experiment = _run(make_score_std("exact"))

        assert [s for s in experiment.scores if s.name == "score_std"] == []
        assert [f.metric for f in experiment.failures] == ["score_std"]

    def test_score_std_names_its_metric_when_there_are_several(self):
        other = Metric(name="other", level="trajectory", fn=lambda t, c: 1.0)

        experiment = _run(EXACT, other, _registry().get("score_std"))

        assert [f.metric for f in experiment.failures] == ["score_std"]
        assert "exact" in experiment.failures[0].error

    def test_a_single_repetition_has_no_disagreement(self):
        names = ["agreement_rate", "entropy"]
        registry = _registry()

        experiment = Runner(_target({"a": ["x"]}), [registry.get(n) for n in names]).run(
            Dataset("d", [Case(input="a", id="a")])
        )

        assert {s.name: s.value for s in experiment.scores} == {
            "agreement_rate": 1.0,
            "entropy": 0.0,
        }

    def test_reference_metrics_need_a_reference_on_every_case(self):
        experiment = Runner(
            _target({"a": ["x", "x"]}), [_registry().get("pass_at_k")], repetitions=2
        ).run(Dataset("d", [Case(input="a", id="a")]))

        assert experiment.scores == []
        assert [f.metric for f in experiment.failures] == ["pass_at_k"]


class TestPerField:
    def test_consistency_of_one_field_ignores_the_others(self):
        runs = {
            "a": [{"label": "x", "note": n} for n in "pqrs"],
            "b": [{"label": v, "note": "same"} for v in "xxxy"],
        }
        dataset = Dataset(
            "d",
            [Case(input=k, id=k, expected_output={"label": "x", "note": "same"}) for k in runs],
        )
        registry = _registry()
        agreement = registry.get("agreement_rate")

        experiment = Runner(
            _target(runs),
            [agreement],
            repetitions=4,
            field_metrics={"label": [agreement], "note": [agreement]},
        ).run(dataset)

        assert _value(experiment, "agreement_rate", "label") == pytest.approx((1.0 + 0.75) / 2)
        assert _value(experiment, "agreement_rate", "note") == pytest.approx((0.25 + 1.0) / 2)

    def test_score_std_of_a_field_uses_the_scores_of_that_field(self):
        runs = {"a": [{"label": v} for v in "xxyx"]}
        dataset = Dataset("d", [Case(input="a", id="a", expected_output={"label": "x"})])

        experiment = Runner(
            _target(runs),
            repetitions=4,
            field_metrics={"label": [EXACT, make_score_std("exact")]},
        ).run(dataset)

        assert _value(experiment, "score_std", "label") == pytest.approx(
            legacy.compute_score_std(_legacy("xxyx", [1.0, 1.0, 0.0, 1.0]))
        )

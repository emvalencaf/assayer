"""Tests for the corpus metrics, run as Experiment-level metrics through the Runner."""

import pytest

from assayer.evaluators.ner import EntitySpan
from assayer.metrics import (
    accuracy,
    bleu,
    make_f1,
    make_precision,
    make_recall,
    ner_macro_f1,
    register_corpus_metrics,
    rouge_l,
)
from assayer.models import Case, Dataset
from assayer.registries import Registry
from assayer.runner import ListField, Runner


def _registry():
    registry = Registry()
    register_corpus_metrics(registry)
    return registry


def _dataset(pairs):
    return Dataset(
        "d", [Case(input=i, id=f"c{n}", expected_output=e) for n, (i, e) in enumerate(pairs)]
    )


class TestExperimentLevel:
    def test_the_whole_corpus_gets_one_experiment_level_score(self):
        dataset = _dataset([("a", "cat"), ("b", "dog"), ("c", "cat")])
        answers = {"a": "cat", "b": "cat", "c": "cat"}

        experiment = Runner(answers.get, [_registry().get("accuracy")]).run(dataset)

        (score,) = experiment.scores
        assert (score.name, score.target, score.target_id, score.field) == (
            "accuracy",
            "experiment",
            None,
            None,
        )
        assert score.value == pytest.approx(2 / 3)
        assert experiment.failures == []

    def test_a_case_without_reference_is_a_failure_not_a_score(self):
        dataset = Dataset("d", [Case(input="a", id="c0", expected_output="x"), Case(input="b")])

        experiment = Runner(str, [_registry().get("accuracy")]).run(dataset)

        assert experiment.scores == []
        assert [f.metric for f in experiment.failures] == ["accuracy"]


class TestParity:
    """The same inputs score the same as the legacy corpus functions."""

    def test_text_metrics_match_the_legacy_functions(self):
        pairs = [
            ("a", "the cat sat on the mat"),
            ("b", "a quick brown fox jumps"),
            ("c", "hello world again and again"),
        ]
        answers = {
            "a": "the cat sat on a mat",
            "b": "a quick brown dog jumps",
            "c": "hello world",
        }
        registry = _registry()
        names = ["bleu", "rouge_l"]

        experiment = Runner(answers.get, [registry.get(n) for n in names]).run(_dataset(pairs))

        predictions = [answers[i] for i, _ in pairs]
        references = [e for _, e in pairs]
        assert {s.name: s.value for s in experiment.scores} == {
            "bleu": bleu(predictions, references),
            "rouge_l": rouge_l(predictions, references),
        }

    def test_classification_metrics_match_the_legacy_functions(self):
        pairs = [("a", "x"), ("b", "y"), ("c", "z"), ("d", "x")]
        answers = {"a": "x", "b": "y", "c": "x", "d": "z"}
        registry = _registry()
        names = ["accuracy", "precision", "recall", "f1"]

        experiment = Runner(answers.get, [registry.get(n) for n in names]).run(_dataset(pairs))

        predictions = [answers[i] for i, _ in pairs]
        references = [e for _, e in pairs]
        assert {s.name: s.value for s in experiment.scores} == {
            "accuracy": accuracy(predictions, references),
            "precision": make_precision()(predictions, references),
            "recall": make_recall()(predictions, references),
            "f1": make_f1()(predictions, references),
        }

    def test_ner_matches_the_legacy_function(self):
        john = EntitySpan("John", "PERSON", 0, 4)
        paris = EntitySpan("Paris", "LOC", 10, 15)
        pairs = [("a", [john, paris]), ("b", [john])]
        answers = {"a": [john], "b": [john, paris]}

        experiment = Runner(answers.get, [_registry().get("ner_macro_f1")]).run(_dataset(pairs))

        (score,) = experiment.scores
        assert score.value == ner_macro_f1([answers[i] for i, _ in pairs], [e for _, e in pairs])
        assert 0 < score.value < 1


class TestPerField:
    def test_a_corpus_metric_runs_on_a_field_alone(self):
        dataset = _dataset(
            [
                ("a", {"label": "x", "note": "foo"}),
                ("b", {"label": "y", "note": "bar"}),
                ("c", {"label": "x", "note": "baz"}),
            ]
        )
        answers = {
            "a": {"label": "x", "note": "?"},
            "b": {"label": "x", "note": "?"},
            "c": {"label": "x", "note": "?"},
        }
        acc = _registry().get("accuracy")

        experiment = Runner(answers.get, field_metrics={"label": [acc]}).run(dataset)

        by_field = {s.field: s.value for s in experiment.scores}
        assert by_field == {"label": pytest.approx(2 / 3)}
        field_score = next(s for s in experiment.scores if s.field == "label")
        assert (field_score.target, field_score.target_id) == ("experiment", None)

    def test_a_case_lacking_the_field_is_a_failure_on_that_field(self):
        dataset = _dataset([("a", {"label": "x"}), ("b", {})])
        acc = _registry().get("accuracy")

        experiment = Runner(lambda i: {"label": "x"}, field_metrics={"label": [acc]}).run(dataset)

        assert experiment.scores == []
        assert [(f.metric, f.field) for f in experiment.failures] == [("accuracy", "label")]

    def test_a_corpus_metric_cannot_score_the_properties_of_list_items(self):
        acc = _registry().get("accuracy")

        with pytest.raises(ValueError, match="trajectory-level"):
            Runner(
                lambda i: {},
                field_metrics={"items": ListField(properties={"label": [acc]}, align="positional")},
            )

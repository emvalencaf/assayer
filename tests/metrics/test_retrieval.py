"""Tests for context precision and recall, through the Runner over retrieval Steps."""

import pytest

from assayer.metrics import (
    make_context_precision,
    make_context_recall,
    register_retrieval_metrics,
)
from assayer.models import Case, Dataset, Step, Trajectory
from assayer.registries import Registry
from assayer.runner import Runner


def _run(metric, retrieved, **case):
    target = lambda q: Trajectory(
        steps=[Step(kind="retrieval", output=retrieved)], final_output="a"
    )
    return Runner(target, [metric]).run(Dataset("d", [Case(input="q", id="c1", **case)]))


def _value(experiment):
    (score,) = experiment.scores
    assert experiment.failures == []
    return score.value


def _items(*ids):
    return [{"id": i, "text": f"text {i}"} for i in ids]


class TestById:
    def test_precision_rewards_relevant_items_ranked_first(self):
        metric = make_context_precision("id")

        first = _value(_run(metric, _items("a", "x", "b"), reference_context_ids=["a", "b"]))
        last = _value(_run(metric, _items("x", "a", "b"), reference_context_ids=["a", "b"]))

        assert first == pytest.approx((1 / 1 + 2 / 3) / 2)
        assert last == pytest.approx((1 / 2 + 2 / 3) / 2)
        assert first > last

    def test_precision_is_zero_when_nothing_relevant_is_retrieved(self):
        experiment = _run(make_context_precision("id"), _items("x"), reference_context_ids=["a"])

        assert _value(experiment) == 0.0

    def test_recall_is_the_share_of_reference_ids_retrieved(self):
        experiment = _run(
            make_context_recall("id"), _items("a", "x"), reference_context_ids=["a", "b"]
        )

        assert _value(experiment) == 0.5

    def test_an_item_without_an_id_is_a_failure(self):
        experiment = _run(make_context_recall("id"), ["plain text"], reference_context_ids=["a"])

        assert experiment.scores == []
        assert [f.metric for f in experiment.failures] == ["context_recall"]


class TestByString:
    def test_matching_ignores_case_and_whitespace_and_works_either_way(self):
        retrieved = ["Paris   is the CAPITAL of France.", "Berlin", "capital"]
        references = ["paris is the capital", "Madrid"]

        precision = _value(
            _run(make_context_precision("string"), retrieved, reference_contexts=references)
        )
        recall = _value(
            _run(make_context_recall("string"), retrieved, reference_contexts=references)
        )

        assert precision == pytest.approx((1 / 1 + 2 / 3) / 2)  # items 1 and 3 hold a reference
        assert recall == 0.5

    def test_items_may_be_mappings_with_text_or_content(self):
        retrieved = [{"content": "the moon"}, {"text": "the sun"}]

        experiment = _run(make_context_recall("string"), retrieved, reference_contexts=["the sun"])

        assert _value(experiment) == 1.0

    def test_steps_are_read_as_one_ranking(self):
        target = lambda q: Trajectory(
            steps=[
                Step(kind="retrieval", output=["x"]),
                Step(kind="tool", output="ignored"),
                Step(kind="retrieval", output="needle"),
            ]
        )
        metric = make_context_precision("string")

        experiment = Runner(target, [metric]).run(
            Dataset("d", [Case(input="q", id="c1", reference_contexts=["needle"])])
        )

        assert _value(experiment) == pytest.approx(1 / 2)


class TestMissingInputs:
    @pytest.mark.parametrize("factory", [make_context_precision, make_context_recall])
    @pytest.mark.parametrize(
        ("mode", "case"),
        [
            ("id", {"reference_contexts": ["x"]}),
            ("string", {"reference_context_ids": ["x"]}),
            ("id", {"reference_context_ids": []}),
        ],
    )
    def test_a_missing_or_empty_reference_is_a_failure_not_a_zero(self, factory, mode, case):
        experiment = _run(factory(mode), _items("a"), **case)

        assert experiment.scores == []
        assert len(experiment.failures) == 1

    def test_a_trajectory_without_a_retrieval_step_is_a_failure(self):
        metric = make_context_recall("id")
        target = lambda q: Trajectory(final_output="a")

        experiment = Runner(target, [metric]).run(
            Dataset("d", [Case(input="q", id="c1", reference_context_ids=["a"])])
        )

        assert experiment.scores == []
        assert "retrieval" in experiment.failures[0].error

    def test_a_retrieval_that_returned_nothing_scores_zero(self):
        experiment = _run(make_context_recall("id"), [], reference_context_ids=["a"])

        assert _value(experiment) == 0.0

    def test_an_unknown_match_mode_is_rejected(self):
        with pytest.raises(ValueError):
            make_context_precision("fuzzy")


def test_register_retrieval_metrics_adds_both_variants_of_both_metrics():
    registry = Registry()

    register_retrieval_metrics(registry)

    for name in ("context_precision", "context_recall"):
        for mode in ("id", "string"):
            assert registry.get(f"{name}_{mode}").level == "trajectory"

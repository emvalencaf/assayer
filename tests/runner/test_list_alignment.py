"""Tests for the Alignment of list Fields through the Runner's field map."""

import pytest

from assayer.metrics import Metric
from assayer.models import Case, Dataset
from assayer.runner import ListField, Runner


def _exact(trajectory, case):
    return trajectory.final_output == case.expected_output


EXACT = Metric(name="exact", level="trajectory", fn=_exact, requires=("expected_output",))


def _score(expected, predicted, **list_field):
    list_field.setdefault("properties", {"name": [EXACT], "qty": [EXACT]})
    runner = Runner(field_metrics={"items": ListField(**list_field)})
    case = Case(input="x", id="c1", expected_output={"items": expected})
    experiment = runner.score(Dataset("d", [case]), [{"items": predicted}])
    return experiment


def _by_name(experiment):
    return {(s.field, s.name): s for s in experiment.scores}


class TestBestMatch:
    def test_items_are_paired_by_similarity_and_scored_property_by_property(self):
        expected = [{"name": "a", "qty": 1}, {"name": "b", "qty": 2}]
        predicted = [{"name": "b", "qty": 9}, {"name": "a", "qty": 1}]

        scores = _by_name(_score(expected, predicted))

        assert scores["items.name", "exact"].value == 1.0
        assert scores["items.qty", "exact"].value == 0.5
        assert scores["items", "list_precision"].value == 1.0
        assert scores["items", "list_recall"].value == 1.0
        assert scores["items", "list_f1"].value == 1.0
        assert scores["items", "list_f1"].metadata["alignment"] == {
            "pairs": [[0, 1], [1, 0]],
            "unmatched_expected": [],
            "unmatched_predicted": [],
        }

    def test_pairs_below_the_threshold_stay_unmatched(self):
        expected = [{"name": "a", "qty": 1}]
        predicted = [{"name": "z", "qty": 9}, {"name": "a", "qty": 1}]

        scores = _by_name(_score(expected, predicted))

        assert scores["items", "list_precision"].value == 0.5
        assert scores["items", "list_recall"].value == 1.0
        assert scores["items", "list_f1"].value == pytest.approx(2 / 3)
        assert scores["items", "list_f1"].metadata["alignment"]["unmatched_predicted"] == [0]

    def test_ties_go_to_the_earlier_position(self):
        expected = [{"name": "a", "qty": 1}]
        predicted = [{"name": "a", "qty": 1}, {"name": "a", "qty": 1}]

        scores = _by_name(_score(expected, predicted))

        assert scores["items", "list_f1"].metadata["alignment"]["pairs"] == [[0, 0]]

    def test_a_custom_threshold_is_honoured(self):
        expected = [{"name": "a", "qty": 1}]
        predicted = [{"name": "a", "qty": 9}]

        loose = _by_name(_score(expected, predicted))
        strict = _by_name(_score(expected, predicted, threshold=0.9))

        assert loose["items", "list_recall"].value == 1.0
        assert strict["items", "list_recall"].value == 0.0
        assert ("items.name", "exact") not in strict


class TestOtherStrategies:
    def test_key_pairs_items_with_the_same_key(self):
        expected = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}]
        predicted = [{"id": 2, "name": "x"}, {"id": 1, "name": "a"}]

        scores = _by_name(
            _score(expected, predicted, align="key", key="id", properties={"name": [EXACT]})
        )

        assert scores["items.name", "exact"].value == 0.5
        assert scores["items", "list_f1"].metadata["alignment"]["pairs"] == [[0, 1], [1, 0]]

    def test_positional_pairs_by_index_whatever_the_similarity(self):
        expected = [{"name": "a", "qty": 1}, {"name": "b", "qty": 2}]
        predicted = [{"name": "b", "qty": 2}, {"name": "a", "qty": 1}]

        scores = _by_name(_score(expected, predicted, align="positional"))

        assert scores["items.name", "exact"].value == 0.0
        assert scores["items", "list_f1"].value == 1.0


class TestEdgeCases:
    @pytest.mark.parametrize(
        ("expected", "predicted", "precision", "recall", "f1"),
        [
            ([], [], 1.0, 1.0, 1.0),
            ([], [{"name": "a", "qty": 1}], 0.0, 1.0, 0.0),
            ([{"name": "a", "qty": 1}], [], 1.0, 0.0, 0.0),
            ([{"name": "a", "qty": 1}], None, 1.0, 0.0, 0.0),
        ],
    )
    def test_empty_lists(self, expected, predicted, precision, recall, f1):
        scores = _by_name(_score(expected, predicted))

        assert scores["items", "list_precision"].value == precision
        assert scores["items", "list_recall"].value == recall
        assert scores["items", "list_f1"].value == f1
        assert not any(field == "items.name" for field, _ in scores)

    def test_an_expected_value_that_is_not_a_list_is_an_evaluation_failure(self):
        experiment = _score("nope", [])

        assert experiment.scores == []
        (failure,) = experiment.failures
        assert failure.field == "items"


class TestNestedLists:
    def test_nested_arrays_align_recursively_without_extra_options(self):
        inner = ListField(properties={"v": [EXACT]})
        expected = [{"name": "a", "tags": [{"v": 1}, {"v": 2}]}]
        predicted = [{"name": "a", "tags": [{"v": 2}]}]

        scores = _by_name(_score(expected, predicted, properties={"name": [EXACT], "tags": inner}))

        assert scores["items.tags.v", "exact"].value == 1.0
        assert scores["items.tags", "list_recall"].value == 0.5
        assert scores["items.tags", "list_precision"].value == 1.0
        assert scores["items", "list_f1"].value == 1.0


class TestInvalidListField:
    def test_key_alignment_needs_a_key(self):
        with pytest.raises(ValueError, match="key"):
            Runner(field_metrics={"a": ListField({"n": [EXACT]}, align="key")})

    def test_unknown_alignment_is_rejected(self):
        with pytest.raises(ValueError, match="align"):
            Runner(field_metrics={"a": ListField({"n": [EXACT]}, align="magic")})

    def test_best_match_needs_a_property_to_compare(self):
        with pytest.raises(ValueError, match="propert"):
            Runner(field_metrics={"a": ListField({})})

    def test_threshold_must_be_a_fraction(self):
        with pytest.raises(ValueError, match="threshold"):
            Runner(field_metrics={"a": ListField({"n": [EXACT]}, threshold=1.5)})

    def test_property_metrics_are_validated_like_field_metrics(self):
        with pytest.raises(TypeError, match="Metric"):
            Runner(field_metrics={"a": ListField({"n": ["exact"]})})

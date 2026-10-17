"""Tests for the field-level metrics, scored through the Runner's field map."""

import pytest

from assayer.metrics import register_field_metrics
from assayer.models import Case, Dataset
from assayer.registries import Registry
from assayer.runner import Runner


def _score(metric_name, expected, predicted, params=None):
    registry = Registry()
    register_field_metrics(registry)
    metric = registry.get(metric_name)
    entry = (metric, params) if params else metric
    runner = Runner(field_metrics={"v": [entry]})
    case = Case(input="x", id="c1", expected_output={"v": expected})
    experiment = runner.score(Dataset("d", [case]), [{"v": predicted}])
    return experiment.scores[0].value


@pytest.mark.parametrize(
    ("expected", "predicted", "value"),
    [("a", "a", 1.0), ("a", "b", 0.0), (True, True, 1.0), (1, True, 1.0), ("a", None, 0.0)],
)
def test_exact_match(expected, predicted, value):
    assert _score("exact_match", expected, predicted) == value


@pytest.mark.parametrize(
    ("expected", "predicted", "value"),
    [("New  York", " new york ", 1.0), ("Paris", "paris!", 0.0), (3, 3, 1.0), ("a", None, 0.0)],
)
def test_normalized_exact_match(expected, predicted, value):
    assert _score("normalized_exact_match", expected, predicted) == value


@pytest.mark.parametrize(
    ("expected", "predicted", "params", "value"),
    [
        (10, 10, None, 1.0),
        (10, 11, None, 0.0),
        (10, 11, {"tolerance": 1}, 1.0),
        (10, 12.5, {"tolerance": 1}, 0.0),
        (10, "10", None, 0.0),
        (10, None, None, 0.0),
    ],
)
def test_numeric_tolerance(expected, predicted, params, value):
    assert _score("numeric_tolerance", expected, predicted, params) == value


@pytest.mark.parametrize(
    ("expected", "predicted", "value"),
    [
        (["a", "b"], ["b", "a"], 1.0),
        ([], [], 1.0),
        (["a", "b"], ["a", "c"], 0.5),
        (["a", "a"], ["a"], pytest.approx(2 / 3)),
        (["a"], [], 0.0),
        (["a"], "a", 0.0),
        ([{"x": 1}], [{"x": 1}], 1.0),
    ],
)
def test_list_f1_ignores_order_and_counts_repeats(expected, predicted, value):
    assert _score("list_f1", expected, predicted) == value

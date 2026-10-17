"""Tests for the Registry of Metric objects."""

import pytest

from assayer.metrics import Metric
from assayer.models import Case, Dataset
from assayer.registries import Registry
from assayer.runner import Runner


def _exact_match_metric() -> Metric:
    return Metric(name="exact_match", level="trajectory", fn=lambda t, c: 1.0)


class TestRegistry:
    def test_duplicate_and_unknown_names(self):
        registry = Registry()
        registry.register(_exact_match_metric())

        with pytest.raises(KeyError):
            registry.register(_exact_match_metric())
        with pytest.raises(KeyError):
            registry.get("missing")

    def test_instances_do_not_share_state(self):
        first, second = Registry(), Registry()
        first.register(_exact_match_metric())

        assert second.list_metrics() == []

    def test_a_custom_metric_registered_by_name_runs_like_a_built_in(self):
        registry = Registry()
        registry.register(
            Metric(
                name="shout",
                level="trajectory",
                fn=lambda t, c: float(t.final_output == c.expected_output.upper()),
                requires=("expected_output",),
            )
        )
        dataset = Dataset("d", [Case(input="a", id="c1", expected_output="HI")])

        experiment = Runner(lambda _: "HI", [registry.get("shout")]).run(dataset)

        assert [(s.name, s.value) for s in experiment.scores] == [("shout", 1.0)]

    def test_listing_is_sorted(self):
        registry = Registry()
        for name in ("b", "a"):
            registry.register(Metric(name=name, level="trajectory", fn=lambda t, c: 1.0))

        assert registry.list_metrics() == ["a", "b"]

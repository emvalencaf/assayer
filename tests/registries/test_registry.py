"""Tests for the Registry of Metric objects."""

import pytest

from assayer.metrics import Metric
from assayer.registries import Registry


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

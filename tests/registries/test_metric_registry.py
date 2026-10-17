"""Tests for MetricRegistry class.

This module tests the MetricRegistry implementation according to the spec
requirements: registration, retrieval, validation, and state isolation.
"""

from typing import Any

import pytest

from assayer.registries.metric_registry import MetricRegistry


def dummy_metric(predictions: list[Any], references: list[Any]) -> float:
    """A simple dummy metric function for testing."""
    return 0.5


def another_metric(predictions: list[Any], references: list[Any]) -> float:
    """Another dummy metric function for testing."""
    return 0.8


class TestMetricRegistryRegistration:
    """Test MetricRegistry.register() functionality."""

    def test_register_and_get_returns_same_function(self):
        """AC-SPEC-005: register(name, fn) stores fn; get(name) returns the same fn."""
        registry = MetricRegistry()

        registry.register("accuracy", dummy_metric)
        retrieved_fn = registry.get("accuracy")

        assert retrieved_fn is dummy_metric
        assert retrieved_fn([], []) == 0.5

    def test_register_multiple_functions(self):
        """Test registering multiple different functions."""
        registry = MetricRegistry()

        registry.register("accuracy", dummy_metric)
        registry.register("f1", another_metric)

        assert registry.get("accuracy") is dummy_metric
        assert registry.get("f1") is another_metric

    def test_register_empty_name_raises_value_error(self):
        """AC-SPEC-006: register raises ValueError for empty name."""
        registry = MetricRegistry()

        with pytest.raises(ValueError):
            registry.register("", dummy_metric)

    def test_register_whitespace_only_name_raises_value_error(self):
        """AC-SPEC-006: register raises ValueError for whitespace-only name."""
        registry = MetricRegistry()

        with pytest.raises(ValueError):
            registry.register("   ", dummy_metric)

        with pytest.raises(ValueError):
            registry.register("\t\n ", dummy_metric)

    def test_register_non_callable_raises_type_error(self):
        """AC-SPEC-006: register raises TypeError for non-callable fn."""
        registry = MetricRegistry()

        with pytest.raises(TypeError):
            registry.register("accuracy", "not_callable")

        with pytest.raises(TypeError):
            registry.register("f1", 42)

        with pytest.raises(TypeError):
            registry.register("precision", {"not": "callable"})

    def test_register_none_raises_type_error(self):
        """Edge case: register None as fn raises TypeError."""
        registry = MetricRegistry()

        with pytest.raises(TypeError):
            registry.register("accuracy", None)

    def test_register_duplicate_name_raises_key_error(self):
        """AC-SPEC-006: register raises KeyError for duplicate name."""
        registry = MetricRegistry()

        registry.register("accuracy", dummy_metric)

        with pytest.raises(KeyError):
            registry.register("accuracy", another_metric)


class TestMetricRegistryRetrieval:
    """Test MetricRegistry.get() functionality."""

    def test_get_unregistered_name_raises_key_error(self):
        """AC-SPEC-007: get raises KeyError for unregistered name."""
        registry = MetricRegistry()

        with pytest.raises(KeyError):
            registry.get("nonexistent")

    def test_get_after_register_works(self):
        """Test normal get after registration."""
        registry = MetricRegistry()

        registry.register("accuracy", dummy_metric)
        result = registry.get("accuracy")

        assert result is dummy_metric


class TestMetricRegistryListing:
    """Test MetricRegistry.list_metrics() functionality."""

    def test_list_metrics_empty_registry_returns_empty_list(self):
        """Edge case: list_metrics() on empty registry returns []."""
        registry = MetricRegistry()

        result = registry.list_metrics()

        assert result == []

    def test_list_metrics_returns_sorted_list(self):
        """AC-SPEC-008: list_metrics() returns sorted list."""
        registry = MetricRegistry()

        # Register in non-alphabetical order
        registry.register("z_metric", dummy_metric)
        registry.register("accuracy", another_metric)
        registry.register("f1", dummy_metric)

        result = registry.list_metrics()

        assert result == ["accuracy", "f1", "z_metric"]

    def test_list_metrics_single_item(self):
        """Test list_metrics with single registered metric."""
        registry = MetricRegistry()

        registry.register("accuracy", dummy_metric)
        result = registry.list_metrics()

        assert result == ["accuracy"]


class TestMetricRegistryStateIsolation:
    """Test that MetricRegistry instances don't share state."""

    def test_independent_registries_do_not_share_state(self):
        """AC-SPEC-013: Two independent MetricRegistry instances do not share state."""
        registry1 = MetricRegistry()
        registry2 = MetricRegistry()

        registry1.register("accuracy", dummy_metric)
        registry2.register("f1", another_metric)

        # registry1 should only have "accuracy"
        assert registry1.list_metrics() == ["accuracy"]
        assert registry1.get("accuracy") is dummy_metric
        with pytest.raises(KeyError):
            registry1.get("f1")

        # registry2 should only have "f1"
        assert registry2.list_metrics() == ["f1"]
        assert registry2.get("f1") is another_metric
        with pytest.raises(KeyError):
            registry2.get("accuracy")

    def test_empty_registries_are_independent(self):
        """Test that empty registries maintain independence."""
        registry1 = MetricRegistry()
        registry2 = MetricRegistry()

        assert registry1.list_metrics() == []
        assert registry2.list_metrics() == []

        # Registering in one should not affect the other
        registry1.register("test", dummy_metric)

        assert registry1.list_metrics() == ["test"]
        assert registry2.list_metrics() == []


class TestMetricRegistryTypeHints:
    """Test that the registry works with properly typed callables."""

    def test_properly_typed_metric_function(self):
        """Test that a properly typed metric function works correctly."""

        def typed_metric(predictions: list[Any], references: list[Any]) -> float:
            return len(predictions) / max(1, len(references))

        registry = MetricRegistry()
        registry.register("typed_metric", typed_metric)

        retrieved = registry.get("typed_metric")
        assert retrieved is typed_metric
        assert callable(retrieved)

    def test_lambda_function_as_metric(self):
        """Test that lambda functions work as metrics."""
        lambda_metric = lambda preds, refs: 1.0

        registry = MetricRegistry()
        registry.register("lambda_metric", lambda_metric)

        retrieved = registry.get("lambda_metric")
        assert retrieved is lambda_metric
        assert retrieved([], []) == 1.0

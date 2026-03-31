"""Tests for registry and evaluator package exports (TASK-005).

This test module validates the wiring of default shared instances and package
re-exports for AC-SPEC-015 and the associated import requirements.
"""

import pytest
from typing import Any


def test_default_metric_registry_importable():
    """Test that default_metric_registry can be imported from assayer.registries."""
    # This should fail initially when the task is not implemented
    from assayer.registries import default_metric_registry

    # Should be a functional MetricRegistry instance
    assert hasattr(default_metric_registry, 'register')
    assert hasattr(default_metric_registry, 'get')
    assert hasattr(default_metric_registry, 'list_metrics')


def test_default_evaluator_registry_importable():
    """Test that default_evaluator_registry can be imported from assayer.registries."""
    # This should fail initially when the task is not implemented
    from assayer.registries import default_evaluator_registry

    # Should be a functional EvaluatorRegistry instance
    assert hasattr(default_evaluator_registry, 'register')
    assert hasattr(default_evaluator_registry, 'get')
    assert hasattr(default_evaluator_registry, 'list_evaluators')


def test_metric_registry_class_importable():
    """Test that MetricRegistry class can be imported from assayer.registries."""
    # This should fail initially when the task is not implemented
    from assayer.registries import MetricRegistry

    # Should be the actual class, not an instance
    assert isinstance(MetricRegistry, type)

    # Should be able to instantiate
    registry = MetricRegistry()
    assert hasattr(registry, 'register')


def test_evaluator_registry_class_importable():
    """Test that EvaluatorRegistry class can be imported from assayer.registries."""
    # This should fail initially when the task is not implemented
    from assayer.registries import EvaluatorRegistry

    # Should be the actual class, not an instance
    assert isinstance(EvaluatorRegistry, type)

    # Should be able to instantiate
    registry = EvaluatorRegistry()
    assert hasattr(registry, 'register')


def test_base_evaluator_importable():
    """Test that BaseEvaluator can be imported from assayer.evaluators."""
    # This should already work, but verifying for completeness
    from assayer.evaluators import BaseEvaluator

    # Should be the actual class
    assert isinstance(BaseEvaluator, type)

    # Should be abstract (cannot instantiate directly)
    with pytest.raises(TypeError):
        BaseEvaluator("test")


def test_default_metric_registry_functional():
    """Test that default_metric_registry is functional (AC-SPEC-015)."""
    # This should fail initially when the task is not implemented
    from assayer.registries import default_metric_registry

    # Should be able to register and retrieve entries
    def dummy_metric(predictions: list[Any], references: list[Any]) -> float:
        return 0.5

    default_metric_registry.register("test_metric", dummy_metric)
    retrieved = default_metric_registry.get("test_metric")
    assert retrieved is dummy_metric

    # Clean up for other tests
    default_metric_registry._registry.pop("test_metric", None)


def test_default_evaluator_registry_functional():
    """Test that default_evaluator_registry is functional (AC-SPEC-015)."""
    # This should fail initially when the task is not implemented
    from assayer.registries import default_evaluator_registry
    from assayer.evaluators import BaseEvaluator
    from assayer.models import FieldEvaluation

    # Create a dummy evaluator class
    class DummyEvaluator(BaseEvaluator):
        def evaluate(self, prediction: Any, reference: Any, **kwargs) -> FieldEvaluation:
            return FieldEvaluation(
                field_name="test",
                passed=True,
                score=1.0,
                details={}
            )

    # Should be able to register and retrieve entries
    default_evaluator_registry.register("test_evaluator", DummyEvaluator)
    retrieved = default_evaluator_registry.get("test_evaluator")
    assert retrieved is DummyEvaluator

    # Clean up for other tests
    default_evaluator_registry._registry.pop("test_evaluator", None)


def test_registries_all_exports():
    """Test that assayer.registries.__all__ contains all four required names."""
    # This should fail initially when the task is not implemented
    from assayer import registries

    expected_exports = {
        "MetricRegistry",
        "EvaluatorRegistry",
        "default_metric_registry",
        "default_evaluator_registry"
    }

    assert hasattr(registries, '__all__')
    actual_exports = set(registries.__all__)

    # All four names should be present
    assert expected_exports.issubset(actual_exports), f"Missing exports: {expected_exports - actual_exports}"


def test_evaluators_all_exports():
    """Test that assayer.evaluators.__all__ contains BaseEvaluator."""
    # This should already work based on the existing code
    from assayer import evaluators

    assert hasattr(evaluators, '__all__')
    assert "BaseEvaluator" in evaluators.__all__


def test_default_instances_are_separate_from_new_instances():
    """Test that default instances don't share state with new instances."""
    # This should fail initially when the task is not implemented
    from assayer.registries import default_metric_registry, MetricRegistry
    from assayer.registries import default_evaluator_registry, EvaluatorRegistry

    # Create new instances
    new_metric_registry = MetricRegistry()
    new_evaluator_registry = EvaluatorRegistry()

    # They should not be the same objects
    assert default_metric_registry is not new_metric_registry
    assert default_evaluator_registry is not new_evaluator_registry

    # They should not share state
    def dummy_metric(predictions: list[Any], references: list[Any]) -> float:
        return 0.1

    default_metric_registry.register("default_test", dummy_metric)
    assert "default_test" in default_metric_registry.list_metrics()
    assert "default_test" not in new_metric_registry.list_metrics()

    # Clean up
    default_metric_registry._registry.pop("default_test", None)


def test_all_imports_work_together():
    """Test that all required imports work together in a single statement."""
    # This should fail initially when the task is not implemented
    from assayer.registries import (
        MetricRegistry,
        EvaluatorRegistry,
        default_metric_registry,
        default_evaluator_registry
    )
    from assayer.evaluators import BaseEvaluator

    # All should be accessible
    assert isinstance(MetricRegistry, type)
    assert isinstance(EvaluatorRegistry, type)
    assert hasattr(default_metric_registry, 'register')
    assert hasattr(default_evaluator_registry, 'register')
    assert isinstance(BaseEvaluator, type)
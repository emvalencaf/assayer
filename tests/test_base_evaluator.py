"""Tests for BaseEvaluator abstract base class.

This module tests the BaseEvaluator abstract class to ensure it enforces
proper subclassing requirements and validates constructor parameters.
"""

import pytest
from typing import Any

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation


class ConcreteEvaluator(BaseEvaluator):
    """Test evaluator that properly implements the evaluate method."""

    def evaluate(self, prediction: Any, reference: Any, **kwargs: Any) -> FieldEvaluation:
        """Mock implementation of evaluate method."""
        return FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value=reference,
            obtained_value=prediction,
            score=1.0,
            prompt_hash=None
        )


class IncompleteEvaluator(BaseEvaluator):
    """Test evaluator that does not implement evaluate method."""
    pass


class TestBaseEvaluatorInstantiation:
    """Test cases for BaseEvaluator instantiation and validation."""

    def test_concrete_subclass_can_be_instantiated_with_name(self):
        """AC-SPEC-001: Concrete subclass can be instantiated with name."""
        evaluator = ConcreteEvaluator("test_evaluator")
        assert evaluator.name == "test_evaluator"

    def test_concrete_subclass_name_property_returns_provided_value(self):
        """AC-SPEC-001: name property returns the provided value."""
        test_name = "my_custom_evaluator"
        evaluator = ConcreteEvaluator(test_name)
        assert evaluator.name == test_name

    def test_base_evaluator_cannot_be_instantiated_directly(self):
        """AC-SPEC-002: BaseEvaluator cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class BaseEvaluator"):
            BaseEvaluator("some_name")

    def test_subclass_without_evaluate_cannot_be_instantiated(self):
        """AC-SPEC-003: Subclass without evaluate() cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class IncompleteEvaluator"):
            IncompleteEvaluator("some_name")

    def test_init_raises_value_error_for_empty_name(self):
        """AC-SPEC-004: __init__ raises ValueError for empty name."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ConcreteEvaluator("")

    def test_init_raises_value_error_for_whitespace_only_name(self):
        """AC-SPEC-004: __init__ raises ValueError for whitespace-only name."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ConcreteEvaluator("   ")

    def test_init_raises_value_error_for_tabs_only_name(self):
        """AC-SPEC-004: __init__ raises ValueError for whitespace-only name with tabs."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ConcreteEvaluator("\t\t")

    def test_init_raises_value_error_for_newlines_only_name(self):
        """AC-SPEC-004: __init__ raises ValueError for whitespace-only name with newlines."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ConcreteEvaluator("\n\n")

    def test_init_raises_value_error_for_mixed_whitespace_name(self):
        """AC-SPEC-004: __init__ raises ValueError for mixed whitespace-only name."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ConcreteEvaluator(" \t\n ")


class TestBaseEvaluatorNameProperty:
    """Test cases for the name property behavior."""

    def test_name_property_is_read_only(self):
        """Name property should be read-only (no setter)."""
        evaluator = ConcreteEvaluator("test_name")

        # Attempt to set the name property should fail
        with pytest.raises(AttributeError):
            evaluator.name = "new_name"

    def test_name_strips_whitespace_from_provided_value(self):
        """Name should strip leading and trailing whitespace."""
        evaluator = ConcreteEvaluator("  test_name  ")
        assert evaluator.name == "test_name"

    def test_name_preserves_internal_whitespace(self):
        """Name should preserve internal whitespace in the name."""
        evaluator = ConcreteEvaluator("  my evaluator name  ")
        assert evaluator.name == "my evaluator name"


class TestBaseEvaluatorAbstractMethod:
    """Test cases for the abstract evaluate method contract."""

    def test_concrete_evaluator_evaluate_method_signature(self):
        """Ensure the evaluate method has the correct signature."""
        evaluator = ConcreteEvaluator("test")

        # Should be able to call with positional arguments
        result = evaluator.evaluate("prediction", "reference")
        assert isinstance(result, FieldEvaluation)

    def test_concrete_evaluator_evaluate_method_with_kwargs(self):
        """Ensure the evaluate method accepts keyword arguments."""
        evaluator = ConcreteEvaluator("test")

        # Should be able to call with keyword arguments
        result = evaluator.evaluate("prediction", "reference", extra_param="value")
        assert isinstance(result, FieldEvaluation)

    def test_concrete_evaluator_returns_field_evaluation(self):
        """Ensure the evaluate method returns FieldEvaluation."""
        evaluator = ConcreteEvaluator("test")
        result = evaluator.evaluate("pred", "ref")

        assert isinstance(result, FieldEvaluation)
        assert result.obtained_value == "pred"
        assert result.expected_value == "ref"
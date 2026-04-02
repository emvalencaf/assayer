"""Tests for FieldRouter class.

This module tests the FieldRouter implementation, including constructor validation,
route method behavior with different output types, and error handling.
"""

import pytest
from unittest.mock import Mock
from typing import Any

from assayer.models import FieldEvaluation
from assayer.evaluators.base import BaseEvaluator
from assayer.registries.evaluator_registry import EvaluatorRegistry


class MockEvaluator(BaseEvaluator):
    """Mock evaluator for testing that accepts field_name kwarg."""

    def __init__(self, name: str, field_name: str = None) -> None:
        """Initialize mock evaluator with optional field_name."""
        super().__init__(name)
        self.field_name = field_name
        self.evaluate_calls = []

    def evaluate(
        self,
        prediction: Any,
        reference: Any,
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Mock evaluate method that records calls and returns a test FieldEvaluation."""
        self.evaluate_calls.append((prediction, reference, kwargs))
        return FieldEvaluation(
            field_name=self.field_name or self._name,
            evaluator_method=self._name,
            expected_value=reference,
            obtained_value=prediction,
            score=0.8,
            prompt_hash=None,
        )


class AnotherMockEvaluator(BaseEvaluator):
    """Another mock evaluator for testing multiple evaluators per field."""

    def __init__(self, name: str, field_name: str = None) -> None:
        """Initialize mock evaluator with optional field_name."""
        super().__init__(name)
        self.field_name = field_name
        self.evaluate_calls = []

    def evaluate(
        self,
        prediction: Any,
        reference: Any,
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Mock evaluate method that returns a different score."""
        self.evaluate_calls.append((prediction, reference, kwargs))
        return FieldEvaluation(
            field_name=self.field_name or self._name,
            evaluator_method=self._name,
            expected_value=reference,
            obtained_value=prediction,
            score=0.6,
            prompt_hash=None,
        )


class TestFieldRouter:
    """Test cases for FieldRouter class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test method."""
        self.registry = EvaluatorRegistry()
        self.registry.register("mock_eval", MockEvaluator)
        self.registry.register("another_eval", AnotherMockEvaluator)

    def test_constructor_validates_evaluator_names(self) -> None:
        """Constructor should raise KeyError if any evaluator name is not in the registry."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "field1": ["mock_eval"],
            "field2": ["nonexistent_evaluator"],
        }

        with pytest.raises(KeyError, match="Evaluator 'nonexistent_evaluator' is not registered"):
            FieldRouter(field_evaluators, self.registry)

    def test_constructor_validates_all_evaluator_names_before_instantiation(self) -> None:
        """Constructor should validate all names before attempting to instantiate any evaluators."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "field1": ["nonexistent1"],
            "field2": ["nonexistent2"],
        }

        with pytest.raises(KeyError):
            FieldRouter(field_evaluators, self.registry)

    def test_constructor_instantiates_evaluators_with_field_name(self) -> None:
        """Constructor should instantiate evaluators with field_name parameter."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "chat": ["mock_eval"],
            "label": ["another_eval"],
        }

        router = FieldRouter(field_evaluators, self.registry)

        # Check that evaluators were instantiated with the correct field names
        assert "chat" in router._routes
        assert "label" in router._routes
        assert len(router._routes["chat"]) == 1
        assert len(router._routes["label"]) == 1
        assert router._routes["chat"][0].field_name == "chat"
        assert router._routes["label"][0].field_name == "label"

    def test_route_with_dict_output_extracts_fields_by_key(self) -> None:
        """route() should extract field values by key when output is a dict."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "chat": ["mock_eval"],
            "label": ["another_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        output = {"chat": "Hello world", "label": "positive"}
        expected_output = {"chat": "Hi there", "label": "positive"}

        results = router.route(output, expected_output)

        assert len(results) == 2

        # Find results by evaluator method
        mock_result = next(r for r in results if r.evaluator_method == "mock_eval")
        another_result = next(r for r in results if r.evaluator_method == "another_eval")

        assert mock_result.field_name == "chat"
        assert mock_result.obtained_value == "Hello world"
        assert mock_result.expected_value == "Hi there"

        assert another_result.field_name == "label"
        assert another_result.obtained_value == "positive"
        assert another_result.expected_value == "positive"

    def test_route_with_scalar_output_uses_full_value(self) -> None:
        """route() should use the full value when output is not a dict."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "response": ["mock_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        output = "This is a scalar response"
        expected_output = "This is the expected response"

        results = router.route(output, expected_output)

        assert len(results) == 1
        assert results[0].field_name == "response"
        assert results[0].obtained_value == "This is a scalar response"
        assert results[0].expected_value == "This is the expected response"

    def test_route_with_mixed_output_types(self) -> None:
        """route() should handle mixed dict/scalar inputs correctly."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "content": ["mock_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        # Dict output with scalar expected
        output = {"content": "dict value"}
        expected_output = "scalar expected"

        results = router.route(output, expected_output)

        assert len(results) == 1
        assert results[0].obtained_value == "dict value"
        assert results[0].expected_value == "scalar expected"

        # Scalar output with dict expected
        output = "scalar value"
        expected_output = {"content": "dict expected"}

        results = router.route(output, expected_output)

        assert len(results) == 1
        assert results[0].obtained_value == "scalar value"
        assert results[0].expected_value == "dict expected"

    def test_route_returns_one_evaluation_per_field_evaluator_pair(self) -> None:
        """route() should return exactly one FieldEvaluation per (field, evaluator) pair."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "chat": ["mock_eval", "another_eval"],
            "label": ["mock_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        output = {"chat": "Hello", "label": "positive"}
        expected_output = {"chat": "Hi", "label": "positive"}

        results = router.route(output, expected_output)

        # Should have 3 results: 2 for "chat" field + 1 for "label" field
        assert len(results) == 3

        # Count evaluations per field
        chat_results = [r for r in results if r.field_name == "chat"]
        label_results = [r for r in results if r.field_name == "label"]

        assert len(chat_results) == 2
        assert len(label_results) == 1

        # Check that different evaluators produced different results for the same field
        chat_methods = [r.evaluator_method for r in chat_results]
        assert "mock_eval" in chat_methods
        assert "another_eval" in chat_methods

    def test_route_with_empty_field_evaluators(self) -> None:
        """route() should return empty list when no field evaluators are configured."""
        from assayer.runner.field_router import FieldRouter

        router = FieldRouter({}, self.registry)

        output = {"field": "value"}
        expected_output = {"field": "expected"}

        results = router.route(output, expected_output)

        assert results == []

    def test_route_evaluates_all_fields_independently(self) -> None:
        """route() should evaluate each field independently with its configured evaluators."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "field1": ["mock_eval"],
            "field2": ["another_eval"],
            "field3": ["mock_eval", "another_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        output = {
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        }
        expected_output = {
            "field1": "expected1",
            "field2": "expected2",
            "field3": "expected3"
        }

        results = router.route(output, expected_output)

        # Should have 4 total results: 1 + 1 + 2
        assert len(results) == 4

        # Verify each field was evaluated correctly
        field1_results = [r for r in results if r.field_name == "field1"]
        field2_results = [r for r in results if r.field_name == "field2"]
        field3_results = [r for r in results if r.field_name == "field3"]

        assert len(field1_results) == 1
        assert len(field2_results) == 1
        assert len(field3_results) == 2

        # Check values were passed correctly
        assert field1_results[0].obtained_value == "value1"
        assert field1_results[0].expected_value == "expected1"

        assert field2_results[0].obtained_value == "value2"
        assert field2_results[0].expected_value == "expected2"

        for result in field3_results:
            assert result.obtained_value == "value3"
            assert result.expected_value == "expected3"

    def test_constructor_with_multiple_evaluators_per_field(self) -> None:
        """Constructor should handle multiple evaluators per field correctly."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "text": ["mock_eval", "another_eval"],
        }

        router = FieldRouter(field_evaluators, self.registry)

        assert "text" in router._routes
        assert len(router._routes["text"]) == 2

        # Check both evaluators have the same field name
        for evaluator in router._routes["text"]:
            assert evaluator.field_name == "text"

    def test_route_with_none_values(self) -> None:
        """route() should handle None values in output and expected_output."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "response": ["mock_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        # Test None output
        results = router.route(None, "expected")
        assert len(results) == 1
        assert results[0].obtained_value is None
        assert results[0].expected_value == "expected"

        # Test None expected_output
        results = router.route("actual", None)
        assert len(results) == 1
        assert results[0].obtained_value == "actual"
        assert results[0].expected_value is None

        # Test both None
        results = router.route(None, None)
        assert len(results) == 1
        assert results[0].obtained_value is None
        assert results[0].expected_value is None

    def test_route_with_missing_field_in_dict(self) -> None:
        """route() should handle missing fields gracefully when extracting from dicts."""
        from assayer.runner.field_router import FieldRouter

        field_evaluators = {
            "missing_field": ["mock_eval"],
        }
        router = FieldRouter(field_evaluators, self.registry)

        output = {"other_field": "value"}
        expected_output = {"missing_field": "expected"}

        # Should raise KeyError when trying to access missing field
        with pytest.raises(KeyError):
            router.route(output, expected_output)
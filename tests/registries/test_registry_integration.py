"""End-to-end integration tests for registry and extension functionality.

This module tests the complete user workflow for registering and using custom
metrics and evaluators, ensuring all components work together correctly.
"""

from typing import Any

import pytest

from assayer.evaluators import BaseEvaluator
from assayer.models import FieldEvaluation
from assayer.registries import EvaluatorRegistry, MetricRegistry


def test_custom_metric_registration_and_usage():
    """Test end-to-end workflow for custom metric registration and execution.

    This test validates that a custom metric function can be registered in a
    MetricRegistry, retrieved by name, and called with sample data to produce
    the expected result.
    """
    # Create an independent registry instance
    registry = MetricRegistry()

    # Define a custom metric function
    def custom_accuracy(predictions: list[Any], references: list[Any]) -> float:
        """Simple accuracy metric for testing."""
        if len(predictions) != len(references):
            return 0.0
        if len(predictions) == 0:
            return 0.0

        correct = sum(1 for p, r in zip(predictions, references) if p == r)
        return correct / len(predictions)

    # Register the metric
    registry.register("custom_accuracy", custom_accuracy)

    # Retrieve the metric by name
    retrieved_metric = registry.get("custom_accuracy")

    # Verify it's the same function
    assert retrieved_metric is custom_accuracy

    # Call the metric with sample data
    sample_predictions = ["cat", "dog", "bird", "cat"]
    sample_references = ["cat", "dog", "fish", "cat"]

    result = retrieved_metric(sample_predictions, sample_references)

    # Assert the expected result (3 out of 4 correct = 0.75)
    assert result == 0.75


def test_custom_evaluator_registration_and_usage():
    """Test end-to-end workflow for custom evaluator registration and execution.

    This test validates that a custom evaluator subclass can be registered in an
    EvaluatorRegistry, retrieved by name, instantiated, and used to produce a
    valid FieldEvaluation.
    """
    # Create an independent registry instance
    registry = EvaluatorRegistry()

    # Define a custom evaluator subclass
    class ExactMatchEvaluator(BaseEvaluator):
        """Simple exact match evaluator for testing."""

        def evaluate(
            self,
            prediction: Any,
            reference: Any,
            **kwargs: Any,
        ) -> FieldEvaluation:
            """Evaluate prediction against reference using exact matching."""
            score = 1.0 if prediction == reference else 0.0

            return FieldEvaluation(
                field_name=kwargs.get("field_name", "test_field"),
                evaluator_method=self.name,
                expected_value=reference,
                obtained_value=prediction,
                score=score,
                prompt_hash=None,
                metadata={"match_type": "exact"},
            )

    # Register the evaluator class
    registry.register("exact_match", ExactMatchEvaluator)

    # Retrieve the evaluator class by name
    retrieved_class = registry.get("exact_match")

    # Verify it's the same class
    assert retrieved_class is ExactMatchEvaluator

    # Instantiate the evaluator
    evaluator = retrieved_class("test_exact_match")

    # Verify it's a BaseEvaluator instance
    assert isinstance(evaluator, BaseEvaluator)
    assert evaluator.name == "test_exact_match"

    # Call evaluate() with sample data
    prediction = "hello world"
    reference = "hello world"

    result = evaluator.evaluate(prediction, reference, field_name="output_text")

    # Assert the result is a valid FieldEvaluation
    assert isinstance(result, FieldEvaluation)
    assert result.field_name == "output_text"
    assert result.evaluator_method == "test_exact_match"
    assert result.expected_value == reference
    assert result.obtained_value == prediction
    assert result.score == 1.0  # Exact match
    assert result.prompt_hash is None
    assert result.metadata == {"match_type": "exact"}


def test_registry_isolation():
    """Test that independently instantiated registries do not share state.

    This test validates that creating separate registry instances ensures
    complete isolation between registrations.
    """
    # Create two independent metric registries
    metric_registry_1 = MetricRegistry()
    metric_registry_2 = MetricRegistry()

    # Create two independent evaluator registries
    evaluator_registry_1 = EvaluatorRegistry()
    evaluator_registry_2 = EvaluatorRegistry()

    # Define a metric and evaluator for testing
    def test_metric(predictions: list[Any], references: list[Any]) -> float:
        return 0.5

    class TestEvaluator(BaseEvaluator):
        def evaluate(
            self,
            prediction: Any,
            reference: Any,
            **kwargs: Any,
        ) -> FieldEvaluation:
            return FieldEvaluation(
                field_name="test",
                evaluator_method=self.name,
                expected_value=reference,
                obtained_value=prediction,
                score=0.5,
                prompt_hash=None,
            )

    # Register in first registries only
    metric_registry_1.register("isolation_metric", test_metric)
    evaluator_registry_1.register("isolation_evaluator", TestEvaluator)

    # Verify first registries contain the registrations
    assert "isolation_metric" in metric_registry_1.list_metrics()
    assert "isolation_evaluator" in evaluator_registry_1.list_evaluators()

    # Verify second registries are empty (proving isolation)
    assert "isolation_metric" not in metric_registry_2.list_metrics()
    assert "isolation_evaluator" not in evaluator_registry_2.list_evaluators()

    # Verify retrieval fails in second registries
    with pytest.raises(KeyError):
        metric_registry_2.get("isolation_metric")

    with pytest.raises(KeyError):
        evaluator_registry_2.get("isolation_evaluator")


def test_complete_integration_workflow():
    """Test complete integration workflow with both metrics and evaluators.

    This test exercises the full workflow where a custom evaluator uses a
    custom metric internally, demonstrating the complete extension story.
    """
    # Create independent registries
    metric_registry = MetricRegistry()
    evaluator_registry = EvaluatorRegistry()

    # Define a custom metric
    def fuzzy_match_score(predictions: list[Any], references: list[Any]) -> float:
        """Calculate fuzzy matching score for lists."""
        if not predictions or not references:
            return 0.0

        # Simple fuzzy logic: case-insensitive matches
        total_score = 0.0
        for pred, ref in zip(predictions, references):
            pred_lower = str(pred).lower()
            ref_lower = str(ref).lower()
            if pred_lower == ref_lower:
                total_score += 1.0
            elif pred_lower in ref_lower or ref_lower in pred_lower:
                total_score += 0.5

        return total_score / max(len(predictions), len(references))

    # Define a custom evaluator that could use the metric
    class FuzzyEvaluator(BaseEvaluator):
        """Evaluator that performs fuzzy matching."""

        def evaluate(
            self,
            prediction: Any,
            reference: Any,
            **kwargs: Any,
        ) -> FieldEvaluation:
            # Simple fuzzy matching logic
            pred_str = str(prediction).lower()
            ref_str = str(reference).lower()

            if pred_str == ref_str:
                score = 1.0
            elif pred_str in ref_str or ref_str in pred_str:
                score = 0.7
            else:
                score = 0.0

            return FieldEvaluation(
                field_name=kwargs.get("field_name", "fuzzy_field"),
                evaluator_method=self.name,
                expected_value=reference,
                obtained_value=prediction,
                score=score,
                prompt_hash=None,
                metadata={"fuzzy_algorithm": "substring"},
            )

    # Register both
    metric_registry.register("fuzzy_match", fuzzy_match_score)
    evaluator_registry.register("fuzzy_evaluator", FuzzyEvaluator)

    # Retrieve and use the metric
    metric_fn = metric_registry.get("fuzzy_match")
    metric_result = metric_fn(["hello", "world"], ["Hello", "World"])
    assert metric_result == 1.0  # Case-insensitive exact matches

    # Retrieve and use the evaluator
    evaluator_class = evaluator_registry.get("fuzzy_evaluator")
    evaluator = evaluator_class("fuzzy_test")

    evaluation_result = evaluator.evaluate("Hello World", "hello world", field_name="greeting")

    # Verify the complete workflow
    assert isinstance(evaluation_result, FieldEvaluation)
    assert evaluation_result.field_name == "greeting"
    assert evaluation_result.evaluator_method == "fuzzy_test"
    assert evaluation_result.score == 1.0  # Case-insensitive exact match

    # Verify both registries maintain their state
    assert len(metric_registry.list_metrics()) == 1
    assert len(evaluator_registry.list_evaluators()) == 1
    assert "fuzzy_match" in metric_registry.list_metrics()
    assert "fuzzy_evaluator" in evaluator_registry.list_evaluators()

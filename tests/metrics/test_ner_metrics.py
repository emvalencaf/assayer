"""Tests for NER metrics and registration functions."""

import pytest

# Import evaluator components that are already implemented
from assayer.evaluators.ner import EntitySpan, NERMatcher
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry

# Import will fail until implementation exists - that's expected for TDD
try:
    from assayer.metrics.ner import ner_macro_f1, register_ner_evaluators, register_ner_metrics
except ImportError:
    ner_macro_f1 = None
    register_ner_metrics = None
    register_ner_evaluators = None


class TestNerMacroF1:
    """Test cases for the ner_macro_f1 batch metric function."""

    def test_ner_macro_f1_perfect_match_single_example(self):
        """Test ner_macro_f1 with perfect predictions for a single example."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = [
            [EntitySpan("John Doe", "PERSON", 0, 8), EntitySpan("Apple Inc", "ORG", 20, 29)]
        ]
        references = [
            [EntitySpan("John Doe", "PERSON", 0, 8), EntitySpan("Apple Inc", "ORG", 20, 29)]
        ]

        result = ner_macro_f1(predictions, references)

        # Should return 1.0 for perfect match
        assert abs(result - 1.0) <= 0.001

    def test_ner_macro_f1_perfect_match_multiple_examples(self):
        """Test ner_macro_f1 with perfect predictions across multiple examples."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = [
            [EntitySpan("John", "PERSON", 0, 4)],
            [EntitySpan("Apple", "ORG", 10, 15)],
            [EntitySpan("Paris", "LOC", 5, 10)],
        ]
        references = [
            [EntitySpan("John", "PERSON", 0, 4)],
            [EntitySpan("Apple", "ORG", 10, 15)],
            [EntitySpan("Paris", "LOC", 5, 10)],
        ]

        result = ner_macro_f1(predictions, references)

        # Should return 1.0 for perfect match across all examples
        assert abs(result - 1.0) <= 0.001

    def test_ner_macro_f1_partial_match_multiple_examples(self):
        """Test ner_macro_f1 with varying accuracy across examples."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        # Example 1: Perfect match (F1 = 1.0)
        # Example 2: Partial match (some precision/recall issues)
        # Example 3: No match (F1 = 0.0)
        predictions = [
            # Example 1: Perfect match
            [EntitySpan("John", "PERSON", 0, 4)],
            # Example 2: Missing one entity from reference
            [EntitySpan("Apple", "ORG", 0, 5)],
            # Example 3: Completely wrong prediction
            [EntitySpan("Wrong", "PERSON", 0, 5)],
        ]
        references = [
            # Example 1: Perfect match
            [EntitySpan("John", "PERSON", 0, 4)],
            # Example 2: Has two entities, predictions only has one
            [EntitySpan("Apple", "ORG", 0, 5), EntitySpan("Google", "ORG", 10, 16)],
            # Example 3: Different entity entirely
            [EntitySpan("Correct", "LOC", 10, 17)],
        ]

        result = ner_macro_f1(predictions, references)

        # Calculate expected result manually:
        # Example 1: F1 = 1.0 (perfect match)
        # Example 2: precision=1.0 (1/1), recall=0.5 (1/2), F1=0.667
        # Example 3: F1 = 0.0 (no match)
        # Mean = (1.0 + 0.667 + 0.0) / 3 = 0.556
        expected = (1.0 + (2 * 1.0 * 0.5 / (1.0 + 0.5)) + 0.0) / 3
        assert abs(result - expected) <= 0.001

    def test_ner_macro_f1_empty_inputs(self):
        """Test ner_macro_f1 returns 0.0 for empty input lists."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = []
        references = []

        result = ner_macro_f1(predictions, references)

        # Should return 0.0 for empty inputs
        assert result == 0.0

    def test_ner_macro_f1_empty_examples_in_lists(self):
        """Test ner_macro_f1 with examples that have empty entity lists."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = [
            [],  # No predicted entities
            [EntitySpan("Apple", "ORG", 0, 5)],  # Has predictions
            [],  # No predicted entities
        ]
        references = [
            [],  # No reference entities
            [],  # No reference entities
            [EntitySpan("Paris", "LOC", 0, 5)],  # Has reference entities
        ]

        result = ner_macro_f1(predictions, references)

        # Example 1: Both empty -> F1 = 0.0 (NERMatcher should return 0.0)
        # Example 2: predictions=1, references=0 -> F1 = 0.0
        # Example 3: predictions=0, references=1 -> F1 = 0.0
        # Mean = (0.0 + 0.0 + 0.0) / 3 = 0.0
        assert result == 0.0

    def test_ner_macro_f1_consistent_with_ner_matcher(self):
        """Test that ner_macro_f1 returns the same values as individual NERMatcher calls."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = [
            [EntitySpan("John", "PERSON", 0, 4), EntitySpan("Apple", "ORG", 10, 15)],
            [EntitySpan("Paris", "LOC", 0, 5)],
        ]
        references = [
            [EntitySpan("John", "PERSON", 0, 4), EntitySpan("Google", "ORG", 10, 16)],
            [EntitySpan("Paris", "LOC", 0, 5), EntitySpan("London", "LOC", 10, 16)],
        ]

        result = ner_macro_f1(predictions, references)

        # Calculate expected using NERMatcher directly
        matcher = NERMatcher()
        scores = []
        for pred, ref in zip(predictions, references):
            match_result = matcher.match(pred, ref)
            scores.append(match_result.macro_f1)
        expected = sum(scores) / len(scores)

        assert abs(result - expected) <= 0.001

    def test_ner_macro_f1_single_example_multiple_types(self):
        """Test ner_macro_f1 with one example containing multiple entity types."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = [
            [
                EntitySpan("John Doe", "PERSON", 0, 8),
                EntitySpan("Apple Inc", "ORG", 20, 29),
                EntitySpan("New York", "LOC", 40, 48),
                EntitySpan("Jane Smith", "PERSON", 60, 70),
            ]
        ]
        references = [
            [
                EntitySpan("John Doe", "PERSON", 0, 8),  # TP for PERSON
                EntitySpan("Microsoft", "ORG", 30, 39),  # FN for ORG (different entity)
                EntitySpan("New York", "LOC", 40, 48),  # TP for LOC
                EntitySpan("Jane Smith", "PERSON", 60, 70),  # TP for PERSON
            ]
        ]

        result = ner_macro_f1(predictions, references)

        # Calculate expected manually:
        # PERSON: 2 TP, 0 FP, 0 FN -> precision=1.0, recall=1.0, F1=1.0
        # ORG: 0 TP, 1 FP, 1 FN -> precision=0.0, recall=0.0, F1=0.0
        # LOC: 1 TP, 0 FP, 0 FN -> precision=1.0, recall=1.0, F1=1.0
        # Macro F1 = (1.0 + 0.0 + 1.0) / 3 = 0.667
        expected = (1.0 + 0.0 + 1.0) / 3
        assert abs(result - expected) <= 0.001

    def test_ner_macro_f1_mismatched_list_lengths(self):
        """Test ner_macro_f1 behavior with mismatched prediction and reference list lengths."""
        if ner_macro_f1 is None:
            pytest.skip("ner_macro_f1 function not implemented yet")

        predictions = [[EntitySpan("John", "PERSON", 0, 4)], [EntitySpan("Apple", "ORG", 0, 5)]]
        references = [
            [EntitySpan("John", "PERSON", 0, 4)]
            # Missing second reference
        ]

        # This should be handled gracefully - zip will stop at the shorter list
        result = ner_macro_f1(predictions, references)

        # Only the first example should be processed (perfect match)
        assert abs(result - 1.0) <= 0.001


class TestRegisterNerMetrics:
    """Test cases for the register_ner_metrics function."""

    def test_register_ner_metrics_success(self):
        """Test that register_ner_metrics successfully registers ner_macro_f1."""
        if register_ner_metrics is None:
            pytest.skip("register_ner_metrics function not implemented yet")

        registry = MetricRegistry()

        # Should not raise any exceptions
        register_ner_metrics(registry)

        # Should be able to retrieve the registered metric
        metric_fn = registry.get("ner_macro_f1")
        assert callable(metric_fn)

    def test_register_ner_metrics_retrieves_working_function(self):
        """Test that the registered metric function actually works."""
        if register_ner_metrics is None:
            pytest.skip("register_ner_metrics function not implemented yet")

        registry = MetricRegistry()
        register_ner_metrics(registry)

        metric_fn = registry.get("ner_macro_f1")

        # Test the retrieved function with a simple case
        predictions = [[EntitySpan("John", "PERSON", 0, 4)]]
        references = [[EntitySpan("John", "PERSON", 0, 4)]]

        result = metric_fn(predictions, references)
        assert abs(result - 1.0) <= 0.001

    def test_register_ner_metrics_duplicate_registration_raises_error(self):
        """Test that registering metrics twice raises KeyError."""
        if register_ner_metrics is None:
            pytest.skip("register_ner_metrics function not implemented yet")

        registry = MetricRegistry()

        # First registration should succeed
        register_ner_metrics(registry)

        # Second registration should raise KeyError
        with pytest.raises(KeyError, match="Metric 'ner_macro_f1' is already registered"):
            register_ner_metrics(registry)

    def test_register_ner_metrics_appears_in_list(self):
        """Test that registered metric appears in the registry's metric list."""
        if register_ner_metrics is None:
            pytest.skip("register_ner_metrics function not implemented yet")

        registry = MetricRegistry()
        register_ner_metrics(registry)

        metric_names = registry.list_metrics()
        assert "ner_macro_f1" in metric_names


class TestRegisterNerEvaluators:
    """Test cases for the register_ner_evaluators function."""

    def test_register_ner_evaluators_success(self):
        """Test that register_ner_evaluators successfully registers NEREvaluator."""
        if register_ner_evaluators is None:
            pytest.skip("register_ner_evaluators function not implemented yet")

        registry = EvaluatorRegistry()

        # Should not raise any exceptions
        register_ner_evaluators(registry)

        # Should be able to retrieve the registered evaluator class
        evaluator_cls = registry.get("ner")
        assert evaluator_cls is not None
        assert isinstance(evaluator_cls, type)

    def test_register_ner_evaluators_retrieves_ner_evaluator_class(self):
        """Test that the registered evaluator class is NEREvaluator."""
        if register_ner_evaluators is None:
            pytest.skip("register_ner_evaluators function not implemented yet")

        # Import NEREvaluator to check class identity
        from assayer.evaluators.ner import NEREvaluator

        registry = EvaluatorRegistry()
        register_ner_evaluators(registry)

        evaluator_cls = registry.get("ner")
        assert evaluator_cls is NEREvaluator

    def test_register_ner_evaluators_can_instantiate_evaluator(self):
        """Test that the registered evaluator class can be instantiated and used."""
        if register_ner_evaluators is None:
            pytest.skip("register_ner_evaluators function not implemented yet")

        registry = EvaluatorRegistry()
        register_ner_evaluators(registry)

        evaluator_cls = registry.get("ner")

        # Should be able to instantiate the evaluator
        evaluator = evaluator_cls(field_name="entities")
        assert evaluator is not None

        # Test evaluation with simple case
        predictions = [EntitySpan("John", "PERSON", 0, 4)]
        references = [EntitySpan("John", "PERSON", 0, 4)]

        result = evaluator.evaluate(predictions, references)
        assert result is not None
        assert abs(result.score - 1.0) <= 0.001

    def test_register_ner_evaluators_duplicate_registration_raises_error(self):
        """Test that registering evaluators twice raises KeyError."""
        if register_ner_evaluators is None:
            pytest.skip("register_ner_evaluators function not implemented yet")

        registry = EvaluatorRegistry()

        # First registration should succeed
        register_ner_evaluators(registry)

        # Second registration should raise KeyError
        with pytest.raises(KeyError, match="Evaluator 'ner' is already registered"):
            register_ner_evaluators(registry)

    def test_register_ner_evaluators_appears_in_list(self):
        """Test that registered evaluator appears in the registry's evaluator list."""
        if register_ner_evaluators is None:
            pytest.skip("register_ner_evaluators function not implemented yet")

        registry = EvaluatorRegistry()
        register_ner_evaluators(registry)

        evaluator_names = registry.list_evaluators()
        assert "ner" in evaluator_names


class TestNerMetricsIntegration:
    """Integration tests for NER metrics and evaluators."""

    def test_both_registrations_work_together(self):
        """Test that both metric and evaluator registrations work in the same session."""
        if register_ner_metrics is None or register_ner_evaluators is None:
            pytest.skip("NER registration functions not implemented yet")

        metric_registry = MetricRegistry()
        evaluator_registry = EvaluatorRegistry()

        # Both registrations should succeed
        register_ner_metrics(metric_registry)
        register_ner_evaluators(evaluator_registry)

        # Should be able to retrieve both
        metric_fn = metric_registry.get("ner_macro_f1")
        evaluator_cls = evaluator_registry.get("ner")

        assert callable(metric_fn)
        assert evaluator_cls is not None

    def test_metric_and_evaluator_produce_consistent_results(self):
        """Test that ner_macro_f1 metric and NEREvaluator produce consistent scores."""
        if register_ner_metrics is None or register_ner_evaluators is None:
            pytest.skip("NER registration functions not implemented yet")

        metric_registry = MetricRegistry()
        evaluator_registry = EvaluatorRegistry()

        register_ner_metrics(metric_registry)
        register_ner_evaluators(evaluator_registry)

        metric_fn = metric_registry.get("ner_macro_f1")
        evaluator_cls = evaluator_registry.get("ner")

        # Test data
        single_prediction = [EntitySpan("John", "PERSON", 0, 4)]
        single_reference = [EntitySpan("John", "PERSON", 0, 4)]

        # Get score from metric function (batch format)
        batch_predictions = [single_prediction]
        batch_references = [single_reference]
        metric_score = metric_fn(batch_predictions, batch_references)

        # Get score from evaluator (single example format)
        evaluator = evaluator_cls(field_name="entities")
        eval_result = evaluator.evaluate(single_prediction, single_reference)
        evaluator_score = eval_result.score

        # Scores should be identical for the same data
        assert abs(metric_score - evaluator_score) <= 0.001

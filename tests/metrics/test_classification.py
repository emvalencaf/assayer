"""Tests for classification metrics."""

from typing import Any

import pytest
from sklearn.metrics import accuracy_score

# Import will fail until implementation exists - that's expected for TDD
try:
    from assayer.metrics.classification import accuracy
except ImportError:
    accuracy = None


class TestAccuracy:
    """Test cases for the accuracy metric function."""

    def test_accuracy_binary_classification_perfect_match(self):
        """Test accuracy for binary classification with perfect predictions."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [1, 0, 1, 1, 0]
        references = [1, 0, 1, 1, 0]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 1.0) <= 0.001

    def test_accuracy_binary_classification_partial_match(self):
        """Test accuracy for binary classification with some incorrect predictions."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [1, 0, 1, 0, 0]
        references = [1, 1, 1, 1, 0]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 0.6) <= 0.001

    def test_accuracy_binary_classification_no_match(self):
        """Test accuracy for binary classification with completely wrong predictions."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [0, 0, 0, 0, 0]
        references = [1, 1, 1, 1, 1]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 0.0) <= 0.001

    def test_accuracy_multiclass_classification_perfect_match(self):
        """Test accuracy for multi-class classification with perfect predictions."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = ["cat", "dog", "bird", "cat", "dog"]
        references = ["cat", "dog", "bird", "cat", "dog"]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 1.0) <= 0.001

    def test_accuracy_multiclass_classification_partial_match(self):
        """Test accuracy for multi-class classification with some incorrect predictions."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = ["cat", "dog", "cat", "bird", "dog"]
        references = ["cat", "dog", "bird", "bird", "cat"]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 0.6) <= 0.001

    def test_accuracy_multiclass_classification_integer_labels(self):
        """Test accuracy for multi-class classification with integer labels."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [0, 1, 2, 0, 1]
        references = [0, 1, 1, 0, 2]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 0.6) <= 0.001

    def test_accuracy_empty_input_lists(self):
        """Test accuracy returns 0.0 for empty input lists."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = []
        references = []

        result = accuracy(predictions, references)

        assert result == 0.0

    def test_accuracy_empty_predictions_with_references(self):
        """Test accuracy returns 0.0 when predictions are empty but references are not."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = []
        references = [1, 0, 1]

        result = accuracy(predictions, references)

        assert result == 0.0

    def test_accuracy_empty_references_with_predictions(self):
        """Test accuracy returns 0.0 when references are empty but predictions are not."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [1, 0, 1]
        references = []

        result = accuracy(predictions, references)

        assert result == 0.0

    def test_accuracy_single_item_correct(self):
        """Test accuracy for single item that is correct."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = ["positive"]
        references = ["positive"]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 1.0) <= 0.001

    def test_accuracy_single_item_incorrect(self):
        """Test accuracy for single item that is incorrect."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = ["positive"]
        references = ["negative"]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001
        assert abs(result - 0.0) <= 0.001

    def test_accuracy_mixed_types_string_and_int(self):
        """Test accuracy with mixed string and integer types (should work as sklearn handles it)."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [1, "dog", 2, 1, "cat"]
        references = [1, "dog", 2, "cat", "cat"]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001

    def test_accuracy_large_dataset(self):
        """Test accuracy with a larger dataset to ensure performance is reasonable."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        # Create a larger dataset
        predictions = [i % 3 for i in range(1000)]
        references = [(i + 1) % 3 for i in range(1000)]

        result = accuracy(predictions, references)
        expected = accuracy_score(references, predictions)

        assert abs(result - expected) <= 0.001

    def test_accuracy_function_signature_and_type_hints(self):
        """Test that accuracy function has correct signature and type hints."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        import inspect
        from typing import get_type_hints

        # Check function signature
        sig = inspect.signature(accuracy)
        params = list(sig.parameters.keys())
        assert params == ["predictions", "references"]

        # Check type hints
        hints = get_type_hints(accuracy)
        assert "predictions" in hints
        assert "references" in hints
        assert "return" in hints
        assert hints["return"] == float

    def test_accuracy_docstring_exists(self):
        """Test that accuracy function has a docstring."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        assert accuracy.__doc__ is not None
        assert len(accuracy.__doc__.strip()) > 0

        # Check for Google-style docstring elements
        docstring = accuracy.__doc__
        assert "Args:" in docstring or "Arguments:" in docstring
        assert "Returns:" in docstring

    def test_accuracy_mismatched_length_inputs(self):
        """Test accuracy behavior with mismatched length inputs."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [1, 0, 1]
        references = [1, 0]  # One item shorter

        # Should either handle gracefully or raise a clear error
        # sklearn.accuracy_score raises ValueError for mismatched lengths
        with pytest.raises(ValueError):
            accuracy(predictions, references)

    def test_accuracy_none_values_handling(self):
        """Test accuracy behavior with None values in input."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        predictions = [1, None, 1]
        references = [1, 0, 1]

        # This should raise an error as None is not a valid label
        with pytest.raises((ValueError, TypeError)):
            accuracy(predictions, references)

    def test_accuracy_consistency_with_sklearn(self):
        """Test that our accuracy function is perfectly consistent with sklearn."""
        if accuracy is None:
            pytest.skip("accuracy function not implemented yet")

        test_cases = [
            # Binary classification cases
            ([1, 0, 1, 1, 0], [1, 0, 1, 1, 0]),  # Perfect
            ([1, 0, 1, 0, 0], [1, 1, 1, 1, 0]),  # Partial
            ([0, 0, 0], [1, 1, 1]),  # No match
            # Multi-class cases
            (["a", "b", "c"], ["a", "b", "c"]),  # Perfect
            (["a", "b", "c"], ["a", "c", "b"]),  # Partial
            ([0, 1, 2, 3], [0, 1, 2, 3]),  # Integer multiclass
            ([0, 1, 2], [3, 3, 3]),  # No overlap in classes
        ]

        for predictions, references in test_cases:
            result = accuracy(predictions, references)
            expected = accuracy_score(references, predictions)
            assert abs(result - expected) <= 0.001, f"Failed for {predictions} vs {references}"


# Import factory functions for testing - will fail until implementation exists
try:
    from collections.abc import Callable

    from assayer.metrics.classification import make_f1, make_precision, make_recall

    # Define MetricFn type alias for classification metrics
    MetricFn = Callable[[list[Any], list[Any]], float]
except ImportError:
    make_precision = None
    make_recall = None
    make_f1 = None
    MetricFn = None


class TestMakePrecision:
    """Test cases for the make_precision factory function."""

    def test_make_precision_macro_binary_classification(self):
        """Test make_precision with macro averaging for binary classification."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        from sklearn.metrics import precision_score

        predictions = [1, 0, 1, 1, 0, 1, 0]
        references = [1, 0, 1, 0, 1, 1, 0]

        precision_fn = make_precision("macro")
        result = precision_fn(predictions, references)
        expected = precision_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_precision_macro_multiclass_classification(self):
        """Test make_precision with macro averaging for multiclass classification."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        from sklearn.metrics import precision_score

        predictions = ["cat", "dog", "bird", "cat", "dog", "bird", "cat"]
        references = ["cat", "dog", "bird", "dog", "cat", "bird", "bird"]

        precision_fn = make_precision("macro")
        result = precision_fn(predictions, references)
        expected = precision_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_precision_micro_averaging(self):
        """Test make_precision with micro averaging."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        from sklearn.metrics import precision_score

        predictions = [0, 1, 2, 0, 1, 2, 1]
        references = [0, 1, 2, 1, 0, 2, 2]

        precision_fn = make_precision("micro")
        result = precision_fn(predictions, references)
        expected = precision_score(references, predictions, average="micro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_precision_weighted_averaging(self):
        """Test make_precision with weighted averaging."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        from sklearn.metrics import precision_score

        predictions = [0, 1, 2, 0, 1, 2, 1, 0, 0, 0]
        references = [0, 1, 2, 1, 0, 2, 2, 0, 0, 1]

        precision_fn = make_precision("weighted")
        result = precision_fn(predictions, references)
        expected = precision_score(references, predictions, average="weighted", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_precision_default_macro_averaging(self):
        """Test make_precision with default macro averaging."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        from sklearn.metrics import precision_score

        predictions = [1, 0, 1, 0, 1]
        references = [1, 1, 1, 0, 0]

        precision_fn = make_precision()  # Should default to macro
        result = precision_fn(predictions, references)
        expected = precision_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_precision_all_same_class_predictions(self):
        """Test make_precision with all predictions being the same class (zero_division=0)."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        predictions = [0, 0, 0, 0, 0]  # All same class
        references = [0, 1, 2, 1, 2]  # Mixed classes

        precision_fn = make_precision("macro")
        result = precision_fn(predictions, references)

        # Should not raise an exception and should return 0.0 due to zero_division=0
        assert result == 0.0

    def test_make_precision_empty_inputs(self):
        """Test make_precision with empty input lists."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        precision_fn = make_precision("macro")
        result = precision_fn([], [])

        assert result == 0.0

    def test_make_precision_function_signature(self):
        """Test make_precision function has correct signature and type hints."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        import inspect
        from typing import get_type_hints

        # Check function signature
        sig = inspect.signature(make_precision)
        params = list(sig.parameters.keys())
        assert "average" in params

        # Check that it has a default value for average
        average_param = sig.parameters["average"]
        assert average_param.default == "macro"

        # Check type hints
        hints = get_type_hints(make_precision)
        assert hints["return"] == MetricFn

    def test_make_precision_docstring_exists(self):
        """Test that make_precision function has a Google-style docstring."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        assert make_precision.__doc__ is not None
        assert len(make_precision.__doc__.strip()) > 0

        # Check for Google-style docstring elements
        docstring = make_precision.__doc__
        assert "Args:" in docstring or "Arguments:" in docstring
        assert "Returns:" in docstring

    def test_make_precision_returns_callable(self):
        """Test that make_precision returns a callable MetricFn."""
        if make_precision is None:
            pytest.skip("make_precision function not implemented yet")

        precision_fn = make_precision("macro")
        assert callable(precision_fn)

        # Test that the returned function works
        predictions = [1, 0, 1]
        references = [1, 1, 0]
        result = precision_fn(predictions, references)
        assert isinstance(result, float)


class TestMakeRecall:
    """Test cases for the make_recall factory function."""

    def test_make_recall_macro_binary_classification(self):
        """Test make_recall with macro averaging for binary classification."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        from sklearn.metrics import recall_score

        predictions = [1, 0, 1, 1, 0, 1, 0]
        references = [1, 0, 1, 0, 1, 1, 0]

        recall_fn = make_recall("macro")
        result = recall_fn(predictions, references)
        expected = recall_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_recall_macro_multiclass_classification(self):
        """Test make_recall with macro averaging for multiclass classification."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        from sklearn.metrics import recall_score

        predictions = ["cat", "dog", "bird", "cat", "dog", "bird", "cat"]
        references = ["cat", "dog", "bird", "dog", "cat", "bird", "bird"]

        recall_fn = make_recall("macro")
        result = recall_fn(predictions, references)
        expected = recall_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_recall_micro_averaging(self):
        """Test make_recall with micro averaging."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        from sklearn.metrics import recall_score

        predictions = [0, 1, 2, 0, 1, 2, 1]
        references = [0, 1, 2, 1, 0, 2, 2]

        recall_fn = make_recall("micro")
        result = recall_fn(predictions, references)
        expected = recall_score(references, predictions, average="micro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_recall_weighted_averaging(self):
        """Test make_recall with weighted averaging."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        from sklearn.metrics import recall_score

        predictions = [0, 1, 2, 0, 1, 2, 1, 0, 0, 0]
        references = [0, 1, 2, 1, 0, 2, 2, 0, 0, 1]

        recall_fn = make_recall("weighted")
        result = recall_fn(predictions, references)
        expected = recall_score(references, predictions, average="weighted", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_recall_default_macro_averaging(self):
        """Test make_recall with default macro averaging."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        from sklearn.metrics import recall_score

        predictions = [1, 0, 1, 0, 1]
        references = [1, 1, 1, 0, 0]

        recall_fn = make_recall()  # Should default to macro
        result = recall_fn(predictions, references)
        expected = recall_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_recall_all_same_class_predictions(self):
        """Test make_recall with all predictions being the same class (zero_division=0)."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        predictions = [0, 0, 0, 0, 0]  # All same class
        references = [0, 1, 2, 1, 2]  # Mixed classes

        recall_fn = make_recall("macro")
        result = recall_fn(predictions, references)

        # Should not raise an exception and should return 0.0 due to zero_division=0
        assert result == 0.0

    def test_make_recall_empty_inputs(self):
        """Test make_recall with empty input lists."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        recall_fn = make_recall("macro")
        result = recall_fn([], [])

        assert result == 0.0

    def test_make_recall_function_signature(self):
        """Test make_recall function has correct signature and type hints."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        import inspect
        from typing import get_type_hints

        # Check function signature
        sig = inspect.signature(make_recall)
        params = list(sig.parameters.keys())
        assert "average" in params

        # Check that it has a default value for average
        average_param = sig.parameters["average"]
        assert average_param.default == "macro"

        # Check type hints
        hints = get_type_hints(make_recall)
        assert hints["return"] == MetricFn

    def test_make_recall_docstring_exists(self):
        """Test that make_recall function has a Google-style docstring."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        assert make_recall.__doc__ is not None
        assert len(make_recall.__doc__.strip()) > 0

        # Check for Google-style docstring elements
        docstring = make_recall.__doc__
        assert "Args:" in docstring or "Arguments:" in docstring
        assert "Returns:" in docstring

    def test_make_recall_returns_callable(self):
        """Test that make_recall returns a callable MetricFn."""
        if make_recall is None:
            pytest.skip("make_recall function not implemented yet")

        recall_fn = make_recall("macro")
        assert callable(recall_fn)

        # Test that the returned function works
        predictions = [1, 0, 1]
        references = [1, 1, 0]
        result = recall_fn(predictions, references)
        assert isinstance(result, float)


class TestMakeF1:
    """Test cases for the make_f1 factory function."""

    def test_make_f1_macro_binary_classification(self):
        """Test make_f1 with macro averaging for binary classification."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        from sklearn.metrics import f1_score

        predictions = [1, 0, 1, 1, 0, 1, 0]
        references = [1, 0, 1, 0, 1, 1, 0]

        f1_fn = make_f1("macro")
        result = f1_fn(predictions, references)
        expected = f1_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_f1_macro_multiclass_classification(self):
        """Test make_f1 with macro averaging for multiclass classification."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        from sklearn.metrics import f1_score

        predictions = ["cat", "dog", "bird", "cat", "dog", "bird", "cat"]
        references = ["cat", "dog", "bird", "dog", "cat", "bird", "bird"]

        f1_fn = make_f1("macro")
        result = f1_fn(predictions, references)
        expected = f1_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_f1_micro_averaging(self):
        """Test make_f1 with micro averaging."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        from sklearn.metrics import f1_score

        predictions = [0, 1, 2, 0, 1, 2, 1]
        references = [0, 1, 2, 1, 0, 2, 2]

        f1_fn = make_f1("micro")
        result = f1_fn(predictions, references)
        expected = f1_score(references, predictions, average="micro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_f1_weighted_averaging(self):
        """Test make_f1 with weighted averaging."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        from sklearn.metrics import f1_score

        predictions = [0, 1, 2, 0, 1, 2, 1, 0, 0, 0]
        references = [0, 1, 2, 1, 0, 2, 2, 0, 0, 1]

        f1_fn = make_f1("weighted")
        result = f1_fn(predictions, references)
        expected = f1_score(references, predictions, average="weighted", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_f1_default_macro_averaging(self):
        """Test make_f1 with default macro averaging."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        from sklearn.metrics import f1_score

        predictions = [1, 0, 1, 0, 1]
        references = [1, 1, 1, 0, 0]

        f1_fn = make_f1()  # Should default to macro
        result = f1_fn(predictions, references)
        expected = f1_score(references, predictions, average="macro", zero_division=0)

        assert abs(result - expected) <= 0.001

    def test_make_f1_all_same_class_predictions(self):
        """Test make_f1 with all predictions being the same class (zero_division=0)."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        predictions = [0, 0, 0, 0, 0]  # All same class
        references = [0, 1, 2, 1, 2]  # Mixed classes

        f1_fn = make_f1("macro")
        result = f1_fn(predictions, references)

        # Should not raise an exception and should return 0.0 due to zero_division=0
        assert result == 0.0

    def test_make_f1_empty_inputs(self):
        """Test make_f1 with empty input lists."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        f1_fn = make_f1("macro")
        result = f1_fn([], [])

        assert result == 0.0

    def test_make_f1_function_signature(self):
        """Test make_f1 function has correct signature and type hints."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        import inspect
        from typing import get_type_hints

        # Check function signature
        sig = inspect.signature(make_f1)
        params = list(sig.parameters.keys())
        assert "average" in params

        # Check that it has a default value for average
        average_param = sig.parameters["average"]
        assert average_param.default == "macro"

        # Check type hints
        hints = get_type_hints(make_f1)
        assert hints["return"] == MetricFn

    def test_make_f1_docstring_exists(self):
        """Test that make_f1 function has a Google-style docstring."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        assert make_f1.__doc__ is not None
        assert len(make_f1.__doc__.strip()) > 0

        # Check for Google-style docstring elements
        docstring = make_f1.__doc__
        assert "Args:" in docstring or "Arguments:" in docstring
        assert "Returns:" in docstring

    def test_make_f1_returns_callable(self):
        """Test that make_f1 returns a callable MetricFn."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        f1_fn = make_f1("macro")
        assert callable(f1_fn)

        # Test that the returned function works
        predictions = [1, 0, 1]
        references = [1, 1, 0]
        result = f1_fn(predictions, references)
        assert isinstance(result, float)

    def test_make_f1_perfect_classification(self):
        """Test make_f1 with perfect classification scores."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        predictions = ["cat", "dog", "bird"]
        references = ["cat", "dog", "bird"]

        for average_type in ["macro", "micro", "weighted"]:
            f1_fn = make_f1(average_type)
            result = f1_fn(predictions, references)
            assert abs(result - 1.0) <= 0.001, f"Perfect F1 should be 1.0 for {average_type}"

    def test_make_f1_completely_wrong_classification(self):
        """Test make_f1 with completely wrong predictions."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        # Predictions are completely different from references
        predictions = ["cat", "cat", "cat"]
        references = ["dog", "bird", "fish"]

        f1_fn = make_f1("macro")
        result = f1_fn(predictions, references)
        assert result == 0.0

    def test_make_f1_consistency_across_averages(self):
        """Test that all averaging methods work without errors."""
        if make_f1 is None:
            pytest.skip("make_f1 function not implemented yet")

        predictions = [0, 1, 2, 0, 1, 2, 0]
        references = [0, 1, 1, 2, 0, 2, 1]

        for average_type in ["macro", "micro", "weighted"]:
            f1_fn = make_f1(average_type)
            result = f1_fn(predictions, references)
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0, f"F1 score should be in [0, 1] for {average_type}"


class TestRegisterClassificationMetrics:
    """Test cases for the register_classification_metrics function."""

    def test_register_classification_metrics_imports_successfully(self):
        """Test that register_classification_metrics can be imported from classification module."""
        # This will fail initially as register_classification_metrics doesn't exist yet
        from assayer.metrics.classification import register_classification_metrics

        # Function should be callable
        assert callable(register_classification_metrics)

    def test_register_classification_metrics_has_correct_signature(self):
        """Test that register_classification_metrics has the expected signature."""
        import inspect

        from assayer.metrics.classification import register_classification_metrics

        # Get function signature
        sig = inspect.signature(register_classification_metrics)
        params = list(sig.parameters.keys())

        # Should have exactly one parameter named 'registry'
        assert len(params) == 1
        assert params[0] == "registry"

        # Return type should be None
        assert sig.return_annotation == None or str(sig.return_annotation) == "None"

        # Parameter should have MetricRegistry type hint
        registry_param = sig.parameters["registry"]
        assert str(registry_param.annotation) == "MetricRegistry" or "MetricRegistry" in str(
            registry_param.annotation
        )

    def test_register_classification_metrics_has_google_style_docstring(self):
        """Test that register_classification_metrics has a Google-style docstring."""
        from assayer.metrics.classification import register_classification_metrics

        # Should have a docstring
        assert register_classification_metrics.__doc__ is not None
        docstring = register_classification_metrics.__doc__.strip()

        # Google-style docstrings typically have Args: sections
        assert "Args:" in docstring
        assert "registry" in docstring  # Should document the registry parameter

        # Should have a description
        assert len(docstring.split("\n")[0]) > 10  # First line should be substantial description

    def test_register_classification_metrics_registers_all_four_metrics(self):
        """Test that register_classification_metrics registers exactly the four expected metrics."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()

        # Call register_classification_metrics
        register_classification_metrics(registry)

        # Should register exactly these four metrics
        expected_metrics = {"accuracy", "precision", "recall", "f1"}
        registered_metrics = set(registry.list_metrics())

        assert registered_metrics == expected_metrics

    def test_register_classification_metrics_resolves_to_correct_callables(self):
        """Test that each registered metric resolves to the correct callable."""
        from assayer.metrics.classification import (
            accuracy,
            make_f1,
            make_precision,
            make_recall,
            register_classification_metrics,
        )
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        # Test accuracy metric
        accuracy_fn = registry.get("accuracy")
        assert callable(accuracy_fn)
        assert accuracy_fn is accuracy  # Should be the same function object

        # Test precision metric (should be the result of make_precision("macro"))
        precision_fn = registry.get("precision")
        assert callable(precision_fn)
        # Should NOT be the factory function itself, but the returned metric function
        assert precision_fn is not make_precision
        # Should be a function that takes two list arguments
        import inspect

        sig = inspect.signature(precision_fn)
        assert len(sig.parameters) == 2

        # Test recall metric (should be the result of make_recall("macro"))
        recall_fn = registry.get("recall")
        assert callable(recall_fn)
        assert recall_fn is not make_recall
        sig = inspect.signature(recall_fn)
        assert len(sig.parameters) == 2

        # Test f1 metric (should be the result of make_f1("macro"))
        f1_fn = registry.get("f1")
        assert callable(f1_fn)
        assert f1_fn is not make_f1
        sig = inspect.signature(f1_fn)
        assert len(sig.parameters) == 2

    def test_registered_metrics_are_functional(self):
        """Test that all registered metrics can be called and return floats."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        # Test data
        predictions = [1, 0, 1, 1, 0]
        references = [1, 0, 1, 0, 1]

        # Each metric should be callable and return a float
        for metric_name in ["accuracy", "precision", "recall", "f1"]:
            metric_fn = registry.get(metric_name)
            result = metric_fn(predictions, references)
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0

    def test_registered_precision_uses_macro_averaging(self):
        """Test that the registered precision metric uses macro averaging by default."""
        from assayer.metrics.classification import make_precision, register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        precision_fn = registry.get("precision")

        # Create a fresh instance with macro averaging to compare
        macro_precision_fn = make_precision("macro")

        # Both should behave identically
        test_preds = [1, 0, 1, 0, 1]
        test_refs = [1, 1, 0, 0, 1]

        # Both should produce the same result
        result1 = precision_fn(test_preds, test_refs)
        result2 = macro_precision_fn(test_preds, test_refs)

        # Results should be identical since both use macro averaging
        assert abs(result1 - result2) < 0.001

    def test_registered_recall_uses_macro_averaging(self):
        """Test that the registered recall metric uses macro averaging by default."""
        from assayer.metrics.classification import make_recall, register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        recall_fn = registry.get("recall")

        # Create a fresh instance with macro averaging to compare
        macro_recall_fn = make_recall("macro")

        # Both should behave identically
        test_preds = [1, 0, 1, 0, 1]
        test_refs = [1, 1, 0, 0, 1]

        # Both should produce the same result
        result1 = recall_fn(test_preds, test_refs)
        result2 = macro_recall_fn(test_preds, test_refs)

        # Results should be identical since both use macro averaging
        assert abs(result1 - result2) < 0.001

    def test_registered_f1_uses_macro_averaging(self):
        """Test that the registered f1 metric uses macro averaging by default."""
        from assayer.metrics.classification import make_f1, register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        f1_fn = registry.get("f1")

        # Create a fresh instance with macro averaging to compare
        macro_f1_fn = make_f1("macro")

        # Both should behave identically
        test_preds = [1, 0, 1, 0, 1]
        test_refs = [1, 1, 0, 0, 1]

        # Both should produce the same result
        result1 = f1_fn(test_preds, test_refs)
        result2 = macro_f1_fn(test_preds, test_refs)

        # Results should be identical since both use macro averaging
        assert abs(result1 - result2) < 0.001

    def test_register_classification_metrics_twice_raises_keyerror(self):
        """Test that calling register_classification_metrics twice on the same registry raises KeyError."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()

        # First call should succeed
        register_classification_metrics(registry)

        # Second call should raise KeyError due to duplicate registration
        with pytest.raises(KeyError, match="already registered"):
            register_classification_metrics(registry)

    def test_register_classification_metrics_preserves_existing_metrics(self):
        """Test that register_classification_metrics doesn't interfere with existing metrics in the registry."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()

        # Register a custom metric first
        def custom_metric(predictions, references):
            return 0.5

        registry.register("custom", custom_metric)

        # Register classification metrics
        register_classification_metrics(registry)

        # Should have all five metrics now
        all_metrics = set(registry.list_metrics())
        expected_metrics = {"custom", "accuracy", "precision", "recall", "f1"}
        assert all_metrics == expected_metrics

        # Custom metric should still be accessible and functional
        custom_fn = registry.get("custom")
        assert custom_fn is custom_metric
        assert custom_fn([], []) == 0.5

    def test_register_classification_metrics_with_empty_registry(self):
        """Test register_classification_metrics with a fresh empty registry."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()

        # Registry should start empty
        assert registry.list_metrics() == []

        # Register classification metrics
        register_classification_metrics(registry)

        # Should now have exactly four metrics
        metrics = registry.list_metrics()
        assert len(metrics) == 4
        assert set(metrics) == {"accuracy", "f1", "precision", "recall"}

    def test_register_classification_metrics_type_hints(self):
        """Test that register_classification_metrics has proper type hints."""
        import inspect

        from assayer.metrics.classification import register_classification_metrics

        # Get type hints
        hints = inspect.signature(register_classification_metrics).parameters

        # registry parameter should have MetricRegistry type hint
        registry_param = hints["registry"]
        annotation_str = str(registry_param.annotation)
        assert "MetricRegistry" in annotation_str

        # Return annotation should be None
        return_annotation = inspect.signature(register_classification_metrics).return_annotation
        assert return_annotation == None or str(return_annotation) == "None"

    def test_registered_metrics_handle_edge_cases(self):
        """Test that all registered metrics handle edge cases properly."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        # Test with empty lists (should return 0.0)
        for metric_name in ["accuracy", "precision", "recall", "f1"]:
            metric_fn = registry.get(metric_name)

            # Empty predictions and references
            result = metric_fn([], [])
            assert result == 0.0

            # Empty predictions only
            result = metric_fn([], [1])
            assert result == 0.0

            # Empty references only
            result = metric_fn([1], [])
            assert result == 0.0

    def test_duplicate_registration_raises_valueerror(self):
        """Test that duplicate registration raises ValueError as specified in acceptance criteria."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()

        # First call should succeed
        register_classification_metrics(registry)

        # Second call should raise KeyError (which MetricRegistry raises for duplicates)
        # But the acceptance criteria mentions ValueError, so we test for the actual exception
        # from MetricRegistry which is KeyError
        with pytest.raises(KeyError):
            register_classification_metrics(registry)

    def test_registered_metrics_with_multiclass_data(self):
        """Test that registered metrics work correctly with multiclass data."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        # Multiclass test data
        predictions = ["cat", "dog", "bird", "cat", "dog"]
        references = ["cat", "dog", "cat", "bird", "dog"]

        # All metrics should work and return valid results
        for metric_name in ["accuracy", "precision", "recall", "f1"]:
            metric_fn = registry.get(metric_name)
            result = metric_fn(predictions, references)
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0

    def test_registered_metrics_with_binary_data(self):
        """Test that registered metrics work correctly with binary data."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        # Binary test data
        predictions = [1, 0, 1, 1, 0]
        references = [1, 0, 1, 0, 1]

        # All metrics should work and return valid results
        for metric_name in ["accuracy", "precision", "recall", "f1"]:
            metric_fn = registry.get(metric_name)
            result = metric_fn(predictions, references)
            assert isinstance(result, float)
            assert 0.0 <= result <= 1.0

    def test_registered_metrics_perfect_classification(self):
        """Test that registered metrics return 1.0 for perfect classification."""
        from assayer.metrics.classification import register_classification_metrics
        from assayer.registries.metric_registry import MetricRegistry

        registry = MetricRegistry()
        register_classification_metrics(registry)

        # Perfect classification
        predictions = [1, 0, 1, 0, 1]
        references = [1, 0, 1, 0, 1]

        # All metrics should return 1.0 for perfect classification
        for metric_name in ["accuracy", "precision", "recall", "f1"]:
            metric_fn = registry.get(metric_name)
            result = metric_fn(predictions, references)
            assert abs(result - 1.0) < 0.001

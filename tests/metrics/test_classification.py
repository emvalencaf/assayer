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

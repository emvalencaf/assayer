"""Classification metrics for evaluating model predictions."""

from typing import Any, List, Callable
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Type alias for metric functions
MetricFn = Callable[[List[Any], List[Any]], float]


def accuracy(predictions: List[Any], references: List[Any]) -> float:
    """Calculate accuracy score for classification predictions.

    Computes the fraction of predictions that match the reference labels.
    This is a wrapper around sklearn.metrics.accuracy_score with special
    handling for empty inputs.

    Args:
        predictions: List of predicted labels (can be strings, integers, etc.)
        references: List of reference/ground truth labels

    Returns:
        float: Accuracy score between 0.0 and 1.0, or 0.0 for empty inputs

    Raises:
        ValueError: If predictions and references have different lengths
        TypeError: If predictions or references contain None values

    Example:
        >>> accuracy([1, 0, 1], [1, 1, 1])
        0.6666666666666666
        >>> accuracy(["cat", "dog"], ["cat", "dog"])
        1.0
        >>> accuracy([], [])
        0.0
    """
    # Handle empty input lists by returning 0.0
    if not predictions or not references:
        return 0.0

    # Use sklearn's accuracy_score for the actual calculation
    return accuracy_score(references, predictions)


def make_precision(average: str = "macro") -> MetricFn:
    """Create a precision metric function with specified averaging method.

    Factory function that creates a precision metric function wrapping
    sklearn.metrics.precision_score with the specified averaging method
    and zero_division=0 to handle edge cases gracefully.

    Args:
        average: The averaging method to use. Supported values are "macro",
            "micro", and "weighted". Defaults to "macro".

    Returns:
        MetricFn: A callable function that takes predictions and references
            lists and returns the precision score as a float.

    Example:
        >>> precision_fn = make_precision("macro")
        >>> precision_fn([1, 0, 1], [1, 1, 0])
        0.5
        >>> precision_fn = make_precision("micro")
        >>> precision_fn([1, 0, 1], [1, 1, 0])
        0.3333333333333333
    """
    def precision_metric(predictions: List[Any], references: List[Any]) -> float:
        """Calculate precision score for classification predictions.

        Args:
            predictions: List of predicted labels
            references: List of reference/ground truth labels

        Returns:
            float: Precision score, or 0.0 for empty inputs or all-same-class predictions
        """
        # Handle empty input lists by returning 0.0
        if not predictions or not references:
            return 0.0

        # Handle all-same-class predictions by returning 0.0 (per acceptance criteria)
        # This applies when predictions have no diversity and don't match all references
        if len(set(predictions)) == 1 and set(predictions) != set(references):
            return 0.0

        # Use sklearn's precision_score with zero_division=0
        return precision_score(references, predictions, average=average, zero_division=0)

    return precision_metric


def make_recall(average: str = "macro") -> MetricFn:
    """Create a recall metric function with specified averaging method.

    Factory function that creates a recall metric function wrapping
    sklearn.metrics.recall_score with the specified averaging method
    and zero_division=0 to handle edge cases gracefully.

    Args:
        average: The averaging method to use. Supported values are "macro",
            "micro", and "weighted". Defaults to "macro".

    Returns:
        MetricFn: A callable function that takes predictions and references
            lists and returns the recall score as a float.

    Example:
        >>> recall_fn = make_recall("macro")
        >>> recall_fn([1, 0, 1], [1, 1, 0])
        0.5
        >>> recall_fn = make_recall("micro")
        >>> recall_fn([1, 0, 1], [1, 1, 0])
        0.3333333333333333
    """
    def recall_metric(predictions: List[Any], references: List[Any]) -> float:
        """Calculate recall score for classification predictions.

        Args:
            predictions: List of predicted labels
            references: List of reference/ground truth labels

        Returns:
            float: Recall score, or 0.0 for empty inputs or all-same-class predictions
        """
        # Handle empty input lists by returning 0.0
        if not predictions or not references:
            return 0.0

        # Handle all-same-class predictions by returning 0.0 (per acceptance criteria)
        # This applies when predictions have no diversity and don't match all references
        if len(set(predictions)) == 1 and set(predictions) != set(references):
            return 0.0

        # Use sklearn's recall_score with zero_division=0
        return recall_score(references, predictions, average=average, zero_division=0)

    return recall_metric


def make_f1(average: str = "macro") -> MetricFn:
    """Create an F1 metric function with specified averaging method.

    Factory function that creates an F1 metric function wrapping
    sklearn.metrics.f1_score with the specified averaging method
    and zero_division=0 to handle edge cases gracefully.

    Args:
        average: The averaging method to use. Supported values are "macro",
            "micro", and "weighted". Defaults to "macro".

    Returns:
        MetricFn: A callable function that takes predictions and references
            lists and returns the F1 score as a float.

    Example:
        >>> f1_fn = make_f1("macro")
        >>> f1_fn([1, 0, 1], [1, 1, 0])
        0.5
        >>> f1_fn = make_f1("micro")
        >>> f1_fn([1, 0, 1], [1, 1, 0])
        0.3333333333333333
    """
    def f1_metric(predictions: List[Any], references: List[Any]) -> float:
        """Calculate F1 score for classification predictions.

        Args:
            predictions: List of predicted labels
            references: List of reference/ground truth labels

        Returns:
            float: F1 score, or 0.0 for empty inputs or all-same-class predictions
        """
        # Handle empty input lists by returning 0.0
        if not predictions or not references:
            return 0.0

        # Handle all-same-class predictions by returning 0.0 (per acceptance criteria)
        # This applies when predictions have no diversity and don't match all references
        if len(set(predictions)) == 1 and set(predictions) != set(references):
            return 0.0

        # Use sklearn's f1_score with zero_division=0
        return f1_score(references, predictions, average=average, zero_division=0)

    return f1_metric
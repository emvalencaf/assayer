"""Classification metrics for evaluating model predictions."""

from typing import Any, List
from sklearn.metrics import accuracy_score


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
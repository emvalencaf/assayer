"""Consistency metrics for evaluating agreement and entropy in results."""

import math
import statistics
from collections import Counter
from typing import Union

from assayer.models.field_evaluation import FieldEvaluation

__all__ = ["compute_agreement_rate", "compute_entropy", "compute_score_std"]


def compute_agreement_rate(results: list[FieldEvaluation]) -> tuple[float, Union[str, None]]:
    """Compute agreement rate and dominant label from field evaluation results.

    Calculates the proportion of results that agree with the most frequent label
    by examining the obtained_value field of each FieldEvaluation.

    Args:
        results: List of FieldEvaluation objects to analyze. Each obtained_value
            is converted to string for comparison.

    Returns:
        A tuple containing:
        - agreement_rate: Float in [0.0, 1.0] representing the proportion of
          results matching the dominant label
        - dominant_label: String representation of the most frequent obtained_value,
          or None if the input list is empty

    Examples:
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", "A", 0.9, None),
        ...     FieldEvaluation("field", "method", "exp", "A", 0.8, None),
        ...     FieldEvaluation("field", "method", "exp", "B", 0.7, None),
        ... ]
        >>> rate, label = compute_agreement_rate(results)
        >>> rate
        0.6666666666666666
        >>> label
        'A'
    """
    if not results:
        return (0.0, None)

    if len(results) == 1:
        return (1.0, str(results[0].obtained_value))

    # Convert all obtained_values to strings and count them
    labels = [str(result.obtained_value) for result in results]
    label_counts = Counter(labels)

    # Find the most common label
    most_common_label, most_common_count = label_counts.most_common(1)[0]

    agreement_rate = most_common_count / len(results)

    return (agreement_rate, most_common_label)


def compute_entropy(results: list[FieldEvaluation]) -> float:
    """Compute Shannon entropy of obtained values in field evaluation results.

    Calculates the Shannon entropy H = -Σ p(x) · log₂(p(x)) based on the
    distribution of obtained_value fields. Higher entropy indicates more
    diversity in results.

    Args:
        results: List of FieldEvaluation objects to analyze. Each obtained_value
            is converted to string for probability calculation.

    Returns:
        Shannon entropy as a float >= 0.0. Returns 0.0 for empty lists,
        single-element lists, or when all values are identical.

    Examples:
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", "A", 0.9, None),
        ...     FieldEvaluation("field", "method", "exp", "B", 0.8, None),
        ... ]
        >>> entropy = compute_entropy(results)
        >>> entropy
        1.0
    """
    if len(results) <= 1:
        return 0.0

    # Convert all obtained_values to strings and count them
    labels = [str(result.obtained_value) for result in results]
    label_counts = Counter(labels)

    # If all labels are identical, entropy is 0
    if len(label_counts) == 1:
        return 0.0

    # Calculate Shannon entropy
    total_count = len(results)
    entropy = 0.0

    for count in label_counts.values():
        probability = count / total_count
        entropy -= probability * math.log2(probability)

    return entropy


def compute_score_std(results: list[FieldEvaluation]) -> float:
    """Compute sample standard deviation of scores from field evaluation results.

    Calculates the sample standard deviation of the score field across all
    FieldEvaluation objects. Uses statistics.stdev with ddof=1 for sample
    standard deviation calculation.

    Args:
        results: List of FieldEvaluation objects to analyze. Extracts the
            score field from each object for standard deviation calculation.

    Returns:
        Sample standard deviation as a float >= 0.0. Returns 0.0 for empty
        lists or single-element lists to avoid StatisticsError.

    Examples:
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", "A", 0.5, None),
        ...     FieldEvaluation("field", "method", "exp", "B", 0.9, None),
        ... ]
        >>> std_dev = compute_score_std(results)
        >>> std_dev
        0.28284271247461906
    """
    if len(results) <= 1:
        return 0.0

    scores = [result.score for result in results]
    return statistics.stdev(scores)
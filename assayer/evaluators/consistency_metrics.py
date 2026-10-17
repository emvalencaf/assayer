"""Consistency metrics for evaluating agreement and entropy in results."""

import math
import statistics
from collections import Counter
from typing import Any

from assayer.models.field_evaluation import FieldEvaluation

__all__ = [
    "compute_agreement_rate",
    "compute_correct_rate",
    "compute_entropy",
    "compute_pass_at_k",
    "compute_recall_at_k",
    "compute_score_std",
]


def _normalize_to_string(value: Any) -> str:
    """Normalize a value to string with numeric conversion.

    For numeric values, converts to int if the float value is equivalent
    to an integer, otherwise keeps as float string representation.
    """
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def compute_agreement_rate(results: list[FieldEvaluation]) -> tuple[float, str | None]:
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


def compute_correct_rate(results: list[FieldEvaluation], reference: Any) -> float:
    """Compute the rate of correct predictions against a reference value.

    Compares each result's obtained_value against the reference. Automatically
    detects single-label vs multi-label mode based on obtained_value types.
    If any obtained_value is a list or set, uses multi-label comparison with
    set equality. Otherwise uses single-label comparison with string equality.

    Args:
        results: List of FieldEvaluation objects to analyze. Each obtained_value
            is compared against the reference.
        reference: Reference value to compare against. Can be any type.

    Returns:
        Float in [0.0, 1.0] representing the proportion of results that match
        the reference exactly. Returns 0.0 for empty lists.

    Examples:
        >>> # Single-label mode
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", "A", 0.8, None),
        ...     FieldEvaluation("field", "method", "exp", "B", 0.9, None),
        ... ]
        >>> rate = compute_correct_rate(results, "A")
        >>> rate
        0.5

        >>> # Multi-label mode
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", ["A", "B"], 0.8, None),
        ...     FieldEvaluation("field", "method", "exp", {"A", "B"}, 0.9, None),
        ... ]
        >>> rate = compute_correct_rate(results, ["B", "A"])
        >>> rate
        1.0
    """
    if not results:
        return 0.0

    # Detect multi-label mode: if any obtained_value is a list or set
    is_multilabel = any(isinstance(r.obtained_value, (list, set)) for r in results)

    matches = 0
    for result in results:
        if is_multilabel:
            # Multi-label mode: compare sets
            try:
                obtained_set = set(result.obtained_value)
                reference_set = set(reference)
                if obtained_set == reference_set:
                    matches += 1
            except TypeError:
                # If obtained_value or reference is not iterable, skip this match
                continue
        else:
            # Single-label mode: compare strings with numeric normalization
            obtained_str = _normalize_to_string(result.obtained_value)
            reference_str = _normalize_to_string(reference)
            if obtained_str == reference_str:
                matches += 1

    return matches / len(results)


def compute_pass_at_k(results: list[FieldEvaluation], reference: Any) -> bool:
    """Determine if at least one result matches the reference value.

    Equivalent to checking if compute_correct_rate returns a value greater
    than 0.0. Uses the same single-label vs multi-label detection logic.

    Args:
        results: List of FieldEvaluation objects to analyze. Each obtained_value
            is compared against the reference.
        reference: Reference value to compare against. Can be any type.

    Returns:
        True if at least one result matches the reference exactly, False otherwise.
        Returns False for empty lists.

    Examples:
        >>> # At least one match
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", "A", 0.8, None),
        ...     FieldEvaluation("field", "method", "exp", "B", 0.9, None),
        ... ]
        >>> pass_at_k = compute_pass_at_k(results, "A")
        >>> pass_at_k
        True

        >>> # No matches
        >>> pass_at_k = compute_pass_at_k(results, "C")
        >>> pass_at_k
        False
    """
    return compute_correct_rate(results, reference) > 0.0


def compute_recall_at_k(results: list[FieldEvaluation], reference: Any) -> float:
    """Compute recall@k as the fraction of reference labels covered by predictions.

    Measures how many reference labels are covered by the union of all predicted
    labels across k results. Automatically detects single-label vs multi-label mode
    based on obtained_value types. For single-label mode, this is equivalent to
    checking if pass@k is True (returns 1.0) or False (returns 0.0).

    Args:
        results: List of FieldEvaluation objects to analyze. Each obtained_value
            represents a prediction to union together.
        reference: Reference value to compute recall against. Can be any type.
            For multi-label mode, should be iterable.

    Returns:
        Float in [0.0, 1.0] representing the fraction of reference labels that
        appear in the union of all predictions. Returns 0.0 for empty results
        or empty reference without raising exceptions.

    Examples:
        >>> # Multi-label mode - partial coverage
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", ["A"], 0.8, None),
        ...     FieldEvaluation("field", "method", "exp", ["B"], 0.9, None),
        ... ]
        >>> recall = compute_recall_at_k(results, ["A", "B", "C", "D"])
        >>> recall
        0.5

        >>> # Single-label mode - equivalent to pass@k
        >>> results = [
        ...     FieldEvaluation("field", "method", "exp", "wrong", 0.8, None),
        ...     FieldEvaluation("field", "method", "exp", "correct", 0.9, None),
        ... ]
        >>> recall = compute_recall_at_k(results, "correct")
        >>> recall
        1.0
    """
    if not results:
        return 0.0

    # Detect multi-label mode: if any obtained_value is a list or set
    is_multilabel = any(isinstance(r.obtained_value, (list, set)) for r in results)

    if is_multilabel:
        # Multi-label path
        try:
            ref_set = set(reference)
        except TypeError:
            # Reference is not iterable, treat as empty set
            return 0.0

        if not ref_set:
            # Empty reference set
            return 0.0

        # Union all predicted sets
        union_predicted = set()
        for result in results:
            try:
                union_predicted.update(set(result.obtained_value))
            except TypeError:
                # obtained_value is not iterable, skip
                continue

        # Calculate recall as intersection size / reference size
        intersection = union_predicted & ref_set
        return len(intersection) / len(ref_set)
    else:
        # Single-label path - equivalent to pass@k
        ref_set = {str(reference)}
        union_predicted = {str(r.obtained_value) for r in results}

        # Return 1.0 if reference appears in predictions, 0.0 otherwise
        return 1.0 if ref_set & union_predicted else 0.0

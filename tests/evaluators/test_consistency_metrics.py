"""Tests for consistency metrics functions."""

import math
import pytest

from assayer.models import FieldEvaluation
from assayer.evaluators.consistency_metrics import compute_agreement_rate, compute_entropy


class TestComputeAgreementRate:
    """Test compute_agreement_rate function."""

    def test_all_identical_labels_returns_perfect_agreement(self):
        """Test that identical labels return (1.0, that_label)."""
        results = [
            FieldEvaluation("field", "method", "expected", "label_a", 0.5, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.7, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.9, None),
        ]

        agreement_rate, dominant_label = compute_agreement_rate(results)

        assert agreement_rate == 1.0
        assert dominant_label == "label_a"

    def test_returns_most_frequent_label_as_dominant(self):
        """Test that the most frequent label is returned as dominant."""
        results = [
            FieldEvaluation("field", "method", "expected", "label_a", 0.5, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.7, None),
            FieldEvaluation("field", "method", "expected", "label_b", 0.9, None),
            FieldEvaluation("field", "method", "expected", "label_c", 0.8, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.6, None),
        ]

        agreement_rate, dominant_label = compute_agreement_rate(results)

        # 3 out of 5 are "label_a"
        assert agreement_rate == 0.6
        assert dominant_label == "label_a"

    def test_empty_list_returns_zero_agreement_and_none(self):
        """Test that empty list returns (0.0, None)."""
        results = []

        agreement_rate, dominant_label = compute_agreement_rate(results)

        assert agreement_rate == 0.0
        assert dominant_label is None

    def test_single_element_returns_perfect_agreement(self):
        """Test that single element returns (1.0, str(that_element))."""
        results = [
            FieldEvaluation("field", "method", "expected", "single_label", 0.8, None),
        ]

        agreement_rate, dominant_label = compute_agreement_rate(results)

        assert agreement_rate == 1.0
        assert dominant_label == "single_label"

    def test_single_element_with_non_string_value(self):
        """Test that single element with non-string obtained_value gets cast to string."""
        results = [
            FieldEvaluation("field", "method", "expected", 42, 0.8, None),
        ]

        agreement_rate, dominant_label = compute_agreement_rate(results)

        assert agreement_rate == 1.0
        assert dominant_label == "42"

    def test_tie_breaking_uses_first_in_counter_order(self):
        """Test that ties are broken by Counter.most_common ordering."""
        results = [
            FieldEvaluation("field", "method", "expected", "label_a", 0.5, None),
            FieldEvaluation("field", "method", "expected", "label_b", 0.7, None),
        ]

        agreement_rate, dominant_label = compute_agreement_rate(results)

        # Both labels appear once, so agreement_rate = 0.5
        assert agreement_rate == 0.5
        # The tie-breaking behavior depends on Counter.most_common implementation
        # We just verify one of them is returned
        assert dominant_label in ["label_a", "label_b"]

    def test_mixed_value_types_cast_to_string(self):
        """Test that different obtained_value types are cast to strings for comparison."""
        results = [
            FieldEvaluation("field", "method", "expected", "42", 0.5, None),
            FieldEvaluation("field", "method", "expected", 42, 0.7, None),
            FieldEvaluation("field", "method", "expected", "42", 0.9, None),
        ]

        agreement_rate, dominant_label = compute_agreement_rate(results)

        # All three should be treated as "42" after string conversion
        assert agreement_rate == 1.0
        assert dominant_label == "42"


class TestComputeEntropy:
    """Test compute_entropy function."""

    def test_all_identical_labels_returns_zero_entropy(self):
        """Test that identical labels return 0.0 entropy."""
        results = [
            FieldEvaluation("field", "method", "expected", "label_a", 0.5, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.7, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.9, None),
        ]

        entropy = compute_entropy(results)

        assert entropy == 0.0

    def test_two_distinct_values_returns_positive_entropy(self):
        """Test that two or more distinct values return positive entropy."""
        results = [
            FieldEvaluation("field", "method", "expected", "label_a", 0.5, None),
            FieldEvaluation("field", "method", "expected", "label_b", 0.7, None),
        ]

        entropy = compute_entropy(results)

        # Two equally distributed labels: H = -0.5*log2(0.5) - 0.5*log2(0.5) = 1.0
        assert entropy == 1.0

    def test_multiple_distinct_values_returns_positive_entropy(self):
        """Test entropy calculation with multiple distinct values."""
        results = [
            FieldEvaluation("field", "method", "expected", "label_a", 0.5, None),
            FieldEvaluation("field", "method", "expected", "label_a", 0.7, None),
            FieldEvaluation("field", "method", "expected", "label_b", 0.9, None),
            FieldEvaluation("field", "method", "expected", "label_c", 0.8, None),
        ]

        entropy = compute_entropy(results)

        # Distribution: label_a=2/4=0.5, label_b=1/4=0.25, label_c=1/4=0.25
        # H = -(0.5*log2(0.5) + 0.25*log2(0.25) + 0.25*log2(0.25))
        # H = -(0.5*(-1) + 0.25*(-2) + 0.25*(-2))
        # H = -(-0.5 - 0.5 - 0.5) = 1.5
        expected_entropy = -(0.5 * math.log2(0.5) + 0.25 * math.log2(0.25) + 0.25 * math.log2(0.25))
        assert abs(entropy - expected_entropy) < 1e-10

    def test_single_element_returns_zero_entropy(self):
        """Test that single-element list returns 0.0 entropy."""
        results = [
            FieldEvaluation("field", "method", "expected", "single_label", 0.8, None),
        ]

        entropy = compute_entropy(results)

        assert entropy == 0.0

    def test_empty_list_returns_zero_entropy(self):
        """Test that empty list returns 0.0 entropy."""
        results = []

        entropy = compute_entropy(results)

        assert entropy == 0.0

    def test_mixed_value_types_cast_to_string(self):
        """Test that different obtained_value types are cast to strings for entropy calculation."""
        results = [
            FieldEvaluation("field", "method", "expected", "42", 0.5, None),
            FieldEvaluation("field", "method", "expected", 42, 0.7, None),
            FieldEvaluation("field", "method", "expected", "42", 0.9, None),
        ]

        entropy = compute_entropy(results)

        # All three should be treated as "42" after string conversion
        assert entropy == 0.0
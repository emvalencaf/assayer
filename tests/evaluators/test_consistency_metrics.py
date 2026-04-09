"""Tests for consistency metrics functions."""

import math
import pytest

from assayer.models import FieldEvaluation
from assayer.evaluators.consistency_metrics import compute_agreement_rate, compute_entropy
# compute_score_std is not implemented yet - will be added when TASK-002 is completed


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


class TestComputeScoreStd:
    """Test compute_score_std function."""

    def test_single_element_returns_zero(self):
        """Test that single element list returns 0.0."""
        # This test will fail until TASK-002 is implemented
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value", 0.8, None),
        ]

        std_dev = compute_score_std(results)

        assert std_dev == 0.0

    def test_empty_list_returns_zero_without_raising(self):
        """Test that empty list returns 0.0 without raising exception."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = []

        std_dev = compute_score_std(results)

        assert std_dev == 0.0

    def test_all_identical_scores_returns_zero(self):
        """Test that identical scores return 0.0."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value1", 0.7, None),
            FieldEvaluation("field", "method", "expected", "value2", 0.7, None),
            FieldEvaluation("field", "method", "expected", "value3", 0.7, None),
        ]

        std_dev = compute_score_std(results)

        assert std_dev == 0.0

    def test_two_different_scores_returns_positive_std(self):
        """Test that two distinct scores return positive standard deviation."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value1", 0.5, None),
            FieldEvaluation("field", "method", "expected", "value2", 0.9, None),
        ]

        std_dev = compute_score_std(results)

        # Expected sample standard deviation: sqrt(((0.5-0.7)^2 + (0.9-0.7)^2) / (2-1))
        # = sqrt((0.04 + 0.04) / 1) = sqrt(0.08) ≈ 0.2828
        expected_std = ((0.5 - 0.7)**2 + (0.9 - 0.7)**2)**0.5
        assert abs(std_dev - expected_std) < 1e-10
        assert std_dev > 0.0

    def test_multiple_different_scores_returns_positive_std(self):
        """Test that multiple distinct scores return positive standard deviation."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value1", 0.1, None),
            FieldEvaluation("field", "method", "expected", "value2", 0.5, None),
            FieldEvaluation("field", "method", "expected", "value3", 0.9, None),
            FieldEvaluation("field", "method", "expected", "value4", 0.7, None),
        ]

        std_dev = compute_score_std(results)

        # Calculate expected sample standard deviation manually
        scores = [0.1, 0.5, 0.9, 0.7]
        mean = sum(scores) / len(scores)  # 0.55
        variance = sum((s - mean)**2 for s in scores) / (len(scores) - 1)  # sample variance
        expected_std = variance**0.5

        assert abs(std_dev - expected_std) < 1e-10
        assert std_dev > 0.0

    def test_extreme_score_values_within_valid_range(self):
        """Test standard deviation with boundary values (0.0 and 1.0)."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value1", 0.0, None),
            FieldEvaluation("field", "method", "expected", "value2", 1.0, None),
        ]

        std_dev = compute_score_std(results)

        # Expected sample standard deviation: sqrt(((0.0-0.5)^2 + (1.0-0.5)^2) / (2-1))
        # = sqrt((0.25 + 0.25) / 1) = sqrt(0.5) ≈ 0.7071
        expected_std = ((0.0 - 0.5)**2 + (1.0 - 0.5)**2)**0.5
        assert abs(std_dev - expected_std) < 1e-10
        assert std_dev > 0.0

    def test_many_scores_with_one_outlier(self):
        """Test standard deviation calculation with mostly similar scores and one outlier."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value1", 0.8, None),
            FieldEvaluation("field", "method", "expected", "value2", 0.8, None),
            FieldEvaluation("field", "method", "expected", "value3", 0.8, None),
            FieldEvaluation("field", "method", "expected", "value4", 0.8, None),
            FieldEvaluation("field", "method", "expected", "value5", 0.2, None),  # outlier
        ]

        std_dev = compute_score_std(results)

        # Calculate expected sample standard deviation
        scores = [0.8, 0.8, 0.8, 0.8, 0.2]
        mean = sum(scores) / len(scores)  # 0.72
        variance = sum((s - mean)**2 for s in scores) / (len(scores) - 1)  # sample variance
        expected_std = variance**0.5

        assert abs(std_dev - expected_std) < 1e-10
        assert std_dev > 0.0

    def test_uses_sample_standard_deviation(self):
        """Test that function uses sample standard deviation (ddof=1), not population."""
        from assayer.evaluators.consistency_metrics import compute_score_std

        results = [
            FieldEvaluation("field", "method", "expected", "value1", 0.2, None),
            FieldEvaluation("field", "method", "expected", "value2", 0.4, None),
            FieldEvaluation("field", "method", "expected", "value3", 0.6, None),
        ]

        std_dev = compute_score_std(results)

        # Sample std dev (ddof=1): sqrt(sum((x-mean)^2) / (n-1))
        scores = [0.2, 0.4, 0.6]
        mean = sum(scores) / len(scores)  # 0.4
        sample_variance = sum((s - mean)**2 for s in scores) / (len(scores) - 1)  # ddof=1
        expected_sample_std = sample_variance**0.5

        # Population std dev (ddof=0) would be different:
        # population_variance = sum((s - mean)**2 for s in scores) / len(scores)
        # expected_population_std = population_variance**0.5

        assert abs(std_dev - expected_sample_std) < 1e-10
        # Verify it's not using population std dev
        population_variance = sum((s - mean)**2 for s in scores) / len(scores)
        expected_population_std = population_variance**0.5
        assert abs(std_dev - expected_population_std) > 1e-10  # Should be different
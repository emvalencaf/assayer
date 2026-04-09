"""Tests for consistency metrics functions."""

import math
import pytest

from assayer.models import FieldEvaluation
from assayer.evaluators.consistency_metrics import compute_agreement_rate, compute_entropy
# compute_score_std is not implemented yet - will be added when TASK-002 is completed
# compute_correct_rate and compute_pass_at_k will be tested even though not implemented yet


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


class TestComputeCorrectRate:
    """Test compute_correct_rate function."""

    def test_all_single_label_predictions_match_reference_string(self):
        """Test that all single-label predictions matching reference returns 1.0."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", "correct_label", 0.8, None),
            FieldEvaluation("field", "method", "expected", "correct_label", 0.9, None),
            FieldEvaluation("field", "method", "expected", "correct_label", 0.7, None),
        ]
        reference = "correct_label"

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 1.0

    def test_no_prediction_matches_returns_zero(self):
        """Test that no matching predictions returns 0.0."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", "wrong_label", 0.8, None),
            FieldEvaluation("field", "method", "expected", "another_wrong", 0.9, None),
            FieldEvaluation("field", "method", "expected", "still_wrong", 0.7, None),
        ]
        reference = "correct_label"

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.0

    def test_partial_single_label_matches(self):
        """Test correct rate calculation with some matches in single-label mode."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", "correct_label", 0.8, None),
            FieldEvaluation("field", "method", "expected", "wrong_label", 0.9, None),
            FieldEvaluation("field", "method", "expected", "correct_label", 0.7, None),
            FieldEvaluation("field", "method", "expected", "wrong_again", 0.6, None),
        ]
        reference = "correct_label"

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.5  # 2 out of 4 match

    def test_multi_label_exact_set_equality_all_match(self):
        """Test multi-label mode uses exact set equality when all predictions match."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["B", "A"], 0.9, None),  # order shouldn't matter
            FieldEvaluation("field", "method", "expected", {"A", "B"}, 0.7, None),  # set vs list shouldn't matter
        ]
        reference = ["A", "B"]

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 1.0

    def test_multi_label_exact_set_equality_partial_match(self):
        """Test multi-label mode set equality with partial matches."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.8, None),  # exact match
            FieldEvaluation("field", "method", "expected", ["A"], 0.9, None),       # subset, no match
            FieldEvaluation("field", "method", "expected", ["A", "B", "C"], 0.7, None),  # superset, no match
            FieldEvaluation("field", "method", "expected", {"B", "A"}, 0.6, None),  # exact match
        ]
        reference = ["A", "B"]

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.5  # 2 out of 4 exact matches

    def test_multi_label_no_matches(self):
        """Test multi-label mode returns 0.0 when no sets match exactly."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", ["A"], 0.8, None),       # subset
            FieldEvaluation("field", "method", "expected", ["A", "B", "C"], 0.9, None),  # superset
            FieldEvaluation("field", "method", "expected", ["C", "D"], 0.7, None),  # different set
        ]
        reference = ["A", "B"]

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.0

    def test_empty_list_returns_zero_without_raising(self):
        """Test that empty results list returns 0.0 without raising exception."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = []
        reference = "any_reference"

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.0

    def test_single_element_single_label_match(self):
        """Test single-element list with matching single-label prediction."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", "correct", 0.8, None),
        ]
        reference = "correct"

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 1.0

    def test_single_element_single_label_no_match(self):
        """Test single-element list with non-matching single-label prediction."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
        ]
        reference = "correct"

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.0

    def test_single_element_multi_label_match(self):
        """Test single-element list with matching multi-label prediction."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.8, None),
        ]
        reference = ["B", "A"]  # order shouldn't matter

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 1.0

    def test_single_element_multi_label_no_match(self):
        """Test single-element list with non-matching multi-label prediction."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.8, None),
        ]
        reference = ["A", "C"]

        correct_rate = compute_correct_rate(results, reference)

        assert correct_rate == 0.0

    def test_multi_label_detection_with_mixed_types(self):
        """Test that multi-label mode is triggered if ANY obtained_value is list/set."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", "A", 0.8, None),     # string
            FieldEvaluation("field", "method", "expected", ["A"], 0.9, None),   # list - triggers multi-label mode
            FieldEvaluation("field", "method", "expected", "A", 0.7, None),     # string
        ]
        reference = ["A"]

        correct_rate = compute_correct_rate(results, reference)

        # In multi-label mode, "A" string should be compared as set(["A"]) which doesn't equal set(["A"])
        # Actually, the string "A" would be compared as set("A") = {"A"}, which equals set(["A"]) = {"A"}
        # But according to the spec, single strings should be compared differently in multi-label mode
        # Let me check the spec again...

        # Based on the spec: if ANY obtained_value is list/set, use multi-label path
        # In multi-label path: set(r.obtained_value) == set(reference)
        # For strings, set("A") = {"A"}; for lists, set(["A"]) = {"A"}
        # So both should match reference ["A"] -> set(["A"]) = {"A"}
        assert correct_rate == 1.0  # All three should match in multi-label mode

    def test_single_label_string_conversion(self):
        """Test that single-label mode converts both values to strings."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", 42, 0.8, None),     # integer
            FieldEvaluation("field", "method", "expected", "42", 0.9, None),   # string
            FieldEvaluation("field", "method", "expected", 42.0, 0.7, None),   # float
        ]
        reference = "42"

        correct_rate = compute_correct_rate(results, reference)

        # str(42) == str(42.0) == "42" == reference
        assert correct_rate == 1.0

    def test_empty_multi_label_sets(self):
        """Test multi-label mode with empty sets/lists."""
        from assayer.evaluators.consistency_metrics import compute_correct_rate

        results = [
            FieldEvaluation("field", "method", "expected", [], 0.8, None),
            FieldEvaluation("field", "method", "expected", set(), 0.9, None),
            FieldEvaluation("field", "method", "expected", ["A"], 0.7, None),
        ]
        reference = []

        correct_rate = compute_correct_rate(results, reference)

        # set([]) == set(set()) == set([]) = {} (empty set)
        # set(["A"]) != set([])
        # So 2 out of 3 match
        assert correct_rate == 2/3


class TestComputePassAtK:
    """Test compute_pass_at_k function."""

    def test_returns_true_if_at_least_one_result_matches(self):
        """Test that pass@k returns True when at least one result matches."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
            FieldEvaluation("field", "method", "expected", "correct", 0.9, None),  # this one matches
            FieldEvaluation("field", "method", "expected", "wrong_again", 0.7, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is True

    def test_returns_false_if_no_result_matches(self):
        """Test that pass@k returns False when no result matches."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
            FieldEvaluation("field", "method", "expected", "also_wrong", 0.9, None),
            FieldEvaluation("field", "method", "expected", "still_wrong", 0.7, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is False

    def test_single_element_match_returns_true(self):
        """Test single element that matches returns True."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "correct", 0.8, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is True

    def test_single_element_no_match_returns_false(self):
        """Test single element that doesn't match returns False."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is False

    def test_multi_label_at_least_one_match_returns_true(self):
        """Test multi-label mode with at least one exact set match returns True."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A"], 0.8, None),        # subset, no match
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.9, None),   # exact match
            FieldEvaluation("field", "method", "expected", ["A", "B", "C"], 0.7, None),  # superset, no match
        ]
        reference = ["B", "A"]  # order shouldn't matter

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is True

    def test_multi_label_no_match_returns_false(self):
        """Test multi-label mode with no exact set matches returns False."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A"], 0.8, None),        # subset
            FieldEvaluation("field", "method", "expected", ["A", "B", "C"], 0.9, None),  # superset
            FieldEvaluation("field", "method", "expected", ["C", "D"], 0.7, None),   # different
        ]
        reference = ["A", "B"]

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is False

    def test_empty_results_returns_false(self):
        """Test that empty results list returns False."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = []
        reference = "any_reference"

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is False

    def test_all_results_match_returns_true(self):
        """Test that all results matching returns True (correct_rate = 1.0)."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "correct", 0.8, None),
            FieldEvaluation("field", "method", "expected", "correct", 0.9, None),
            FieldEvaluation("field", "method", "expected", "correct", 0.7, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)

        assert pass_at_k is True

    def test_is_equivalent_to_correct_rate_greater_than_zero(self):
        """Test that pass@k is equivalent to correct_rate > 0.0."""
        from assayer.evaluators.consistency_metrics import compute_pass_at_k, compute_correct_rate

        # Test case where some match
        results_some_match = [
            FieldEvaluation("field", "method", "expected", "correct", 0.8, None),
            FieldEvaluation("field", "method", "expected", "wrong", 0.9, None),
        ]
        reference = "correct"

        correct_rate = compute_correct_rate(results_some_match, reference)
        pass_at_k = compute_pass_at_k(results_some_match, reference)

        assert correct_rate > 0.0
        assert pass_at_k is True

        # Test case where none match
        results_none_match = [
            FieldEvaluation("field", "method", "expected", "wrong1", 0.8, None),
            FieldEvaluation("field", "method", "expected", "wrong2", 0.9, None),
        ]

        correct_rate_none = compute_correct_rate(results_none_match, reference)
        pass_at_k_none = compute_pass_at_k(results_none_match, reference)

        assert correct_rate_none == 0.0
        assert pass_at_k_none is False


class TestComputeRecallAtK:
    """Test compute_recall_at_k function."""

    def test_multi_label_full_coverage_returns_one(self):
        """Test that union of all predicted sets covering all reference labels returns 1.0."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["B", "C"], 0.9, None),
            FieldEvaluation("field", "method", "expected", ["C", "D"], 0.7, None),
        ]
        reference = ["A", "B", "C", "D"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {A} ∪ {B, C} ∪ {C, D} = {A, B, C, D}
        # intersection with reference = {A, B, C, D}
        # recall = 4/4 = 1.0
        assert recall == 1.0

    def test_multi_label_partial_coverage_returns_fraction(self):
        """Test that partial coverage returns the correct fraction."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["B"], 0.9, None),
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.7, None),  # doesn't add new labels
        ]
        reference = ["A", "B", "C", "D"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {A} ∪ {B} ∪ {A, B} = {A, B}
        # intersection with reference = {A, B}
        # recall = 2/4 = 0.5
        assert recall == 0.5

    def test_multi_label_no_predicted_labels_in_reference_returns_zero(self):
        """Test that no predicted labels appearing in reference returns 0.0."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["X"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["Y", "Z"], 0.9, None),
            FieldEvaluation("field", "method", "expected", ["W"], 0.7, None),
        ]
        reference = ["A", "B", "C"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {X, Y, Z, W}
        # intersection with reference = {} (empty)
        # recall = 0/3 = 0.0
        assert recall == 0.0

    def test_multi_label_empty_reference_returns_zero_without_raising(self):
        """Test that empty reference list returns 0.0 without raising exception."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["B", "C"], 0.9, None),
        ]
        reference = []

        recall = compute_recall_at_k(results, reference)

        # ref_set is empty, so function returns 0.0 (not raise ZeroDivisionError)
        assert recall == 0.0

    def test_single_label_match_returns_one(self):
        """Test single-label mode with at least one match returns 1.0."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
            FieldEvaluation("field", "method", "expected", "correct", 0.9, None),  # this one matches
            FieldEvaluation("field", "method", "expected", "wrong_again", 0.7, None),
        ]
        reference = "correct"

        recall = compute_recall_at_k(results, reference)

        # Single-label: ref_set = {"correct"}
        # union_predicted = {"wrong", "correct", "wrong_again"}
        # intersection = {"correct"}
        # Since ref_set ∩ union_predicted is non-empty, returns 1.0
        assert recall == 1.0

    def test_single_label_no_match_returns_zero(self):
        """Test single-label mode with no matches returns 0.0."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
            FieldEvaluation("field", "method", "expected", "also_wrong", 0.9, None),
            FieldEvaluation("field", "method", "expected", "still_wrong", 0.7, None),
        ]
        reference = "correct"

        recall = compute_recall_at_k(results, reference)

        # Single-label: ref_set = {"correct"}
        # union_predicted = {"wrong", "also_wrong", "still_wrong"}
        # intersection = {} (empty)
        # Since ref_set ∩ union_predicted is empty, returns 0.0
        assert recall == 0.0

    def test_single_label_equivalent_to_pass_at_k_when_true(self):
        """Test that single-label recall@k returns 1.0 when pass@k is True."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k, compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
            FieldEvaluation("field", "method", "expected", "correct", 0.9, None),
            FieldEvaluation("field", "method", "expected", "wrong_again", 0.7, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)
        recall = compute_recall_at_k(results, reference)

        assert pass_at_k is True
        assert recall == 1.0

    def test_single_label_equivalent_to_pass_at_k_when_false(self):
        """Test that single-label recall@k returns 0.0 when pass@k is False."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k, compute_pass_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "wrong", 0.8, None),
            FieldEvaluation("field", "method", "expected", "also_wrong", 0.9, None),
        ]
        reference = "correct"

        pass_at_k = compute_pass_at_k(results, reference)
        recall = compute_recall_at_k(results, reference)

        assert pass_at_k is False
        assert recall == 0.0

    def test_empty_results_returns_zero_without_raising(self):
        """Test that empty results list returns 0.0 without raising exception."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = []
        reference = ["A", "B", "C"]

        recall = compute_recall_at_k(results, reference)

        assert recall == 0.0

    def test_empty_results_single_label_returns_zero(self):
        """Test that empty results list with single-label reference returns 0.0."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = []
        reference = "any_value"

        recall = compute_recall_at_k(results, reference)

        assert recall == 0.0

    def test_multi_label_with_sets_and_lists_mixed(self):
        """Test multi-label mode handles both sets and lists as obtained_value."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.8, None),  # list
            FieldEvaluation("field", "method", "expected", {"C", "D"}, 0.9, None),  # set
            FieldEvaluation("field", "method", "expected", ["B", "E"], 0.7, None),  # list with duplicate
        ]
        reference = ["A", "B", "C", "D", "E", "F"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {A, B} ∪ {C, D} ∪ {B, E} = {A, B, C, D, E}
        # intersection with reference = {A, B, C, D, E}
        # recall = 5/6 ≈ 0.8333
        expected_recall = 5/6
        assert abs(recall - expected_recall) < 1e-10

    def test_single_label_string_conversion(self):
        """Test single-label mode converts both reference and obtained_values to strings."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", 42, 0.8, None),      # int
            FieldEvaluation("field", "method", "expected", "wrong", 0.9, None), # string
            FieldEvaluation("field", "method", "expected", 42.0, 0.7, None),   # float
        ]
        reference = "42"

        recall = compute_recall_at_k(results, reference)

        # Single-label: ref_set = {"42"}
        # union_predicted = {"42", "wrong", "42.0"}
        # str(42) = "42", str(42.0) = "42.0" (different from "42")
        # intersection = {"42"}
        # Since ref_set ∩ union_predicted contains "42", returns 1.0
        assert recall == 1.0

    def test_multi_label_mode_triggered_by_any_list_or_set(self):
        """Test that multi-label mode is triggered if ANY obtained_value is list or set."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "A", 0.8, None),     # string
            FieldEvaluation("field", "method", "expected", ["A"], 0.9, None),   # list triggers multi-label
            FieldEvaluation("field", "method", "expected", "B", 0.7, None),     # string
        ]
        reference = ["A", "B"]

        recall = compute_recall_at_k(results, reference)

        # Multi-label mode: ref_set = {A, B}
        # union_predicted = set("A") ∪ {A} ∪ set("B") = {"A"} ∪ {A} ∪ {"B"} = {A, B}
        # intersection = {A, B}
        # recall = 2/2 = 1.0
        assert recall == 1.0

    def test_multi_label_empty_obtained_values(self):
        """Test multi-label mode with empty lists/sets as obtained_values."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", [], 0.8, None),      # empty list
            FieldEvaluation("field", "method", "expected", set(), 0.9, None),   # empty set
            FieldEvaluation("field", "method", "expected", ["A"], 0.7, None),   # non-empty
        ]
        reference = ["A", "B"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {} ∪ {} ∪ {A} = {A}
        # intersection with {A, B} = {A}
        # recall = 1/2 = 0.5
        assert recall == 0.5

    def test_single_element_multi_label_perfect_match(self):
        """Test single-element list with perfect multi-label match."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B", "C"], 0.8, None),
        ]
        reference = ["A", "B", "C"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {A, B, C}
        # intersection with {A, B, C} = {A, B, C}
        # recall = 3/3 = 1.0
        assert recall == 1.0

    def test_single_element_single_label_perfect_match(self):
        """Test single-element list with perfect single-label match."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", "correct", 0.8, None),
        ]
        reference = "correct"

        recall = compute_recall_at_k(results, reference)

        # Single-label: ref_set = {"correct"}, union_predicted = {"correct"}
        # intersection = {"correct"}, returns 1.0
        assert recall == 1.0

    def test_multi_label_superset_predictions(self):
        """Test multi-label mode where predictions contain extra labels not in reference."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B", "X"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["C", "Y", "Z"], 0.9, None),
        ]
        reference = ["A", "B", "C"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {A, B, X, C, Y, Z}
        # intersection with {A, B, C} = {A, B, C}
        # recall = 3/3 = 1.0 (extra predicted labels don't hurt recall)
        assert recall == 1.0

    def test_multi_label_duplicate_labels_in_results(self):
        """Test multi-label mode with duplicate labels across different results."""
        from assayer.evaluators.consistency_metrics import compute_recall_at_k

        results = [
            FieldEvaluation("field", "method", "expected", ["A", "B"], 0.8, None),
            FieldEvaluation("field", "method", "expected", ["A", "C"], 0.9, None),  # A appears again
            FieldEvaluation("field", "method", "expected", ["B", "D"], 0.7, None),  # B appears again
        ]
        reference = ["A", "B", "C", "D", "E"]

        recall = compute_recall_at_k(results, reference)

        # union_predicted = {A, B} ∪ {A, C} ∪ {B, D} = {A, B, C, D}
        # intersection with {A, B, C, D, E} = {A, B, C, D}
        # recall = 4/5 = 0.8
        assert recall == 0.8
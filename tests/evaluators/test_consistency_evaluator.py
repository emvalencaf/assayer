"""Tests for ConsistencyEvaluator class."""

import pytest
from typing import Any

from assayer.evaluators.base import BaseEvaluator
from assayer.evaluators.consistency import ConsistencyEvaluator
from assayer.models import FieldEvaluation


class StubEvaluator(BaseEvaluator):
    """Concrete stub implementation of BaseEvaluator for testing."""

    def __init__(self, name: str = "test_evaluator") -> None:
        """Initialize the stub evaluator.

        Args:
            name: Name for the evaluator.
        """
        super().__init__(name)

    def evaluate(
        self,
        prediction: Any,
        reference: Any,
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Return a dummy FieldEvaluation.

        Args:
            prediction: The predicted value.
            reference: The reference value.
            **kwargs: Additional keyword arguments.

        Returns:
            A dummy FieldEvaluation with score 0.5.
        """
        return FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value=reference,
            obtained_value=prediction,
            score=0.5,
            prompt_hash=None,
        )


class TestConsistencyEvaluatorConstructor:
    """Test ConsistencyEvaluator constructor validation and attribute storage."""

    def test_constructor_with_defaults(self) -> None:
        """Test constructor with default parameters."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 5
        assert consistency_evaluator._min_k is None

    def test_constructor_with_custom_k(self) -> None:
        """Test constructor with custom k value."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=10)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 10
        assert consistency_evaluator._min_k is None

    def test_constructor_with_custom_min_k(self) -> None:
        """Test constructor with custom min_k value."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=10, min_k=3)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 10
        assert consistency_evaluator._min_k == 3

    def test_constructor_with_all_custom_params(self) -> None:
        """Test constructor with all custom parameters."""
        evaluator = StubEvaluator("custom_evaluator")
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=20, min_k=5)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 20
        assert consistency_evaluator._min_k == 5

    def test_constructor_raises_error_when_k_zero(self) -> None:
        """Test constructor raises ValueError when k is 0."""
        evaluator = StubEvaluator()

        with pytest.raises(ValueError, match="k must be >= 1"):
            ConsistencyEvaluator(evaluator, k=0)

    def test_constructor_raises_error_when_k_negative(self) -> None:
        """Test constructor raises ValueError when k is negative."""
        evaluator = StubEvaluator()

        with pytest.raises(ValueError, match="k must be >= 1"):
            ConsistencyEvaluator(evaluator, k=-1)

    def test_constructor_raises_error_when_k_very_negative(self) -> None:
        """Test constructor raises ValueError when k is very negative."""
        evaluator = StubEvaluator()

        with pytest.raises(ValueError, match="k must be >= 1"):
            ConsistencyEvaluator(evaluator, k=-100)

    def test_constructor_raises_error_when_min_k_zero(self) -> None:
        """Test constructor raises ValueError when min_k is 0."""
        evaluator = StubEvaluator()

        with pytest.raises(ValueError, match="min_k must be >= 1"):
            ConsistencyEvaluator(evaluator, min_k=0)

    def test_constructor_raises_error_when_min_k_negative(self) -> None:
        """Test constructor raises ValueError when min_k is negative."""
        evaluator = StubEvaluator()

        with pytest.raises(ValueError, match="min_k must be >= 1"):
            ConsistencyEvaluator(evaluator, min_k=-1)

    def test_constructor_raises_error_when_min_k_very_negative(self) -> None:
        """Test constructor raises ValueError when min_k is very negative."""
        evaluator = StubEvaluator()

        with pytest.raises(ValueError, match="min_k must be >= 1"):
            ConsistencyEvaluator(evaluator, min_k=-50)

    def test_constructor_accepts_min_k_equal_to_k(self) -> None:
        """Test constructor accepts min_k equal to k."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=5, min_k=5)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 5
        assert consistency_evaluator._min_k == 5

    def test_constructor_accepts_min_k_less_than_k(self) -> None:
        """Test constructor accepts min_k less than k."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=10, min_k=3)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 10
        assert consistency_evaluator._min_k == 3

    def test_constructor_accepts_min_k_one(self) -> None:
        """Test constructor accepts min_k of 1."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=5, min_k=1)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 5
        assert consistency_evaluator._min_k == 1

    def test_constructor_accepts_k_one(self) -> None:
        """Test constructor accepts k of 1."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=1)

        assert consistency_evaluator._evaluator is evaluator
        assert consistency_evaluator._k == 1
        assert consistency_evaluator._min_k is None

    def test_constructor_accepts_different_evaluator_types(self) -> None:
        """Test constructor accepts different BaseEvaluator subclass instances."""
        class AnotherStubEvaluator(BaseEvaluator):
            def __init__(self) -> None:
                super().__init__("another_stub")

            def evaluate(
                self,
                prediction: Any,
                reference: Any,
                **kwargs: Any,
            ) -> FieldEvaluation:
                return FieldEvaluation(
                    field_name="another_test_field",
                    evaluator_method="another_test_method",
                    expected_value=reference,
                    obtained_value=prediction,
                    score=1.0,
                    prompt_hash=None,
                )

        evaluator1 = StubEvaluator("eval1")
        evaluator2 = AnotherStubEvaluator()

        consistency_evaluator1 = ConsistencyEvaluator(evaluator1)
        consistency_evaluator2 = ConsistencyEvaluator(evaluator2)

        assert consistency_evaluator1._evaluator is evaluator1
        assert consistency_evaluator2._evaluator is evaluator2


class TestConsistencyEvaluatorEvaluateDataset:
    """Test ConsistencyEvaluator.evaluate_dataset method."""

    def test_empty_dataset_returns_empty_summary(self) -> None:
        """Test that empty dataset returns empty ConsistencySummary."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator)

        result = consistency_evaluator.evaluate_dataset([], "group_field")

        assert result.mean_agreement_rate == 0.0
        assert result.mean_entropy == 0.0
        assert result.mean_score_std == 0.0
        assert result.mean_correct_rate == 0.0
        assert result.pass_at_k_rate == 0.0
        assert result.mean_recall_at_k == 0.0
        assert result.per_group == []
        assert result.worst_groups == []

    def test_missing_group_by_field_raises_valueerror(self) -> None:
        """Test that missing group_by field raises ValueError with index."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
            {"prediction": "pred2", "reference": "ref2"},  # Missing group_field
        ]

        with pytest.raises(ValueError, match="Record at index 1 is missing field 'group_field'"):
            consistency_evaluator.evaluate_dataset(dataset, "group_field")

    def test_missing_group_by_field_first_record_raises_valueerror(self) -> None:
        """Test that missing group_by field in first record raises ValueError with index 0."""
        evaluator = StubEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"prediction": "pred1", "reference": "ref1"},  # Missing group_field
            {"group_field": "A", "prediction": "pred2", "reference": "ref2"},
        ]

        with pytest.raises(ValueError, match="Record at index 0 is missing field 'group_field'"):
            consistency_evaluator.evaluate_dataset(dataset, "group_field")

    def test_groups_records_by_group_field(self) -> None:
        """Test that records are correctly grouped by group_by field."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.8,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},
            {"group_field": "A", "prediction": "pred3", "reference": "ref3"},
        ]

        result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # Should have 2 groups (A and B)
        assert len(result.per_group) == 2

        # Group A should have 2 records, Group B should have 1 record
        group_sizes = {group.group_key: group.n for group in result.per_group}
        assert group_sizes.get("A") == 2
        assert group_sizes.get("B") == 1

        # Evaluator should be called once per record (3 times total)
        assert evaluator.evaluate.call_count == 3

    def test_uses_custom_prediction_and_reference_fields(self) -> None:
        """Test that custom prediction_field and reference_field names are used."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="custom_ref",
            obtained_value="custom_pred",
            score=0.9,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "custom_pred": "pred1", "custom_ref": "ref1"},
            {"group_field": "A", "custom_pred": "pred2", "custom_ref": "ref2"},
        ]

        result = consistency_evaluator.evaluate_dataset(
            dataset,
            "group_field",
            prediction_field="custom_pred",
            reference_field="custom_ref"
        )

        # Verify evaluator was called with correct field values
        evaluator.evaluate.assert_any_call("pred1", "ref1")
        evaluator.evaluate.assert_any_call("pred2", "ref2")
        assert len(result.per_group) == 1

    def test_default_prediction_and_reference_fields(self) -> None:
        """Test that default field names 'prediction' and 'reference' are used."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="default_ref",
            obtained_value="default_pred",
            score=0.7,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
        ]

        result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        evaluator.evaluate.assert_called_once_with("pred1", "ref1")
        assert len(result.per_group) == 1

    def test_min_k_filtering_excludes_small_groups(self) -> None:
        """Test that groups with fewer than min_k records are excluded."""
        import warnings
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.5,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator, min_k=3)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},  # Group A: 1 record
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},  # Group B: 3 records
            {"group_field": "B", "prediction": "pred3", "reference": "ref3"},
            {"group_field": "B", "prediction": "pred4", "reference": "ref4"},
            {"group_field": "C", "prediction": "pred5", "reference": "ref5"},  # Group C: 2 records
            {"group_field": "C", "prediction": "pred6", "reference": "ref6"},
        ]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

            # Should emit warning about excluded groups
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            warning_message = str(w[0].message)
            assert "Excluded groups with n < 3:" in warning_message
            assert "A" in warning_message
            assert "C" in warning_message

        # Only group B should remain (has 3 records)
        assert len(result.per_group) == 1
        assert result.per_group[0].group_key == "B"
        assert result.per_group[0].n == 3

    def test_min_k_none_includes_all_groups(self) -> None:
        """Test that min_k=None includes all groups regardless of size."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.6,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator, min_k=None)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},  # Group A: 1 record
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},  # Group B: 2 records
            {"group_field": "B", "prediction": "pred3", "reference": "ref3"},
        ]

        result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # Should include both groups
        assert len(result.per_group) == 2
        group_sizes = {group.group_key: group.n for group in result.per_group}
        assert group_sizes.get("A") == 1
        assert group_sizes.get("B") == 2

    def test_min_k_boundary_condition_equal_to_min_k(self) -> None:
        """Test that groups with exactly min_k records are retained."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.4,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator, min_k=2)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},  # Group A: 1 record (excluded)
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},  # Group B: 2 records (retained)
            {"group_field": "B", "prediction": "pred3", "reference": "ref3"},
            {"group_field": "C", "prediction": "pred4", "reference": "ref4"},  # Group C: 3 records (retained)
            {"group_field": "C", "prediction": "pred5", "reference": "ref5"},
            {"group_field": "C", "prediction": "pred6", "reference": "ref6"},
        ]

        result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # Should include groups B and C (both have >= 2 records)
        assert len(result.per_group) == 2
        group_sizes = {group.group_key: group.n for group in result.per_group}
        assert group_sizes.get("B") == 2
        assert group_sizes.get("C") == 3

    def test_all_groups_filtered_returns_empty_summary(self) -> None:
        """Test that when all groups are filtered out by min_k, returns empty summary."""
        import warnings
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.3,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator, min_k=5)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},  # Group A: 1 record
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},  # Group B: 2 records
            {"group_field": "B", "prediction": "pred3", "reference": "ref3"},
        ]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

            # Should emit warning about all groups being excluded
            assert len(w) == 1
            assert "Excluded groups with n < 5:" in str(w[0].message)

        # Should return empty summary
        assert result.mean_agreement_rate == 0.0
        assert result.mean_entropy == 0.0
        assert result.mean_score_std == 0.0
        assert result.mean_correct_rate == 0.0
        assert result.pass_at_k_rate == 0.0
        assert result.mean_recall_at_k == 0.0
        assert result.per_group == []
        assert result.worst_groups == []

    def test_evaluator_called_once_per_record_in_each_group(self) -> None:
        """Test that wrapped evaluator is called exactly once per record within each group."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.75,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
            {"group_field": "A", "prediction": "pred2", "reference": "ref2"},
            {"group_field": "B", "prediction": "pred3", "reference": "ref3"},
            {"group_field": "B", "prediction": "pred4", "reference": "ref4"},
            {"group_field": "B", "prediction": "pred5", "reference": "ref5"},
        ]

        result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # Should call evaluator exactly 5 times (once per record)
        assert evaluator.evaluate.call_count == 5

        # Verify all calls were made with correct parameters
        expected_calls = [
            ("pred1", "ref1"),
            ("pred2", "ref2"),
            ("pred3", "ref3"),
            ("pred4", "ref4"),
            ("pred5", "ref5"),
        ]
        actual_calls = [call[0] for call in evaluator.evaluate.call_args_list]
        assert actual_calls == expected_calls

    def test_returns_consistency_summary_with_per_group_evaluations(self) -> None:
        """Test that method returns ConsistencySummary with ConsistencyFieldEvaluation per group."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.8,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
            {"group_field": "A", "prediction": "pred2", "reference": "ref2"},
            {"group_field": "B", "prediction": "pred3", "reference": "ref3"},
        ]

        # Mock all metric computation functions
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=0.9) as mock_agreement, \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=0.5) as mock_entropy, \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.1) as mock_std, \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.7) as mock_correct, \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True) as mock_pass, \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.85) as mock_recall:

            result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # Should have 2 groups (A and B)
        assert len(result.per_group) == 2

        # Check that per_group contains ConsistencyFieldEvaluation instances
        for group_eval in result.per_group:
            from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation
            assert isinstance(group_eval, ConsistencyFieldEvaluation)
            assert group_eval.group_key in ["A", "B"]

            # Verify group-specific values
            if group_eval.group_key == "A":
                assert group_eval.n == 2
            elif group_eval.group_key == "B":
                assert group_eval.n == 1

    def test_consistency_summary_worst_groups_sorted_by_agreement_rate(self) -> None:
        """Test that worst_groups contains top-10 groups sorted by ascending agreement_rate."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.5,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        # Create dataset with multiple groups
        dataset = []
        for i in range(12):  # More than 10 groups to test top-10 limiting
            dataset.append({
                "group_field": f"group_{i}",
                "prediction": f"pred_{i}",
                "reference": f"ref_{i}"
            })

        # Mock compute_agreement_rate to return different values for each group
        def mock_agreement_rate(results):
            # Return different agreement rates based on the first result's obtained_value
            group_id = int(results[0].obtained_value.split('_')[1])
            return (group_id % 10) / 10.0  # Values from 0.0 to 0.9

        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', side_effect=mock_agreement_rate), \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=0.5), \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.1), \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.7), \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True), \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.85):

            result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # worst_groups should contain at most 10 entries
        assert len(result.worst_groups) <= 10

        # worst_groups should be sorted by ascending agreement_rate
        if len(result.worst_groups) > 1:
            for i in range(len(result.worst_groups) - 1):
                assert result.worst_groups[i].agreement_rate <= result.worst_groups[i + 1].agreement_rate

    def test_consistency_summary_computes_mean_metrics(self) -> None:
        """Test that ConsistencySummary correctly computes mean values across groups."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.6,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},
        ]

        # Mock metric functions to return specific values
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=0.8), \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=1.0), \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.2), \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.6), \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True), \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.9):

            result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # With 2 identical groups, means should equal the individual values
        assert result.mean_agreement_rate == 0.8
        assert result.mean_entropy == 1.0
        assert result.mean_score_std == 0.2
        assert result.mean_correct_rate == 0.6
        assert result.mean_recall_at_k == 0.9
        assert result.pass_at_k_rate == 1.0  # Both groups have pass_at_k=True

    def test_consistency_summary_pass_at_k_rate_computation(self) -> None:
        """Test that pass_at_k_rate is computed as proportion of groups with pass_at_k=True."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="expected",
            obtained_value="result",
            score=0.7,
            prompt_hash=None,
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator)

        dataset = [
            {"group_field": "A", "prediction": "pred1", "reference": "ref1"},
            {"group_field": "B", "prediction": "pred2", "reference": "ref2"},
            {"group_field": "C", "prediction": "pred3", "reference": "ref3"},
            {"group_field": "D", "prediction": "pred4", "reference": "ref4"},
        ]

        # Mock pass_at_k to return different values for different groups
        def mock_pass_at_k(results):
            group_name = results[0].obtained_value[-1]  # Last char of "predN"
            return group_name in ["1", "3"]  # Groups A and C return True, B and D return False

        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=0.8), \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=1.0), \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.2), \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.6), \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', side_effect=mock_pass_at_k), \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.9):

            result = consistency_evaluator.evaluate_dataset(dataset, "group_field")

        # 2 out of 4 groups have pass_at_k=True, so pass_at_k_rate should be 0.5
        assert result.pass_at_k_rate == 0.5


class TestConsistencyEvaluatorEvaluateLive:
    """Test ConsistencyEvaluator.evaluate_live method."""

    def test_calls_target_fn_exactly_k_times(self) -> None:
        """Test that target_fn is called exactly k times."""
        from unittest.mock import Mock

        # Create mock evaluator
        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="prediction",
            score=0.8,
            prompt_hash=None,
        )

        # Create mock target function
        target_fn = Mock()
        target_fn.side_effect = ["pred1", "pred2", "pred3"]  # Return different values each call

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=3)

        result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

        # target_fn should be called exactly k=3 times with the same input
        assert target_fn.call_count == 3
        target_fn.assert_any_call("input")
        # Verify all calls were with the same input
        for call in target_fn.call_args_list:
            assert call[0] == ("input",)

    def test_calls_evaluator_once_per_target_fn_output(self) -> None:
        """Test that wrapped evaluator is called once for each target_fn output."""
        from unittest.mock import Mock

        # Create mock evaluator
        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="prediction",
            score=0.9,
            prompt_hash=None,
        )

        # Create mock target function
        target_fn = Mock()
        target_fn.side_effect = ["output1", "output2", "output3", "output4"]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=4)

        result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

        # Evaluator should be called 4 times (once per target_fn output)
        assert evaluator.evaluate.call_count == 4

        # Verify evaluator was called with each target_fn output and the reference
        expected_calls = [
            ("output1", "reference"),
            ("output2", "reference"),
            ("output3", "reference"),
            ("output4", "reference"),
        ]
        actual_calls = [call[0] for call in evaluator.evaluate.call_args_list]
        assert actual_calls == expected_calls

    def test_returns_consistency_field_evaluation_with_group_key_none(self) -> None:
        """Test that method returns ConsistencyFieldEvaluation with group_key=None."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="prediction",
            score=0.7,
            prompt_hash=None,
        )

        target_fn = Mock()
        target_fn.side_effect = ["output1", "output2"]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=2)

        # Mock all metric computation functions
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=(0.8, "dominant")) as mock_agreement, \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=0.5) as mock_entropy, \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.1) as mock_std, \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.6) as mock_correct, \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True) as mock_pass, \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.9) as mock_recall:

            result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

        # Verify return type and group_key
        from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation
        assert isinstance(result, ConsistencyFieldEvaluation)
        assert result.group_key is None

    def test_returns_consistency_field_evaluation_with_n_equals_k(self) -> None:
        """Test that returned ConsistencyFieldEvaluation has n == k."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="prediction",
            score=0.6,
            prompt_hash=None,
        )

        target_fn = Mock()
        target_fn.side_effect = ["out1", "out2", "out3", "out4", "out5"]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=5)

        # Mock metric functions
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=(0.9, "dom")) as mock_agreement, \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=0.3) as mock_entropy, \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.2) as mock_std, \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.4) as mock_correct, \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=False) as mock_pass, \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.8) as mock_recall:

            result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

        assert result.n == 5  # Should equal k

    def test_k_equals_1_returns_expected_consistency_metrics(self) -> None:
        """Test that k=1 returns ConsistencyFieldEvaluation with expected single-run metrics."""
        from unittest.mock import Mock

        evaluator = StubEvaluator()  # Use the StubEvaluator which returns a fixed FieldEvaluation
        target_fn = Mock()
        target_fn.return_value = "single_output"

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=1)

        result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

        # With k=1, should have specific consistency metric values
        assert result.n == 1
        assert result.group_key is None

        # For k=1: entropy=0.0, score_std=0.0, agreement_rate=1.0
        assert result.entropy == 0.0
        assert result.score_std == 0.0
        assert result.agreement_rate == 1.0

    def test_target_fn_exception_propagates(self) -> None:
        """Test that exceptions from target_fn propagate without being caught."""
        evaluator = StubEvaluator()

        def failing_target_fn(input):
            if input == "fail_input":
                raise RuntimeError("Target function failed")
            return "success_output"

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=3)

        # Exception should propagate from target_fn
        with pytest.raises(RuntimeError, match="Target function failed"):
            consistency_evaluator.evaluate_live(failing_target_fn, "fail_input", "reference")

    def test_target_fn_exception_on_second_call_propagates(self) -> None:
        """Test that exception on a later call to target_fn propagates."""
        evaluator = StubEvaluator()

        call_count = 0
        def failing_on_second_call(input):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Second call failed")
            return f"output_{call_count}"

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=3)

        # Should fail on the second call
        with pytest.raises(ValueError, match="Second call failed"):
            consistency_evaluator.evaluate_live(failing_on_second_call, "input", "reference")

    def test_evaluator_exception_propagates(self) -> None:
        """Test that exceptions from wrapped evaluator propagate without being caught."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.side_effect = RuntimeError("Evaluator failed")

        target_fn = Mock()
        target_fn.return_value = "output"

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=2)

        # Exception should propagate from evaluator
        with pytest.raises(RuntimeError, match="Evaluator failed"):
            consistency_evaluator.evaluate_live(target_fn, "input", "reference")

    def test_evaluator_exception_on_second_evaluation_propagates(self) -> None:
        """Test that exception from evaluator on a later evaluation propagates."""
        from unittest.mock import Mock

        evaluator = Mock()
        # First call succeeds, second call fails
        evaluator.evaluate.side_effect = [
            FieldEvaluation(
                field_name="test_field",
                evaluator_method="test_method",
                expected_value="reference",
                obtained_value="output1",
                score=0.8,
                prompt_hash=None,
            ),
            ValueError("Second evaluation failed")
        ]

        target_fn = Mock()
        target_fn.side_effect = ["output1", "output2"]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=2)

        # Should fail on the second evaluation
        with pytest.raises(ValueError, match="Second evaluation failed"):
            consistency_evaluator.evaluate_live(target_fn, "input", "reference")

    def test_calls_all_metric_functions_with_collected_results(self) -> None:
        """Test that all consistency metrics are called with the collected FieldEvaluation results."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        field_eval1 = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="output1",
            score=0.8,
            prompt_hash=None,
        )
        field_eval2 = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="output2",
            score=0.6,
            prompt_hash=None,
        )
        evaluator.evaluate.side_effect = [field_eval1, field_eval2]

        target_fn = Mock()
        target_fn.side_effect = ["output1", "output2"]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=2)

        # Mock all metric computation functions to track calls
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=(0.5, "output1")) as mock_agreement, \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=1.0) as mock_entropy, \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.1) as mock_std, \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.5) as mock_correct, \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True) as mock_pass, \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.7) as mock_recall:

            result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

            # Verify all metric functions were called with the collected results
            mock_agreement.assert_called_once_with([field_eval1, field_eval2])
            mock_entropy.assert_called_once_with([field_eval1, field_eval2])
            mock_std.assert_called_once_with([field_eval1, field_eval2])
            mock_correct.assert_called_once_with([field_eval1, field_eval2], "reference")
            mock_pass.assert_called_once_with([field_eval1, field_eval2], "reference")
            mock_recall.assert_called_once_with([field_eval1, field_eval2], "reference")

    def test_returns_consistency_field_evaluation_with_computed_metrics(self) -> None:
        """Test that returned ConsistencyFieldEvaluation contains metrics from metric functions."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="prediction",
            score=0.5,
            prompt_hash=None,
        )

        target_fn = Mock()
        target_fn.side_effect = ["output1", "output2", "output3"]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=3)

        # Mock metric functions with specific return values
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=(0.67, "output1")) as mock_agreement, \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=1.2) as mock_entropy, \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.15) as mock_std, \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.33) as mock_correct, \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True) as mock_pass, \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=0.8) as mock_recall:

            result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

            # Verify all metric values are correctly set in the result
            assert result.agreement_rate == 0.67
            assert result.dominant_label == "output1"
            assert result.entropy == 1.2
            assert result.score_std == 0.15
            assert result.correct_rate == 0.33
            assert result.pass_at_k is True
            assert result.recall_at_k == 0.8

    def test_works_with_different_input_and_reference_types(self) -> None:
        """Test that evaluate_live works with different input and reference types."""
        from unittest.mock import Mock

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value=[1, 2, 3],
            obtained_value=[1, 2],
            score=0.8,
            prompt_hash=None,
        )

        target_fn = Mock()
        target_fn.side_effect = [[1, 2], [2, 3]]

        consistency_evaluator = ConsistencyEvaluator(evaluator, k=2)

        # Test with list input and reference
        result = consistency_evaluator.evaluate_live(target_fn, {"complex": "input"}, [1, 2, 3])

        # Verify target_fn was called with the complex input
        target_fn.assert_any_call({"complex": "input"})

        # Verify evaluator was called with list outputs and reference
        evaluator.evaluate.assert_any_call([1, 2], [1, 2, 3])
        evaluator.evaluate.assert_any_call([2, 3], [1, 2, 3])

    def test_min_k_parameter_has_no_effect_in_live_mode(self) -> None:
        """Test that min_k parameter has no effect in evaluate_live method."""
        from unittest.mock import Mock, patch

        evaluator = Mock()
        evaluator.evaluate.return_value = FieldEvaluation(
            field_name="test_field",
            evaluator_method="test_method",
            expected_value="reference",
            obtained_value="prediction",
            score=0.7,
            prompt_hash=None,
        )

        target_fn = Mock()
        target_fn.side_effect = ["output1", "output2"]

        # Create evaluator with min_k that would filter in evaluate_dataset
        consistency_evaluator = ConsistencyEvaluator(evaluator, k=2, min_k=10)

        # Mock metric functions
        with patch('assayer.evaluators.consistency_metrics.compute_agreement_rate', return_value=(1.0, "output1")) as mock_agreement, \
             patch('assayer.evaluators.consistency_metrics.compute_entropy', return_value=0.0) as mock_entropy, \
             patch('assayer.evaluators.consistency_metrics.compute_score_std', return_value=0.0) as mock_std, \
             patch('assayer.evaluators.consistency_metrics.compute_correct_rate', return_value=0.5) as mock_correct, \
             patch('assayer.evaluators.consistency_metrics.compute_pass_at_k', return_value=True) as mock_pass, \
             patch('assayer.evaluators.consistency_metrics.compute_recall_at_k', return_value=1.0) as mock_recall:

            result = consistency_evaluator.evaluate_live(target_fn, "input", "reference")

        # Should work normally with n=2, ignoring min_k=10
        assert result.n == 2
        assert target_fn.call_count == 2
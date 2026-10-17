"""Tests for consistency evaluation models."""

import pytest

from assayer.models import ConsistencyFieldEvaluation, ConsistencySummary, FieldEvaluation


class TestConsistencyFieldEvaluation:
    """Test ConsistencyFieldEvaluation dataclass."""

    def test_can_be_instantiated_with_all_required_fields(self):
        """Test that ConsistencyFieldEvaluation can be instantiated with all required fields and exposes them as typed attributes."""
        # Create sample FieldEvaluation instances for raw_results
        field_eval1 = FieldEvaluation(
            field_name="test_field",
            evaluator_method="exact_match",
            expected_value="expected",
            obtained_value="obtained",
            score=0.8,
            prompt_hash=None,
        )
        field_eval2 = FieldEvaluation(
            field_name="test_field",
            evaluator_method="exact_match",
            expected_value="expected",
            obtained_value="obtained2",
            score=0.6,
            prompt_hash=None,
        )

        eval_result = ConsistencyFieldEvaluation(
            group_key="test_group",
            n=3,
            agreement_rate=0.7,
            dominant_label="label_a",
            entropy=1.5,
            score_std=0.2,
            correct_rate=0.6,
            pass_at_k=True,
            recall_at_k=0.8,
            raw_results=[field_eval1, field_eval2],
        )

        # Test all fields are accessible and have expected types
        assert eval_result.group_key == "test_group"
        assert isinstance(eval_result.group_key, str)

        assert eval_result.n == 3
        assert isinstance(eval_result.n, int)

        assert eval_result.agreement_rate == 0.7
        assert isinstance(eval_result.agreement_rate, float)

        assert eval_result.dominant_label == "label_a"
        assert isinstance(eval_result.dominant_label, str)

        assert eval_result.entropy == 1.5
        assert isinstance(eval_result.entropy, float)

        assert eval_result.score_std == 0.2
        assert isinstance(eval_result.score_std, float)

        assert eval_result.correct_rate == 0.6
        assert isinstance(eval_result.correct_rate, float)

        assert eval_result.pass_at_k is True
        assert isinstance(eval_result.pass_at_k, bool)

        assert eval_result.recall_at_k == 0.8
        assert isinstance(eval_result.recall_at_k, float)

        assert eval_result.raw_results == [field_eval1, field_eval2]
        assert isinstance(eval_result.raw_results, list)
        assert all(isinstance(item, FieldEvaluation) for item in eval_result.raw_results)

    def test_post_init_raises_value_error_if_n_less_than_1(self):
        """Test that __post_init__ raises ValueError if n < 1."""
        with pytest.raises(ValueError, match="n must be >= 1"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=0,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=0.8,
            )

        with pytest.raises(ValueError, match="n must be >= 1"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=-1,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=0.8,
            )

    def test_post_init_raises_value_error_if_agreement_rate_outside_range(self):
        """Test that __post_init__ raises ValueError if agreement_rate is outside [0.0, 1.0]."""
        with pytest.raises(ValueError, match="agreement_rate must be in the range \\[0.0, 1.0\\]"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=-0.1,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=0.8,
            )

        with pytest.raises(ValueError, match="agreement_rate must be in the range \\[0.0, 1.0\\]"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=1.1,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=0.8,
            )

    def test_post_init_raises_value_error_if_entropy_less_than_zero(self):
        """Test that __post_init__ raises ValueError if entropy < 0.0."""
        with pytest.raises(ValueError, match="entropy must be >= 0.0"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=-0.1,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=0.8,
            )

    def test_post_init_raises_value_error_if_score_std_less_than_zero(self):
        """Test that __post_init__ raises ValueError if score_std < 0.0."""
        with pytest.raises(ValueError, match="score_std must be >= 0.0"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=-0.1,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=0.8,
            )

    def test_post_init_raises_value_error_if_correct_rate_outside_range(self):
        """Test that __post_init__ raises ValueError if correct_rate is outside [0.0, 1.0]."""
        with pytest.raises(ValueError, match="correct_rate must be in the range \\[0.0, 1.0\\]"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=-0.1,
                pass_at_k=True,
                recall_at_k=0.8,
            )

        with pytest.raises(ValueError, match="correct_rate must be in the range \\[0.0, 1.0\\]"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=1.1,
                pass_at_k=True,
                recall_at_k=0.8,
            )

    def test_post_init_raises_value_error_if_recall_at_k_outside_range(self):
        """Test that __post_init__ raises ValueError if recall_at_k is outside [0.0, 1.0]."""
        with pytest.raises(ValueError, match="recall_at_k must be in the range \\[0.0, 1.0\\]"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=-0.1,
            )

        with pytest.raises(ValueError, match="recall_at_k must be in the range \\[0.0, 1.0\\]"):
            ConsistencyFieldEvaluation(
                group_key="test",
                n=3,
                agreement_rate=0.7,
                dominant_label="label_a",
                entropy=1.5,
                score_std=0.2,
                correct_rate=0.6,
                pass_at_k=True,
                recall_at_k=1.1,
            )

    def test_accepts_none_values_without_raising(self):
        """Test that group_key=None and dominant_label=None are accepted without raising."""
        # Should not raise with group_key=None
        eval_result = ConsistencyFieldEvaluation(
            group_key=None,
            n=3,
            agreement_rate=0.7,
            dominant_label="label_a",
            entropy=1.5,
            score_std=0.2,
            correct_rate=0.6,
            pass_at_k=True,
            recall_at_k=0.8,
        )
        assert eval_result.group_key is None

        # Should not raise with dominant_label=None
        eval_result = ConsistencyFieldEvaluation(
            group_key="test",
            n=3,
            agreement_rate=0.7,
            dominant_label=None,
            entropy=1.5,
            score_std=0.2,
            correct_rate=0.6,
            pass_at_k=True,
            recall_at_k=0.8,
        )
        assert eval_result.dominant_label is None

        # Should not raise with both None
        eval_result = ConsistencyFieldEvaluation(
            group_key=None,
            n=3,
            agreement_rate=0.7,
            dominant_label=None,
            entropy=1.5,
            score_std=0.2,
            correct_rate=0.6,
            pass_at_k=True,
            recall_at_k=0.8,
        )
        assert eval_result.group_key is None
        assert eval_result.dominant_label is None

    def test_raw_results_defaults_to_empty_list(self):
        """Test that raw_results defaults to an empty list when not provided."""
        eval_result = ConsistencyFieldEvaluation(
            group_key="test",
            n=3,
            agreement_rate=0.7,
            dominant_label="label_a",
            entropy=1.5,
            score_std=0.2,
            correct_rate=0.6,
            pass_at_k=True,
            recall_at_k=0.8,
            # raw_results not provided
        )

        assert eval_result.raw_results == []
        assert isinstance(eval_result.raw_results, list)

    def test_boundary_values_are_accepted(self):
        """Test that boundary values for ranges are accepted."""
        # Test minimum boundary values
        eval_result = ConsistencyFieldEvaluation(
            group_key="test",
            n=1,  # minimum value
            agreement_rate=0.0,  # minimum value
            dominant_label="label_a",
            entropy=0.0,  # minimum value
            score_std=0.0,  # minimum value
            correct_rate=0.0,  # minimum value
            pass_at_k=False,
            recall_at_k=0.0,  # minimum value
        )
        assert eval_result.n == 1
        assert eval_result.agreement_rate == 0.0
        assert eval_result.entropy == 0.0
        assert eval_result.score_std == 0.0
        assert eval_result.correct_rate == 0.0
        assert eval_result.recall_at_k == 0.0

        # Test maximum boundary values
        eval_result = ConsistencyFieldEvaluation(
            group_key="test",
            n=1000,  # large but valid value
            agreement_rate=1.0,  # maximum value
            dominant_label="label_a",
            entropy=10.0,  # unbounded above, so any positive value is valid
            score_std=5.0,  # unbounded above, so any positive value is valid
            correct_rate=1.0,  # maximum value
            pass_at_k=True,
            recall_at_k=1.0,  # maximum value
        )
        assert eval_result.n == 1000
        assert eval_result.agreement_rate == 1.0
        assert eval_result.entropy == 10.0
        assert eval_result.score_std == 5.0
        assert eval_result.correct_rate == 1.0
        assert eval_result.recall_at_k == 1.0

    def test_edge_case_n_equals_one(self):
        """Test edge case where n == 1, which should be valid according to the spec."""
        eval_result = ConsistencyFieldEvaluation(
            group_key="test",
            n=1,
            agreement_rate=1.0,  # must be 1.0 when n == 1
            dominant_label="label_a",
            entropy=0.0,  # must be 0.0 when n == 1
            score_std=0.0,  # must be 0.0 when n == 1
            correct_rate=1.0,
            pass_at_k=True,
            recall_at_k=1.0,
        )

        assert eval_result.n == 1
        assert eval_result.agreement_rate == 1.0
        assert eval_result.entropy == 0.0
        assert eval_result.score_std == 0.0

    def test_raw_results_accepts_field_evaluation_list(self):
        """Test that raw_results properly accepts a list of FieldEvaluation objects."""
        field_eval = FieldEvaluation(
            field_name="test_field",
            evaluator_method="exact_match",
            expected_value="expected",
            obtained_value="obtained",
            score=0.8,
            prompt_hash="abc123",
        )

        eval_result = ConsistencyFieldEvaluation(
            group_key="test",
            n=1,
            agreement_rate=1.0,
            dominant_label="label_a",
            entropy=0.0,
            score_std=0.0,
            correct_rate=1.0,
            pass_at_k=True,
            recall_at_k=1.0,
            raw_results=[field_eval],
        )

        assert len(eval_result.raw_results) == 1
        assert eval_result.raw_results[0] is field_eval
        assert isinstance(eval_result.raw_results[0], FieldEvaluation)


class TestConsistencySummary:
    """Test ConsistencySummary dataclass."""

    def test_can_be_instantiated_with_all_required_fields(self):
        """Test that ConsistencySummary can be instantiated with all required fields and exposes them as typed attributes."""
        # Create some ConsistencyFieldEvaluation instances
        eval1 = ConsistencyFieldEvaluation(
            group_key="group1",
            n=3,
            agreement_rate=0.8,
            dominant_label="label_a",
            entropy=1.2,
            score_std=0.15,
            correct_rate=0.7,
            pass_at_k=True,
            recall_at_k=0.85,
        )
        eval2 = ConsistencyFieldEvaluation(
            group_key="group2",
            n=2,
            agreement_rate=0.5,
            dominant_label="label_b",
            entropy=1.0,
            score_std=0.25,
            correct_rate=0.4,
            pass_at_k=False,
            recall_at_k=0.6,
        )

        summary = ConsistencySummary(
            per_group=[eval1, eval2],
            mean_agreement_rate=0.65,
            mean_entropy=1.1,
            mean_score_std=0.2,
            mean_correct_rate=0.55,
            pass_at_k_rate=0.5,
            mean_recall_at_k=0.725,
            worst_groups=[eval2],
        )

        # Test all fields are accessible and have expected types
        assert summary.per_group == [eval1, eval2]
        assert isinstance(summary.per_group, list)
        assert all(isinstance(item, ConsistencyFieldEvaluation) for item in summary.per_group)

        assert summary.mean_agreement_rate == 0.65
        assert isinstance(summary.mean_agreement_rate, float)

        assert summary.mean_entropy == 1.1
        assert isinstance(summary.mean_entropy, float)

        assert summary.mean_score_std == 0.2
        assert isinstance(summary.mean_score_std, float)

        assert summary.mean_correct_rate == 0.55
        assert isinstance(summary.mean_correct_rate, float)

        assert summary.pass_at_k_rate == 0.5
        assert isinstance(summary.pass_at_k_rate, float)

        assert summary.mean_recall_at_k == 0.725
        assert isinstance(summary.mean_recall_at_k, float)

        assert summary.worst_groups == [eval2]
        assert isinstance(summary.worst_groups, list)
        assert all(isinstance(item, ConsistencyFieldEvaluation) for item in summary.worst_groups)

    def test_post_init_raises_value_error_if_pass_at_k_rate_outside_range(self):
        """Test that __post_init__ raises ValueError if pass_at_k_rate is outside [0.0, 1.0]."""
        with pytest.raises(ValueError, match="pass_at_k_rate must be in the range \\[0.0, 1.0\\]"):
            ConsistencySummary(
                mean_agreement_rate=0.5,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=0.6,
                pass_at_k_rate=-0.1,
                mean_recall_at_k=0.7,
            )

        with pytest.raises(ValueError, match="pass_at_k_rate must be in the range \\[0.0, 1.0\\]"):
            ConsistencySummary(
                mean_agreement_rate=0.5,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=0.6,
                pass_at_k_rate=1.1,
                mean_recall_at_k=0.7,
            )

    def test_post_init_raises_value_error_if_mean_correct_rate_outside_range(self):
        """Test that __post_init__ raises ValueError if mean_correct_rate is outside [0.0, 1.0]."""
        with pytest.raises(
            ValueError, match="mean_correct_rate must be in the range \\[0.0, 1.0\\]"
        ):
            ConsistencySummary(
                mean_agreement_rate=0.5,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=-0.1,
                pass_at_k_rate=0.8,
                mean_recall_at_k=0.7,
            )

        with pytest.raises(
            ValueError, match="mean_correct_rate must be in the range \\[0.0, 1.0\\]"
        ):
            ConsistencySummary(
                mean_agreement_rate=0.5,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=1.1,
                pass_at_k_rate=0.8,
                mean_recall_at_k=0.7,
            )

    def test_post_init_raises_value_error_if_mean_recall_at_k_outside_range(self):
        """Test that __post_init__ raises ValueError if mean_recall_at_k is outside [0.0, 1.0]."""
        with pytest.raises(
            ValueError, match="mean_recall_at_k must be in the range \\[0.0, 1.0\\]"
        ):
            ConsistencySummary(
                mean_agreement_rate=0.5,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=0.6,
                pass_at_k_rate=0.8,
                mean_recall_at_k=-0.1,
            )

        with pytest.raises(
            ValueError, match="mean_recall_at_k must be in the range \\[0.0, 1.0\\]"
        ):
            ConsistencySummary(
                mean_agreement_rate=0.5,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=0.6,
                pass_at_k_rate=0.8,
                mean_recall_at_k=1.1,
            )

    def test_post_init_raises_value_error_if_mean_agreement_rate_outside_range(self):
        """Test that __post_init__ raises ValueError if mean_agreement_rate is outside [0.0, 1.0]."""
        with pytest.raises(
            ValueError, match="mean_agreement_rate must be in the range \\[0.0, 1.0\\]"
        ):
            ConsistencySummary(
                mean_agreement_rate=-0.1,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=0.6,
                pass_at_k_rate=0.8,
                mean_recall_at_k=0.7,
            )

        with pytest.raises(
            ValueError, match="mean_agreement_rate must be in the range \\[0.0, 1.0\\]"
        ):
            ConsistencySummary(
                mean_agreement_rate=1.1,
                mean_entropy=1.0,
                mean_score_std=0.2,
                mean_correct_rate=0.6,
                pass_at_k_rate=0.8,
                mean_recall_at_k=0.7,
            )

    def test_per_group_and_worst_groups_default_to_empty_lists(self):
        """Test that per_group and worst_groups default to empty lists when not provided."""
        summary = ConsistencySummary(
            mean_agreement_rate=0.5,
            mean_entropy=1.0,
            mean_score_std=0.2,
            mean_correct_rate=0.6,
            pass_at_k_rate=0.8,
            mean_recall_at_k=0.7,
            # per_group and worst_groups not provided
        )

        assert summary.per_group == []
        assert isinstance(summary.per_group, list)
        assert summary.worst_groups == []
        assert isinstance(summary.worst_groups, list)

    def test_mean_entropy_and_mean_score_std_are_not_validated(self):
        """Test that mean_entropy and mean_score_std are not bounded above."""
        # Should not raise with large values for unbounded fields
        summary = ConsistencySummary(
            mean_agreement_rate=0.5,
            mean_entropy=100.0,  # unbounded above
            mean_score_std=50.0,  # unbounded above
            mean_correct_rate=0.6,
            pass_at_k_rate=0.8,
            mean_recall_at_k=0.7,
        )

        assert summary.mean_entropy == 100.0
        assert summary.mean_score_std == 50.0

    def test_boundary_values_are_accepted(self):
        """Test that boundary values for ranges are accepted."""
        # Test minimum boundary values
        summary = ConsistencySummary(
            mean_agreement_rate=0.0,  # minimum value
            mean_entropy=0.0,  # minimum value (not bounded above)
            mean_score_std=0.0,  # minimum value (not bounded above)
            mean_correct_rate=0.0,  # minimum value
            pass_at_k_rate=0.0,  # minimum value
            mean_recall_at_k=0.0,  # minimum value
        )
        assert summary.mean_agreement_rate == 0.0
        assert summary.mean_entropy == 0.0
        assert summary.mean_score_std == 0.0
        assert summary.mean_correct_rate == 0.0
        assert summary.pass_at_k_rate == 0.0
        assert summary.mean_recall_at_k == 0.0

        # Test maximum boundary values for bounded fields
        summary = ConsistencySummary(
            mean_agreement_rate=1.0,  # maximum value
            mean_entropy=10.0,  # unbounded above, so any positive value is valid
            mean_score_std=5.0,  # unbounded above, so any positive value is valid
            mean_correct_rate=1.0,  # maximum value
            pass_at_k_rate=1.0,  # maximum value
            mean_recall_at_k=1.0,  # maximum value
        )
        assert summary.mean_agreement_rate == 1.0
        assert summary.mean_entropy == 10.0
        assert summary.mean_score_std == 5.0
        assert summary.mean_correct_rate == 1.0
        assert summary.pass_at_k_rate == 1.0
        assert summary.mean_recall_at_k == 1.0

    def test_empty_groups_edge_case(self):
        """Test edge case where per_group and worst_groups can be empty."""
        summary = ConsistencySummary(
            per_group=[],  # empty list
            mean_agreement_rate=0.0,
            mean_entropy=0.0,
            mean_score_std=0.0,
            mean_correct_rate=0.0,
            pass_at_k_rate=0.0,
            mean_recall_at_k=0.0,
            worst_groups=[],  # empty list
        )

        assert summary.per_group == []
        assert summary.worst_groups == []

    def test_consistency_field_evaluation_instances_in_lists(self):
        """Test that per_group and worst_groups properly accept ConsistencyFieldEvaluation instances."""
        eval1 = ConsistencyFieldEvaluation(
            group_key="group1",
            n=1,
            agreement_rate=1.0,
            dominant_label="label_a",
            entropy=0.0,
            score_std=0.0,
            correct_rate=1.0,
            pass_at_k=True,
            recall_at_k=1.0,
        )
        eval2 = ConsistencyFieldEvaluation(
            group_key="group2",
            n=2,
            agreement_rate=0.5,
            dominant_label="label_b",
            entropy=1.0,
            score_std=0.2,
            correct_rate=0.4,
            pass_at_k=False,
            recall_at_k=0.6,
        )

        summary = ConsistencySummary(
            per_group=[eval1, eval2],
            mean_agreement_rate=0.75,
            mean_entropy=0.5,
            mean_score_std=0.1,
            mean_correct_rate=0.7,
            pass_at_k_rate=0.5,
            mean_recall_at_k=0.8,
            worst_groups=[eval2],  # subset of per_group
        )

        assert len(summary.per_group) == 2
        assert summary.per_group[0] is eval1
        assert summary.per_group[1] is eval2
        assert len(summary.worst_groups) == 1
        assert summary.worst_groups[0] is eval2

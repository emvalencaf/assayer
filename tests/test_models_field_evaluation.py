"""Tests for FieldEvaluation dataclass from assayer.models.

This module tests the FieldEvaluation dataclass implementation including:
- Valid instantiation with all seven fields
- Default behavior for metadata field
- Validation in __post_init__ method
- Edge cases and boundary conditions
"""

import pytest
from typing import Any

from assayer.models import FieldEvaluation


class TestFieldEvaluationInstantiation:
    """Test valid instantiation scenarios for FieldEvaluation."""

    def test_instantiation_with_all_fields(self):
        """Test AC-SPEC-003: FieldEvaluation can be instantiated with all seven fields."""
        # Arrange
        field_name = "accuracy"
        evaluator_method = "bleu"
        expected_value = "hello world"
        obtained_value = "hello universe"
        score = 0.75
        prompt_hash = "abc123def456"
        metadata = {"model": "gpt-4", "temperature": 0.7}

        # Act
        field_eval = FieldEvaluation(
            field_name=field_name,
            evaluator_method=evaluator_method,
            expected_value=expected_value,
            obtained_value=obtained_value,
            score=score,
            prompt_hash=prompt_hash,
            metadata=metadata
        )

        # Assert
        assert field_eval.field_name == field_name
        assert field_eval.evaluator_method == evaluator_method
        assert field_eval.expected_value == expected_value
        assert field_eval.obtained_value == obtained_value
        assert field_eval.score == score
        assert field_eval.prompt_hash == prompt_hash
        assert field_eval.metadata == metadata

    def test_instantiation_without_metadata_defaults_to_empty_dict(self):
        """Test AC-SPEC-003: metadata defaults to empty dict when not provided."""
        # Arrange & Act
        field_eval = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value="hello world",
            obtained_value="hello universe",
            score=0.75,
            prompt_hash="abc123def456"
        )

        # Assert
        assert field_eval.metadata == {}

    def test_instantiation_with_none_values(self):
        """Test that expected_value=None and prompt_hash=None are valid."""
        # Arrange & Act
        field_eval = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value=None,
            obtained_value="hello universe",
            score=0.75,
            prompt_hash=None
        )

        # Assert
        assert field_eval.expected_value is None
        assert field_eval.prompt_hash is None

    def test_instantiation_with_boundary_scores(self):
        """Test that score=0.0 and score=1.0 are valid boundary values."""
        # Test score=0.0
        field_eval_zero = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value="hello world",
            obtained_value="goodbye world",
            score=0.0,
            prompt_hash="abc123"
        )
        assert field_eval_zero.score == 0.0

        # Test score=1.0
        field_eval_one = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value="hello world",
            obtained_value="hello world",
            score=1.0,
            prompt_hash="abc123"
        )
        assert field_eval_one.score == 1.0


class TestFieldEvaluationValidation:
    """Test validation logic in FieldEvaluation.__post_init__."""

    def test_empty_field_name_raises_value_error(self):
        """Test AC-SPEC-004: empty field_name raises ValueError."""
        with pytest.raises(ValueError, match="field_name.*empty"):
            FieldEvaluation(
                field_name="",
                evaluator_method="bleu",
                expected_value="hello world",
                obtained_value="hello universe",
                score=0.75,
                prompt_hash="abc123"
            )

    def test_whitespace_only_field_name_raises_value_error(self):
        """Test edge case: whitespace-only field_name raises ValueError."""
        with pytest.raises(ValueError, match="field_name.*empty"):
            FieldEvaluation(
                field_name="   \t\n  ",
                evaluator_method="bleu",
                expected_value="hello world",
                obtained_value="hello universe",
                score=0.75,
                prompt_hash="abc123"
            )

    def test_empty_evaluator_method_raises_value_error(self):
        """Test AC-SPEC-004: empty evaluator_method raises ValueError."""
        with pytest.raises(ValueError, match="evaluator_method.*empty"):
            FieldEvaluation(
                field_name="accuracy",
                evaluator_method="",
                expected_value="hello world",
                obtained_value="hello universe",
                score=0.75,
                prompt_hash="abc123"
            )

    def test_whitespace_only_evaluator_method_raises_value_error(self):
        """Test edge case: whitespace-only evaluator_method raises ValueError."""
        with pytest.raises(ValueError, match="evaluator_method.*empty"):
            FieldEvaluation(
                field_name="accuracy",
                evaluator_method="  \t\n  ",
                expected_value="hello world",
                obtained_value="hello universe",
                score=0.75,
                prompt_hash="abc123"
            )

    def test_score_below_zero_raises_value_error(self):
        """Test AC-SPEC-004: score < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="score.*0.0.*1.0"):
            FieldEvaluation(
                field_name="accuracy",
                evaluator_method="bleu",
                expected_value="hello world",
                obtained_value="hello universe",
                score=-0.1,
                prompt_hash="abc123"
            )

    def test_score_above_one_raises_value_error(self):
        """Test AC-SPEC-004: score > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="score.*0.0.*1.0"):
            FieldEvaluation(
                field_name="accuracy",
                evaluator_method="bleu",
                expected_value="hello world",
                obtained_value="hello universe",
                score=1.1,
                prompt_hash="abc123"
            )

    def test_score_exactly_zero_is_valid(self):
        """Test that score=0.0 is a valid boundary value."""
        # Should not raise an exception
        field_eval = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value="hello world",
            obtained_value="goodbye world",
            score=0.0,
            prompt_hash="abc123"
        )
        assert field_eval.score == 0.0

    def test_score_exactly_one_is_valid(self):
        """Test that score=1.0 is a valid boundary value."""
        # Should not raise an exception
        field_eval = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value="hello world",
            obtained_value="hello world",
            score=1.0,
            prompt_hash="abc123"
        )
        assert field_eval.score == 1.0


class TestFieldEvaluationEdgeCases:
    """Test edge cases and special scenarios."""

    def test_various_data_types_for_expected_and_obtained_values(self):
        """Test that expected_value and obtained_value accept Any type."""
        test_cases = [
            ("string", "string"),
            (42, 43),
            ([1, 2, 3], [1, 2, 4]),
            ({"key": "value"}, {"key": "different"}),
            (None, "something"),
            ("something", None),
            (True, False),
        ]

        for expected, obtained in test_cases:
            field_eval = FieldEvaluation(
                field_name="test_field",
                evaluator_method="test_method",
                expected_value=expected,
                obtained_value=obtained,
                score=0.5,
                prompt_hash="test_hash"
            )
            assert field_eval.expected_value == expected
            assert field_eval.obtained_value == obtained

    def test_metadata_mutability(self):
        """Test that metadata dictionary can be modified after instantiation."""
        field_eval = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="bleu",
            expected_value="hello world",
            obtained_value="hello universe",
            score=0.75,
            prompt_hash="abc123"
        )

        # Metadata should start empty
        assert field_eval.metadata == {}

        # Should be able to add to metadata
        field_eval.metadata["model"] = "gpt-4"
        assert field_eval.metadata["model"] == "gpt-4"

    def test_prompt_hash_none_is_valid(self):
        """Test that prompt_hash=None is valid for non-judge evaluators."""
        field_eval = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="exact_match",
            expected_value="hello world",
            obtained_value="hello universe",
            score=0.0,
            prompt_hash=None
        )
        assert field_eval.prompt_hash is None
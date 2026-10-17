"""Tests for the RunResult dataclass in assayer.models.

These tests verify that RunResult correctly holds input, output, evaluations list,
and token usage according to AC-SPEC-005 and related acceptance criteria.
"""

from typing import Any

from assayer.models import FieldEvaluation, RunResult, TokenUsage


class TestRunResultBasicConstruction:
    """Test basic construction and attribute access for RunResult."""

    def test_run_result_construction_with_all_fields(self):
        """Test that RunResult can be instantiated with all required fields."""
        # Arrange
        input_data = {"question": "What is 2+2?"}
        output_data = {"answer": "4"}
        token_usage = TokenUsage(input_tokens=10, output_tokens=5, cost_usd=0.001)
        evaluation = FieldEvaluation(
            field_name="answer",
            evaluator_method="exact_match",
            expected_value="4",
            obtained_value="4",
            score=1.0,
            prompt_hash=None,
        )
        evaluations = [evaluation]

        # Act
        run_result = RunResult(
            input=input_data, output=output_data, evaluations=evaluations, token_usage=token_usage
        )

        # Assert
        assert run_result.input == input_data
        assert run_result.output == output_data
        assert run_result.evaluations == evaluations
        assert run_result.token_usage == token_usage

    def test_run_result_attributes_return_provided_values(self):
        """Test that RunResult attributes are accessible and return provided values."""
        # Arrange
        input_val = "test input"
        output_val = {"result": 42}
        token_usage = TokenUsage(input_tokens=20, output_tokens=10, cost_usd=None)
        evaluation = FieldEvaluation(
            field_name="result",
            evaluator_method="numeric_check",
            expected_value=42,
            obtained_value=42,
            score=1.0,
            prompt_hash="abcd1234",
        )

        # Act
        run_result = RunResult(
            input=input_val, output=output_val, evaluations=[evaluation], token_usage=token_usage
        )

        # Assert - AC-SPEC-005: RunResult holds input, output, list of FieldEvaluation, and TokenUsage
        assert isinstance(run_result.input, str)
        assert run_result.input == input_val
        assert isinstance(run_result.output, dict)
        assert run_result.output == output_val
        assert isinstance(run_result.evaluations, list)
        assert len(run_result.evaluations) == 1
        assert isinstance(run_result.evaluations[0], FieldEvaluation)
        assert isinstance(run_result.token_usage, TokenUsage)


class TestRunResultEvaluationsDefaulting:
    """Test that evaluations field defaults correctly."""

    def test_run_result_evaluations_defaults_to_empty_list(self):
        """Test that evaluations defaults to empty list when not provided."""
        # Arrange
        input_data = "test"
        output_data = "result"
        token_usage = TokenUsage(input_tokens=5, output_tokens=3, cost_usd=0.0)

        # Act - Note: not providing evaluations parameter
        run_result = RunResult(input=input_data, output=output_data, token_usage=token_usage)

        # Assert
        assert run_result.evaluations == []
        assert isinstance(run_result.evaluations, list)

    def test_run_result_with_empty_evaluations_is_valid(self):
        """Test that RunResult with empty evaluations list is valid."""
        # Arrange
        input_data = {"key": "value"}
        output_data = {"result": "success"}
        token_usage = TokenUsage(input_tokens=15, output_tokens=8, cost_usd=0.002)
        empty_evaluations = []

        # Act
        run_result = RunResult(
            input=input_data,
            output=output_data,
            evaluations=empty_evaluations,
            token_usage=token_usage,
        )

        # Assert
        assert run_result.evaluations == []
        assert len(run_result.evaluations) == 0


class TestRunResultWithVariousDataTypes:
    """Test RunResult with various input/output data types."""

    def test_run_result_with_none_values(self):
        """Test RunResult can handle None as input or output."""
        # Arrange
        token_usage = TokenUsage(input_tokens=0, output_tokens=0, cost_usd=None)

        # Act
        run_result = RunResult(input=None, output=None, token_usage=token_usage)

        # Assert
        assert run_result.input is None
        assert run_result.output is None
        assert run_result.evaluations == []

    def test_run_result_with_complex_data_structures(self):
        """Test RunResult with complex nested data structures."""
        # Arrange
        complex_input = {
            "nested": {"data": [1, 2, 3]},
            "list": ["a", "b", {"c": "d"}],
            "number": 42.5,
        }
        complex_output = [{"response": "first"}, {"response": "second", "metadata": {"score": 0.9}}]
        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)

        # Act
        run_result = RunResult(input=complex_input, output=complex_output, token_usage=token_usage)

        # Assert
        assert run_result.input == complex_input
        assert run_result.output == complex_output


class TestRunResultWithMultipleEvaluations:
    """Test RunResult with multiple FieldEvaluation instances."""

    def test_run_result_with_multiple_evaluations(self):
        """Test RunResult can hold multiple FieldEvaluation instances."""
        # Arrange
        input_data = {"prompt": "Generate a story"}
        output_data = {"story": "Once upon a time...", "length": 100}
        token_usage = TokenUsage(input_tokens=25, output_tokens=75, cost_usd=0.005)

        evaluations = [
            FieldEvaluation(
                field_name="story",
                evaluator_method="llm_judge",
                expected_value="A creative story",
                obtained_value="Once upon a time...",
                score=0.85,
                prompt_hash="hash123",
            ),
            FieldEvaluation(
                field_name="length",
                evaluator_method="exact_match",
                expected_value=100,
                obtained_value=100,
                score=1.0,
                prompt_hash=None,
            ),
        ]

        # Act
        run_result = RunResult(
            input=input_data, output=output_data, evaluations=evaluations, token_usage=token_usage
        )

        # Assert
        assert len(run_result.evaluations) == 2
        assert all(isinstance(eval, FieldEvaluation) for eval in run_result.evaluations)
        assert run_result.evaluations[0].field_name == "story"
        assert run_result.evaluations[1].field_name == "length"


class TestRunResultEdgeCases:
    """Test edge cases for RunResult."""

    def test_run_result_with_zero_token_usage(self):
        """Test RunResult with zero token usage (e.g., cached response)."""
        # Arrange
        input_data = "cached query"
        output_data = "cached result"
        zero_token_usage = TokenUsage(input_tokens=0, output_tokens=0, cost_usd=0.0)

        # Act
        run_result = RunResult(input=input_data, output=output_data, token_usage=zero_token_usage)

        # Assert
        assert run_result.token_usage.input_tokens == 0
        assert run_result.token_usage.output_tokens == 0
        assert run_result.token_usage.cost_usd == 0.0

    def test_run_result_with_evaluation_boundary_scores(self):
        """Test RunResult with evaluations having boundary scores (0.0 and 1.0)."""
        # Arrange
        input_data = "test"
        output_data = "response"
        token_usage = TokenUsage(input_tokens=10, output_tokens=5, cost_usd=None)

        evaluations = [
            FieldEvaluation(
                field_name="perfect",
                evaluator_method="test",
                expected_value="match",
                obtained_value="match",
                score=1.0,  # perfect score
                prompt_hash=None,
            ),
            FieldEvaluation(
                field_name="failure",
                evaluator_method="test",
                expected_value="expected",
                obtained_value="wrong",
                score=0.0,  # worst score
                prompt_hash=None,
            ),
        ]

        # Act
        run_result = RunResult(
            input=input_data, output=output_data, evaluations=evaluations, token_usage=token_usage
        )

        # Assert
        assert run_result.evaluations[0].score == 1.0
        assert run_result.evaluations[1].score == 0.0

    def test_run_result_mutability(self):
        """Test that RunResult is mutable (not frozen)."""
        # Arrange
        initial_input = "initial"
        token_usage = TokenUsage(input_tokens=5, output_tokens=3, cost_usd=None)

        # Act
        run_result = RunResult(
            input=initial_input, output="initial_output", token_usage=token_usage
        )

        # Modify the run_result
        run_result.input = "modified"
        new_evaluation = FieldEvaluation(
            field_name="new_field",
            evaluator_method="new_method",
            expected_value="expected",
            obtained_value="actual",
            score=0.5,
            prompt_hash=None,
        )
        run_result.evaluations.append(new_evaluation)

        # Assert
        assert run_result.input == "modified"
        assert len(run_result.evaluations) == 1
        assert run_result.evaluations[0].field_name == "new_field"


class TestRunResultTypeCompatibility:
    """Test that RunResult works with the expected types from the spec."""

    def test_run_result_typing_compatibility(self):
        """Test that RunResult fields match the expected type annotations."""
        # Arrange
        input_val: Any = {"test": "data"}
        output_val: Any = ["result1", "result2"]
        evaluations_val: list[FieldEvaluation] = []
        token_usage_val: TokenUsage = TokenUsage(input_tokens=1, output_tokens=1, cost_usd=1.0)

        # Act
        run_result = RunResult(
            input=input_val,
            output=output_val,
            evaluations=evaluations_val,
            token_usage=token_usage_val,
        )

        # Assert - verify types match expected annotations
        assert isinstance(run_result.input, dict)  # Any allows dict
        assert isinstance(run_result.output, list)  # Any allows list
        assert isinstance(run_result.evaluations, list)
        assert isinstance(run_result.token_usage, TokenUsage)

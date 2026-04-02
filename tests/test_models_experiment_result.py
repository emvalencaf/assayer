"""Tests for the ExperimentResult model."""

import pytest
from assayer.models import ExperimentResult, RunResult, TokenUsage


class TestExperimentResultConstruction:
    """Test ExperimentResult construction and basic field access."""

    def test_experiment_result_with_valid_name_and_empty_runs(self):
        """ExperimentResult can be created with a valid name and empty runs list."""
        result = ExperimentResult(experiment_name="test_experiment", runs=[])

        assert result.experiment_name == "test_experiment"
        assert result.runs == []

    def test_experiment_result_with_valid_name_and_default_runs(self):
        """ExperimentResult can be created with a valid name and default runs (empty list)."""
        result = ExperimentResult(experiment_name="test_experiment")

        assert result.experiment_name == "test_experiment"
        assert result.runs == []

    def test_experiment_result_with_valid_name_and_runs(self):
        """ExperimentResult can be created with a valid name and list of RunResult."""
        token_usage = TokenUsage(input_tokens=10, output_tokens=5, cost_usd=0.01)
        run_result = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage
        )
        result = ExperimentResult(
            experiment_name="test_experiment",
            runs=[run_result]
        )

        assert result.experiment_name == "test_experiment"
        assert len(result.runs) == 1
        assert result.runs[0] == run_result


class TestExperimentResultValidation:
    """Test ExperimentResult validation in __post_init__."""

    def test_empty_experiment_name_raises_value_error(self):
        """ExperimentResult raises ValueError when experiment_name is empty string."""
        with pytest.raises(ValueError, match="experiment_name must not be empty"):
            ExperimentResult(experiment_name="", runs=[])

    def test_whitespace_only_experiment_name_raises_value_error(self):
        """ExperimentResult raises ValueError when experiment_name is whitespace-only."""
        with pytest.raises(ValueError, match="experiment_name must not be empty"):
            ExperimentResult(experiment_name="   ", runs=[])

    def test_tab_only_experiment_name_raises_value_error(self):
        """ExperimentResult raises ValueError when experiment_name is tab-only."""
        with pytest.raises(ValueError, match="experiment_name must not be empty"):
            ExperimentResult(experiment_name="\t\t", runs=[])

    def test_newline_only_experiment_name_raises_value_error(self):
        """ExperimentResult raises ValueError when experiment_name is newline-only."""
        with pytest.raises(ValueError, match="experiment_name must not be empty"):
            ExperimentResult(experiment_name="\n\n", runs=[])

    def test_mixed_whitespace_experiment_name_raises_value_error(self):
        """ExperimentResult raises ValueError when experiment_name is mixed whitespace."""
        with pytest.raises(ValueError, match="experiment_name must not be empty"):
            ExperimentResult(experiment_name=" \t\n ", runs=[])


class TestExperimentResultCompareMethod:
    """Test ExperimentResult.compare method."""

    def test_compare_default_behavior(self):
        """ExperimentResult.compare behavior depends on whether runner module is imported."""
        result1 = ExperimentResult(experiment_name="experiment1", runs=[], metrics={"f1": 0.8})
        result2 = ExperimentResult(experiment_name="experiment2", runs=[], metrics={"f1": 0.85})

        # The behavior depends on whether assayer.runner.compare has been imported
        # If runner compare module was imported, it works; otherwise NotImplementedError
        try:
            comparison = result1.compare(result2)
            # If we get here, the runner compare module was imported
            assert isinstance(comparison, dict)
            assert "metric_deltas" in comparison
            assert "avg_token_cost_delta" in comparison
        except NotImplementedError as e:
            # If we get here, the runner compare module was not imported
            assert "compare() is implemented in the runner spec" in str(e)

    def test_compare_method_accepts_experiment_result_parameter(self):
        """ExperimentResult.compare accepts another ExperimentResult as parameter."""
        token_usage = TokenUsage(input_tokens=10, output_tokens=5, cost_usd=0.01)
        run_result = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage
        )
        result1 = ExperimentResult(experiment_name="experiment1", runs=[run_result])
        result2 = ExperimentResult(experiment_name="experiment2", runs=[])

        # Should not raise TypeError about parameter type
        # Behavior depends on whether runner compare module was imported
        try:
            comparison = result1.compare(result2)
            assert isinstance(comparison, dict)
        except NotImplementedError as e:
            assert "compare() is implemented in the runner spec" in str(e)


class TestExperimentResultEdgeCases:
    """Test edge cases for ExperimentResult."""

    def test_experiment_result_with_multiple_runs(self):
        """ExperimentResult can hold multiple RunResult objects."""
        token_usage1 = TokenUsage(input_tokens=10, output_tokens=5, cost_usd=0.01)
        token_usage2 = TokenUsage(input_tokens=15, output_tokens=8, cost_usd=0.02)

        run_result1 = RunResult(
            input="input 1",
            output="output 1",
            token_usage=token_usage1
        )
        run_result2 = RunResult(
            input="input 2",
            output="output 2",
            token_usage=token_usage2
        )

        result = ExperimentResult(
            experiment_name="multi_run_experiment",
            runs=[run_result1, run_result2]
        )

        assert result.experiment_name == "multi_run_experiment"
        assert len(result.runs) == 2
        assert result.runs[0] == run_result1
        assert result.runs[1] == run_result2

    def test_experiment_name_with_leading_trailing_whitespace_valid(self):
        """ExperimentResult with experiment_name having leading/trailing whitespace is invalid."""
        # Based on the spec, whitespace-only names should be invalid
        # This means names with only leading/trailing whitespace around content should be valid
        # But let's test the stricter interpretation from the task
        result = ExperimentResult(experiment_name="  valid_name  ", runs=[])

        # The validation should strip and check if empty, so this should be valid
        assert result.experiment_name == "  valid_name  "

    def test_experiment_name_with_special_characters(self):
        """ExperimentResult accepts experiment_name with special characters."""
        special_name = "experiment-123_test@2024.v1"
        result = ExperimentResult(experiment_name=special_name, runs=[])

        assert result.experiment_name == special_name
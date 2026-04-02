"""Tests for experiment comparison functionality.

Tests the compare_experiments function and ExperimentResult.compare() method
that compute metric deltas and token cost differences between experiments.
"""

import pytest
from assayer.models import ExperimentResult, RunResult, TokenUsage, FieldEvaluation
from assayer.runner.compare import compare_experiments


class TestCompareExperiments:
    """Test cases for the compare_experiments function."""

    def test_returns_expected_structure(self):
        """Test that compare_experiments returns a dict with required keys."""
        baseline = ExperimentResult(
            experiment_name="baseline",
            runs=[],
            metrics={}
        )
        candidate = ExperimentResult(
            experiment_name="candidate",
            runs=[],
            metrics={}
        )

        result = compare_experiments(baseline, candidate)

        assert isinstance(result, dict)
        assert "metric_deltas" in result
        assert "avg_token_cost_delta" in result
        assert isinstance(result["metric_deltas"], dict)
        assert isinstance(result["avg_token_cost_delta"], dict)

        # Check avg_token_cost_delta structure
        cost_delta = result["avg_token_cost_delta"]
        assert "input_tokens" in cost_delta
        assert "output_tokens" in cost_delta
        assert "cost_usd" in cost_delta

    def test_metric_deltas_for_shared_metrics(self):
        """Test metric_deltas calculation for metrics present in both experiments."""
        baseline = ExperimentResult(
            experiment_name="baseline",
            runs=[],
            metrics={"f1": 0.8, "bleu": 0.6, "accuracy": 0.75}
        )
        candidate = ExperimentResult(
            experiment_name="candidate",
            runs=[],
            metrics={"f1": 0.85, "bleu": 0.55, "accuracy": 0.80}
        )

        result = compare_experiments(baseline, candidate)
        metric_deltas = result["metric_deltas"]

        assert metric_deltas["f1"] == pytest.approx(0.05)
        assert metric_deltas["bleu"] == pytest.approx(-0.05)
        assert metric_deltas["accuracy"] == pytest.approx(0.05)

    def test_metric_deltas_for_missing_metrics(self):
        """Test metric_deltas returns None for metrics present in only one experiment."""
        baseline = ExperimentResult(
            experiment_name="baseline",
            runs=[],
            metrics={"f1": 0.8, "rouge": 0.7}
        )
        candidate = ExperimentResult(
            experiment_name="candidate",
            runs=[],
            metrics={"f1": 0.85, "bleu": 0.6}
        )

        result = compare_experiments(baseline, candidate)
        metric_deltas = result["metric_deltas"]

        assert metric_deltas["f1"] == pytest.approx(0.05)  # shared metric
        assert metric_deltas["rouge"] is None  # only in baseline
        assert metric_deltas["bleu"] is None   # only in candidate

    def test_token_cost_delta_with_pricing(self):
        """Test avg_token_cost_delta calculation when both experiments have pricing."""
        baseline_runs = [
            RunResult(
                input="test1",
                output="output1",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
            ),
            RunResult(
                input="test2",
                output="output2",
                token_usage=TokenUsage(input_tokens=120, output_tokens=60, cost_usd=0.012)
            )
        ]
        candidate_runs = [
            RunResult(
                input="test1",
                output="output1",
                token_usage=TokenUsage(input_tokens=110, output_tokens=45, cost_usd=0.011)
            ),
            RunResult(
                input="test2",
                output="output2",
                token_usage=TokenUsage(input_tokens=130, output_tokens=55, cost_usd=0.013)
            )
        ]

        baseline = ExperimentResult("baseline", runs=baseline_runs, metrics={})
        candidate = ExperimentResult("candidate", runs=candidate_runs, metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        # baseline avg: input=110, output=55, cost=0.011
        # candidate avg: input=120, output=50, cost=0.012
        assert cost_delta["input_tokens"] == pytest.approx(10.0)
        assert cost_delta["output_tokens"] == pytest.approx(-5.0)
        assert cost_delta["cost_usd"] == pytest.approx(0.001)

    def test_token_cost_delta_missing_pricing(self):
        """Test avg_token_cost_delta.cost_usd is None when either experiment lacks pricing."""
        baseline_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
            )
        ]
        candidate_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=110, output_tokens=45, cost_usd=None)
            )
        ]

        baseline = ExperimentResult("baseline", runs=baseline_runs, metrics={})
        candidate = ExperimentResult("candidate", runs=candidate_runs, metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        assert cost_delta["input_tokens"] == pytest.approx(10.0)
        assert cost_delta["output_tokens"] == pytest.approx(-5.0)
        assert cost_delta["cost_usd"] is None

    def test_token_cost_delta_both_missing_pricing(self):
        """Test avg_token_cost_delta.cost_usd is None when both experiments lack pricing."""
        baseline_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=None)
            )
        ]
        candidate_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=110, output_tokens=45, cost_usd=None)
            )
        ]

        baseline = ExperimentResult("baseline", runs=baseline_runs, metrics={})
        candidate = ExperimentResult("candidate", runs=candidate_runs, metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        assert cost_delta["input_tokens"] == pytest.approx(10.0)
        assert cost_delta["output_tokens"] == pytest.approx(-5.0)
        assert cost_delta["cost_usd"] is None

    def test_empty_datasets_handling(self):
        """Test that empty datasets are handled without raising exceptions."""
        # Both empty
        baseline = ExperimentResult("baseline", runs=[], metrics={})
        candidate = ExperimentResult("candidate", runs=[], metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        # When _avg() returns None for empty datasets, None - None should be handled
        assert cost_delta["input_tokens"] is None or cost_delta["input_tokens"] == 0
        assert cost_delta["output_tokens"] is None or cost_delta["output_tokens"] == 0
        assert cost_delta["cost_usd"] is None

        # One empty, one non-empty
        candidate_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
            )
        ]
        candidate = ExperimentResult("candidate", runs=candidate_runs, metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        # Should handle None - value or value - None
        assert isinstance(cost_delta["input_tokens"], (float, type(None)))
        assert isinstance(cost_delta["output_tokens"], (float, type(None)))
        assert cost_delta["cost_usd"] is None

    def test_partial_token_data(self):
        """Test handling when some runs have None values for token fields."""
        baseline_runs = [
            RunResult(
                input="test1",
                output="output1",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
            ),
            RunResult(
                input="test2",
                output="output2",
                token_usage=TokenUsage(input_tokens=120, output_tokens=60, cost_usd=None)
            )
        ]
        candidate_runs = [
            RunResult(
                input="test1",
                output="output1",
                token_usage=TokenUsage(input_tokens=110, output_tokens=45, cost_usd=0.011)
            )
        ]

        baseline = ExperimentResult("baseline", runs=baseline_runs, metrics={})
        candidate = ExperimentResult("candidate", runs=candidate_runs, metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        # Should calculate averages only from non-None values
        assert isinstance(cost_delta["input_tokens"], float)
        assert isinstance(cost_delta["output_tokens"], float)
        assert cost_delta["cost_usd"] is None  # baseline has mixed pricing

    def test_experiment_result_compare_delegation(self):
        """Test that ExperimentResult.compare() delegates to compare_experiments after monkey-patching."""
        # The compare module is imported at the top of this file, which triggers monkey-patching
        baseline = ExperimentResult("baseline", runs=[], metrics={"f1": 0.8})
        candidate = ExperimentResult("candidate", runs=[], metrics={"f1": 0.85})

        # Test that the method works and returns expected structure
        result = baseline.compare(candidate)

        assert isinstance(result, dict)
        assert "metric_deltas" in result
        assert "avg_token_cost_delta" in result
        assert result["metric_deltas"]["f1"] == pytest.approx(0.05)

    def test_all_metrics_from_both_experiments_included(self):
        """Test that metric_deltas includes all metrics from both experiments."""
        baseline = ExperimentResult(
            experiment_name="baseline",
            runs=[],
            metrics={"metric_a": 0.1, "metric_b": 0.2}
        )
        candidate = ExperimentResult(
            experiment_name="candidate",
            runs=[],
            metrics={"metric_b": 0.25, "metric_c": 0.3}
        )

        result = compare_experiments(baseline, candidate)
        metric_deltas = result["metric_deltas"]

        # Should have all metrics from both experiments
        assert set(metric_deltas.keys()) == {"metric_a", "metric_b", "metric_c"}
        assert metric_deltas["metric_a"] is None  # only in baseline
        assert metric_deltas["metric_b"] == pytest.approx(0.05)  # shared
        assert metric_deltas["metric_c"] is None  # only in candidate

    def test_zero_metric_values(self):
        """Test handling of zero metric values."""
        baseline = ExperimentResult("baseline", runs=[], metrics={"f1": 0.0})
        candidate = ExperimentResult("candidate", runs=[], metrics={"f1": 0.1})

        result = compare_experiments(baseline, candidate)
        metric_deltas = result["metric_deltas"]

        assert metric_deltas["f1"] == pytest.approx(0.1)

    def test_negative_metric_deltas(self):
        """Test that negative deltas are handled correctly."""
        baseline = ExperimentResult("baseline", runs=[], metrics={"error_rate": 0.3})
        candidate = ExperimentResult("candidate", runs=[], metrics={"error_rate": 0.2})

        result = compare_experiments(baseline, candidate)
        metric_deltas = result["metric_deltas"]

        assert metric_deltas["error_rate"] == pytest.approx(-0.1)

    @pytest.mark.parametrize("baseline_cost,candidate_cost,expected", [
        (None, None, None),
        (0.01, None, None),
        (None, 0.02, None),
        (0.01, 0.02, 0.01)
    ])
    def test_cost_delta_combinations(self, baseline_cost, candidate_cost, expected):
        """Test various combinations of cost values."""
        baseline_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=baseline_cost)
            )
        ]
        candidate_runs = [
            RunResult(
                input="test",
                output="output",
                token_usage=TokenUsage(input_tokens=100, output_tokens=50, cost_usd=candidate_cost)
            )
        ]

        baseline = ExperimentResult("baseline", runs=baseline_runs, metrics={})
        candidate = ExperimentResult("candidate", runs=candidate_runs, metrics={})

        result = compare_experiments(baseline, candidate)
        cost_delta = result["avg_token_cost_delta"]

        if expected is None:
            assert cost_delta["cost_usd"] is None
        else:
            assert cost_delta["cost_usd"] == pytest.approx(expected)
"""Test cases for EvaluationPipeline.

This module contains comprehensive tests for the EvaluationPipeline class,
covering initialization, execution, validation, error handling, and integration
with all runner components.
"""

import json
import tempfile
from typing import Any, Callable
from unittest.mock import MagicMock

import pytest

from assayer.models import ExperimentResult, RunResult, TokenUsage, FieldEvaluation
from assayer.runner.pricing import PricingConfig
from assayer.runner.pipeline import EvaluationPipeline
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry
from assayer.evaluators.base import BaseEvaluator


class MockEvaluator(BaseEvaluator):
    """Mock evaluator for testing purposes."""

    def __init__(self, name: str, field_name: str = None) -> None:
        super().__init__(name)
        self.field_name = field_name or "default"

    def evaluate(self, prediction: Any, reference: Any, **kwargs: Any) -> FieldEvaluation:
        """Return a mock evaluation result."""
        score = 0.8 if prediction == reference else 0.5
        return FieldEvaluation(
            field_name=self.field_name,
            evaluator_method=self.name,
            expected_value=reference,
            obtained_value=prediction,
            score=score,
            prompt_hash=None,
            metadata={}
        )


class MockResult:
    """Mock result object with usage metadata."""

    def __init__(self, output: Any, input_tokens: int = 10, output_tokens: int = 20):
        self.output = output
        self.usage_metadata = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }

    def __getitem__(self, key):
        # Support dict-like access to output
        if hasattr(self.output, "__getitem__"):
            return self.output[key]
        return self.output


class TestEvaluationPipelineInit:
    """Test EvaluationPipeline initialization and validation."""

    def test_init_with_valid_params(self):
        """Test successful initialization with valid parameters."""
        evaluator_registry = EvaluatorRegistry()
        evaluator_registry.register("mock_eval", MockEvaluator)

        metric_registry = MetricRegistry()
        metric_registry.register("accuracy", lambda preds, refs: 0.85)

        target_fn = lambda x: f"output_{x}"
        dataset = [{"input": "test", "expected_output": "expected"}]
        field_evaluators = {"field": ["mock_eval"]}
        metrics = ["accuracy"]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators=field_evaluators,
            metrics=metrics,
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
            experiment_name="test_experiment"
        )

        assert pipeline is not None

    def test_init_with_pricing_config(self):
        """Test initialization with pricing configuration."""
        evaluator_registry = EvaluatorRegistry()
        evaluator_registry.register("mock_eval", MockEvaluator)

        metric_registry = MetricRegistry()
        metric_registry.register("accuracy", lambda preds, refs: 0.85)

        pricing_config = PricingConfig(
            cost_per_input_token=0.001,
            cost_per_output_token=0.002
        )

        pipeline = EvaluationPipeline(
            target_fn=lambda x: x,
            dataset=[{"input": "test", "expected_output": "expected"}],
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
            pricing_config=pricing_config
        )

        assert pipeline is not None

    def test_init_invalid_evaluator_raises_keyerror(self):
        """Test that invalid evaluator name raises KeyError before execution."""
        evaluator_registry = EvaluatorRegistry()
        # Don't register any evaluators

        metric_registry = MetricRegistry()
        metric_registry.register("accuracy", lambda preds, refs: 0.85)

        with pytest.raises(KeyError, match="invalid_evaluator"):
            EvaluationPipeline(
                target_fn=lambda x: x,
                dataset=[{"input": "test", "expected_output": "expected"}],
                field_evaluators={"field": ["invalid_evaluator"]},
                metrics=["accuracy"],
                evaluator_registry=evaluator_registry,
                metric_registry=metric_registry
            )

    def test_init_invalid_metric_raises_keyerror(self):
        """Test that invalid metric name raises KeyError before execution."""
        evaluator_registry = EvaluatorRegistry()
        evaluator_registry.register("mock_eval", MockEvaluator)

        metric_registry = MetricRegistry()
        # Don't register any metrics

        with pytest.raises(KeyError, match="invalid_metric"):
            EvaluationPipeline(
                target_fn=lambda x: x,
                dataset=[{"input": "test", "expected_output": "expected"}],
                field_evaluators={"field": ["mock_eval"]},
                metrics=["invalid_metric"],
                evaluator_registry=evaluator_registry,
                metric_registry=metric_registry
            )


class TestEvaluationPipelineRun:
    """Test EvaluationPipeline.run() method execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator_registry = EvaluatorRegistry()
        self.evaluator_registry.register("mock_eval", MockEvaluator)

        self.metric_registry = MetricRegistry()
        self.metric_registry.register("accuracy", self._accuracy_metric)
        self.metric_registry.register("f1", self._f1_metric)

    def _accuracy_metric(self, predictions: list[Any], references: list[Any]) -> float:
        """Mock accuracy metric."""
        if not predictions or not references:
            return 0.0
        return sum(p == r for p, r in zip(predictions, references)) / len(predictions)

    def _f1_metric(self, predictions: list[Any], references: list[Any]) -> float:
        """Mock F1 metric."""
        return 0.75  # Fixed value for testing

    def test_run_single_example_returns_experiment_result(self):
        """Test run() with single example returns ExperimentResult with one RunResult."""
        def target_fn(input_val):
            result = MockResult("output_value")
            return result

        dataset = [{"input": "test_input", "expected_output": "expected_output"}]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry,
            experiment_name="single_example_test"
        )

        result = pipeline.run()

        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "single_example_test"
        assert len(result.runs) == 1
        assert hasattr(result, 'metrics')  # Should have metrics field
        assert isinstance(result.metrics, dict)
        assert "accuracy" in result.metrics

    def test_run_multiple_examples_correct_count(self):
        """Test run() with N examples returns ExperimentResult with exactly N RunResults."""
        def target_fn(input_val):
            return MockResult(f"output_{input_val}")

        dataset = [
            {"input": "test1", "expected_output": "expected1"},
            {"input": "test2", "expected_output": "expected2"},
            {"input": "test3", "expected_output": "expected3"},
        ]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        assert len(result.runs) == 3
        assert all(isinstance(run, RunResult) for run in result.runs)

    def test_run_populates_token_usage(self):
        """Test that each RunResult.token_usage is populated."""
        def target_fn(input_val):
            return MockResult("output", input_tokens=15, output_tokens=25)

        dataset = [{"input": "test", "expected_output": "expected"}]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        run_result = result.runs[0]
        assert isinstance(run_result.token_usage, TokenUsage)
        assert run_result.token_usage.input_tokens == 15
        assert run_result.token_usage.output_tokens == 25
        assert run_result.token_usage.cost_usd is None  # No pricing config

    def test_run_with_pricing_calculates_cost(self):
        """Test that pricing configuration correctly calculates costs."""
        def target_fn(input_val):
            return MockResult("output", input_tokens=10, output_tokens=20)

        pricing_config = PricingConfig(
            cost_per_input_token=0.001,
            cost_per_output_token=0.002
        )

        dataset = [{"input": "test", "expected_output": "expected"}]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry,
            pricing_config=pricing_config
        )

        result = pipeline.run()

        run_result = result.runs[0]
        expected_cost = 10 * 0.001 + 20 * 0.002  # 0.01 + 0.04 = 0.05
        assert run_result.token_usage.cost_usd == expected_cost

    def test_run_field_evaluations_populated(self):
        """Test that field evaluations are populated for all field-evaluator pairs."""
        def target_fn(input_val):
            return MockResult({"field1": "value1", "field2": "value2"})

        # Register a second evaluator
        self.evaluator_registry.register("second_eval", MockEvaluator)

        dataset = [{"input": "test", "expected_output": {"field1": "expected1", "field2": "expected2"}}]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={
                "field1": ["mock_eval", "second_eval"],
                "field2": ["mock_eval"]
            },
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        run_result = result.runs[0]
        # Should have 3 evaluations: field1 x 2 evaluators + field2 x 1 evaluator
        assert len(run_result.evaluations) == 3

        # Check that all evaluations are FieldEvaluation instances
        assert all(isinstance(eval_result, FieldEvaluation) for eval_result in run_result.evaluations)

        # Check field names
        field_names = [eval_result.field_name for eval_result in run_result.evaluations]
        assert "field1" in field_names
        assert "field2" in field_names

    def test_run_metric_aggregation_after_all_runs(self):
        """Test that metrics are aggregated after all runs and stored in result."""
        call_count = 0

        def counting_metric(predictions, references):
            nonlocal call_count
            call_count += 1
            return 0.8

        self.metric_registry.register("counting_metric", counting_metric)

        def target_fn(input_val):
            return MockResult(f"output_{input_val}")

        dataset = [
            {"input": "test1", "expected_output": "expected1"},
            {"input": "test2", "expected_output": "expected2"},
        ]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["counting_metric"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        # Metric should be called only once, after all runs
        assert call_count == 1
        assert result.metrics["counting_metric"] == 0.8

    def test_run_multiple_metrics(self):
        """Test that multiple metrics are computed and stored."""
        def target_fn(input_val):
            return MockResult("output")

        dataset = [{"input": "test", "expected_output": "expected"}]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy", "f1"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        assert "accuracy" in result.metrics
        assert "f1" in result.metrics
        assert len(result.metrics) == 2

    def test_run_no_usage_metadata_defaults_zero_tokens(self):
        """Test that missing usage_metadata defaults to zero tokens."""
        def target_fn(input_val):
            # Return object without usage_metadata
            result = MagicMock()
            result.usage_metadata = None
            return result

        dataset = [{"input": "test", "expected_output": "expected"}]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        run_result = result.runs[0]
        assert run_result.token_usage.input_tokens == 0
        assert run_result.token_usage.output_tokens == 0
        assert run_result.token_usage.cost_usd is None


class TestEvaluationPipelineEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator_registry = EvaluatorRegistry()
        self.evaluator_registry.register("mock_eval", MockEvaluator)

        self.metric_registry = MetricRegistry()
        self.metric_registry.register("accuracy", lambda preds, refs: 0.0 if not preds else 0.85)

    def test_run_empty_dataset_returns_zero_runs(self):
        """Test that empty dataset returns ExperimentResult with zero runs."""
        def target_fn(input_val):
            return MockResult("output")

        dataset = []

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        assert len(result.runs) == 0
        assert result.metrics["accuracy"] == 0.0  # Metrics should handle empty case

    def test_run_target_fn_exception_propagates_with_index(self):
        """Test that target_fn exceptions propagate with example index."""
        def failing_target_fn(input_val):
            if input_val == "fail":
                raise ValueError("Target function failed")
            return MockResult("output")

        dataset = [
            {"input": "success", "expected_output": "expected"},
            {"input": "fail", "expected_output": "expected"},
        ]

        pipeline = EvaluationPipeline(
            target_fn=failing_target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        with pytest.raises(ValueError, match="Target function failed"):
            pipeline.run()


class TestEvaluationPipelineDatasetLoading:
    """Test dataset loading from various sources."""

    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator_registry = EvaluatorRegistry()
        self.evaluator_registry.register("mock_eval", MockEvaluator)

        self.metric_registry = MetricRegistry()
        self.metric_registry.register("accuracy", lambda preds, refs: 0.85)

    def test_run_with_list_dataset(self):
        """Test run() with dataset as list of dicts."""
        def target_fn(input_val):
            return MockResult(f"output_{input_val}")

        dataset = [
            {"input": "test1", "expected_output": "expected1"},
            {"input": "test2", "expected_output": "expected2"},
        ]

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={"field": ["mock_eval"]},
            metrics=["accuracy"],
            evaluator_registry=self.evaluator_registry,
            metric_registry=self.metric_registry
        )

        result = pipeline.run()

        assert len(result.runs) == 2
        assert result.runs[0].input == "test1"
        assert result.runs[1].input == "test2"

    def test_run_with_json_file_dataset(self):
        """Test run() with dataset loaded from JSON file."""
        dataset_content = [
            {"input": "file_input1", "expected_output": "file_expected1"},
            {"input": "file_input2", "expected_output": "file_expected2"},
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset_content, f)
            temp_file_path = f.name

        try:
            def target_fn(input_val):
                return MockResult(f"output_{input_val}")

            pipeline = EvaluationPipeline(
                target_fn=target_fn,
                dataset=temp_file_path,  # Pass file path as string
                field_evaluators={"field": ["mock_eval"]},
                metrics=["accuracy"],
                evaluator_registry=self.evaluator_registry,
                metric_registry=self.metric_registry
            )

            result = pipeline.run()

            assert len(result.runs) == 2
            assert result.runs[0].input == "file_input1"
            assert result.runs[1].input == "file_input2"
        finally:
            import os
            os.unlink(temp_file_path)


class TestEvaluationPipelineIntegration:
    """Integration tests for EvaluationPipeline with all components."""

    def test_full_pipeline_integration(self):
        """Test complete pipeline with all components working together."""
        evaluator_registry = EvaluatorRegistry()
        evaluator_registry.register("test_evaluator", MockEvaluator)

        metric_registry = MetricRegistry()

        def accuracy_metric(predictions, references):
            if not predictions:
                return 0.0
            return sum(p == r for p, r in zip(predictions, references)) / len(predictions)

        def precision_metric(predictions, references):
            return 0.9  # Mock value

        metric_registry.register("accuracy", accuracy_metric)
        metric_registry.register("precision", precision_metric)

        def target_fn(input_val):
            # Simulate LLM call with token usage
            output = {"summary": f"Summary of {input_val}", "score": 0.8}
            result = MockResult(output, input_tokens=50, output_tokens=30)
            return result

        dataset = [
            {"input": "Document 1", "expected_output": {"summary": "Expected summary 1", "score": 0.9}},
            {"input": "Document 2", "expected_output": {"summary": "Expected summary 2", "score": 0.7}},
            {"input": "Document 3", "expected_output": {"summary": "Expected summary 3", "score": 0.8}},
        ]

        pricing_config = PricingConfig(
            cost_per_input_token=0.0001,
            cost_per_output_token=0.0002
        )

        pipeline = EvaluationPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators={
                "summary": ["test_evaluator"],
                "score": ["test_evaluator"]
            },
            metrics=["accuracy", "precision"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
            pricing_config=pricing_config,
            experiment_name="integration_test"
        )

        result = pipeline.run()

        # Verify experiment structure
        assert isinstance(result, ExperimentResult)
        assert result.experiment_name == "integration_test"
        assert len(result.runs) == 3

        # Verify each run
        for i, run in enumerate(result.runs):
            assert isinstance(run, RunResult)
            assert run.input == f"Document {i + 1}"
            assert isinstance(run.output, MockResult)

            # Check token usage
            assert run.token_usage.input_tokens == 50
            assert run.token_usage.output_tokens == 30
            expected_cost = 50 * 0.0001 + 30 * 0.0002  # 0.005 + 0.006 = 0.011
            assert run.token_usage.cost_usd == expected_cost

            # Check evaluations (2 fields × 1 evaluator each = 2 evaluations per run)
            assert len(run.evaluations) == 2

            evaluation_fields = {eval_result.field_name for eval_result in run.evaluations}
            assert evaluation_fields == {"summary", "score"}

        # Verify metrics
        assert hasattr(result, 'metrics')
        assert isinstance(result.metrics, dict)
        assert "accuracy" in result.metrics
        assert "precision" in result.metrics
        assert result.metrics["precision"] == 0.9

        # Accuracy should be calculated based on actual predictions vs references
        assert isinstance(result.metrics["accuracy"], float)
        assert 0.0 <= result.metrics["accuracy"] <= 1.0
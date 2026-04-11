"""Tests for HistoricalPipeline constructor and fail-fast validation.

Covers:
- Class and module existence
- Constructor signature (no target_fn)
- Instance attribute storage
- Fail-fast KeyError on unregistered metric names
- Fail-fast KeyError on unregistered evaluator names (via FieldRouter)
- Default experiment_name value
- Placeholder run() raises NotImplementedError
- Google-style docstrings and type hints
- run() returns ExperimentResult with correct structure
- run() raises ValueError for missing 'prediction' key
- run() routes through FieldRouter
- RunResult.token_usage is TokenUsage(0, 0, None) for every run
- RunResult.output is set to the record's prediction value
- Aggregate metrics computed via metric_registry.get(name)
- run() Google-style docstring
- run() return type annotation
"""

import inspect
from typing import Any, get_type_hints
from unittest.mock import MagicMock, patch, call

import pytest

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation, ExperimentResult, RunResult, TokenUsage
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

class _StubEvaluator(BaseEvaluator):
    """Minimal evaluator used only for registry population."""

    def evaluate(self, prediction: Any, reference: Any, **kwargs: Any) -> FieldEvaluation:
        """Return a fixed stub evaluation."""
        return FieldEvaluation(
            field_name="stub",
            evaluator_method=self.name,
            expected_value=reference,
            obtained_value=prediction,
            score=1.0,
            prompt_hash=None,
            metadata={},
        )


@pytest.fixture()
def evaluator_registry() -> EvaluatorRegistry:
    """Return a registry pre-populated with one evaluator."""
    reg = EvaluatorRegistry()
    reg.register("stub_eval", _StubEvaluator)
    return reg


@pytest.fixture()
def metric_registry() -> MetricRegistry:
    """Return a registry pre-populated with one metric."""
    reg = MetricRegistry()
    reg.register("accuracy", lambda preds, refs: 0.9)
    return reg


@pytest.fixture()
def minimal_dataset() -> list[dict]:
    """Return a minimal one-row dataset."""
    return [{"input": "hello", "expected_output": "world"}]


# ---------------------------------------------------------------------------
# 1. Import / existence
# ---------------------------------------------------------------------------

class TestHistoricalPipelineImport:
    """HistoricalPipeline exists and is importable."""

    def test_class_importable(self):
        """HistoricalPipeline can be imported from its module."""
        from assayer.runner.historical_pipeline import HistoricalPipeline  # noqa: F401

    def test_class_is_a_class(self):
        """HistoricalPipeline is a proper class."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert inspect.isclass(HistoricalPipeline)


# ---------------------------------------------------------------------------
# 2. Constructor signature
# ---------------------------------------------------------------------------

class TestHistoricalPipelineSignature:
    """Constructor has the expected parameters and no target_fn."""

    def _get_params(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        return list(inspect.signature(HistoricalPipeline.__init__).parameters.keys())

    def test_has_dataset_param(self):
        assert "dataset" in self._get_params()

    def test_has_field_evaluators_param(self):
        assert "field_evaluators" in self._get_params()

    def test_has_metrics_param(self):
        assert "metrics" in self._get_params()

    def test_has_evaluator_registry_param(self):
        assert "evaluator_registry" in self._get_params()

    def test_has_metric_registry_param(self):
        assert "metric_registry" in self._get_params()

    def test_has_experiment_name_param(self):
        assert "experiment_name" in self._get_params()

    def test_no_target_fn_param(self):
        """target_fn must NOT be present in the constructor."""
        assert "target_fn" not in self._get_params()

    def test_experiment_name_has_default(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        sig = inspect.signature(HistoricalPipeline.__init__)
        param = sig.parameters["experiment_name"]
        assert param.default != inspect.Parameter.empty
        assert param.default == "unnamed_experiment"

    def test_init_return_annotation_is_none(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        sig = inspect.signature(HistoricalPipeline.__init__)
        assert sig.return_annotation in (None, type(None))


# ---------------------------------------------------------------------------
# 3. Successful construction and attribute storage
# ---------------------------------------------------------------------------

class TestHistoricalPipelineInitSuccess:
    """Valid arguments produce a properly configured instance."""

    def test_constructs_without_error(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline is not None

    def test_stores_dataset_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.dataset is minimal_dataset

    def test_stores_field_evaluators_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        fe = {"stub": ["stub_eval"]}
        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators=fe,
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.field_evaluators is fe

    def test_stores_metrics_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.metrics == ["accuracy"]

    def test_stores_evaluator_registry_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.evaluator_registry is evaluator_registry

    def test_stores_metric_registry_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.metric_registry is metric_registry

    def test_stores_experiment_name_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
            experiment_name="my_experiment",
        )
        assert pipeline.experiment_name == "my_experiment"

    def test_default_experiment_name_is_unnamed_experiment(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.experiment_name == "unnamed_experiment"

    def test_stores_field_router_as_private_attribute(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline
        from assayer.runner.field_router import FieldRouter

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert hasattr(pipeline, "_field_router")
        assert isinstance(pipeline._field_router, FieldRouter)

    def test_accepts_dataset_as_string_path(
        self,
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
        tmp_path,
    ):
        """Constructor must accept a file-path string for dataset without error."""
        import json

        from assayer.runner.historical_pipeline import HistoricalPipeline

        dataset_file = tmp_path / "dataset.json"
        dataset_file.write_text(
            json.dumps([{"input": "a", "expected_output": "b"}])
        )

        # Should not raise; the path is stored; actual loading happens in run()
        pipeline = HistoricalPipeline(
            dataset=str(dataset_file),
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline is not None

    def test_empty_metrics_list_constructs_without_error(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=[],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert pipeline.metrics == []


# ---------------------------------------------------------------------------
# 4. Fail-fast validation — unregistered metrics
# ---------------------------------------------------------------------------

class TestHistoricalPipelineMetricValidation:
    """KeyError is raised immediately for unregistered metric names."""

    def test_single_unregistered_metric_raises_keyerror(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        empty_metric_registry = MetricRegistry()

        with pytest.raises(KeyError):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"stub": ["stub_eval"]},
                metrics=["nonexistent_metric"],
                evaluator_registry=evaluator_registry,
                metric_registry=empty_metric_registry,
            )

    def test_unregistered_metric_error_contains_metric_name(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        empty_metric_registry = MetricRegistry()

        with pytest.raises(KeyError, match="ghost_metric"):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"stub": ["stub_eval"]},
                metrics=["ghost_metric"],
                evaluator_registry=evaluator_registry,
                metric_registry=empty_metric_registry,
            )

    def test_mixed_valid_invalid_metrics_raises_keyerror(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """Even if some metrics are valid, a single invalid one must raise."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        with pytest.raises(KeyError):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"stub": ["stub_eval"]},
                metrics=["accuracy", "does_not_exist"],
                evaluator_registry=evaluator_registry,
                metric_registry=metric_registry,
            )

    def test_validation_happens_at_construction_not_at_run(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
    ):
        """KeyError must be raised during __init__, not deferred to run()."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        empty_metric_registry = MetricRegistry()

        with pytest.raises(KeyError):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"stub": ["stub_eval"]},
                metrics=["missing"],
                evaluator_registry=evaluator_registry,
                metric_registry=empty_metric_registry,
            )


# ---------------------------------------------------------------------------
# 5. Fail-fast validation — unregistered evaluators (via FieldRouter)
# ---------------------------------------------------------------------------

class TestHistoricalPipelineEvaluatorValidation:
    """KeyError is raised immediately for unregistered evaluator names."""

    def test_single_unregistered_evaluator_raises_keyerror(
        self,
        minimal_dataset: list[dict],
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        empty_evaluator_registry = EvaluatorRegistry()

        with pytest.raises(KeyError):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"field": ["nonexistent_eval"]},
                metrics=["accuracy"],
                evaluator_registry=empty_evaluator_registry,
                metric_registry=metric_registry,
            )

    def test_unregistered_evaluator_error_contains_evaluator_name(
        self,
        minimal_dataset: list[dict],
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        empty_evaluator_registry = EvaluatorRegistry()

        with pytest.raises(KeyError, match="phantom_eval"):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"field": ["phantom_eval"]},
                metrics=["accuracy"],
                evaluator_registry=empty_evaluator_registry,
                metric_registry=metric_registry,
            )

    def test_invalid_evaluator_in_second_field_raises_keyerror(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """Evaluator validation covers all fields, not just the first."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        with pytest.raises(KeyError):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={
                    "field_a": ["stub_eval"],
                    "field_b": ["not_registered"],
                },
                metrics=["accuracy"],
                evaluator_registry=evaluator_registry,
                metric_registry=metric_registry,
            )

    def test_evaluator_validation_happens_at_construction(
        self,
        minimal_dataset: list[dict],
        metric_registry: MetricRegistry,
    ):
        """KeyError must be raised during __init__, not deferred to run()."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        empty_evaluator_registry = EvaluatorRegistry()

        with pytest.raises(KeyError):
            HistoricalPipeline(
                dataset=minimal_dataset,
                field_evaluators={"field": ["missing_eval"]},
                metrics=["accuracy"],
                evaluator_registry=empty_evaluator_registry,
                metric_registry=metric_registry,
            )


# ---------------------------------------------------------------------------
# 6. Placeholder run() method
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunMethod:
    """run() exists and raises NotImplementedError as a placeholder."""

    def test_run_method_exists(
        self,
        minimal_dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=minimal_dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert callable(getattr(pipeline, "run", None))

    def test_run_is_callable(
        self,
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=[],
            field_evaluators={},
            metrics=[],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )
        assert callable(pipeline.run)


# ---------------------------------------------------------------------------
# 7. Docstrings
# ---------------------------------------------------------------------------

class TestHistoricalPipelineDocstrings:
    """Class and __init__ must have Google-style docstrings."""

    def test_class_has_docstring(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert HistoricalPipeline.__doc__ is not None
        assert len(HistoricalPipeline.__doc__.strip()) > 0

    def test_init_has_docstring(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert HistoricalPipeline.__init__.__doc__ is not None
        assert len(HistoricalPipeline.__init__.__doc__.strip()) > 0

    def test_class_docstring_contains_args_section(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert "Args:" in HistoricalPipeline.__doc__

    def test_class_docstring_contains_raises_section(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert "Raises:" in HistoricalPipeline.__doc__

    def test_init_docstring_contains_args_section(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert "Args:" in HistoricalPipeline.__init__.__doc__

    def test_init_docstring_contains_raises_section(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert "Raises:" in HistoricalPipeline.__init__.__doc__


# ---------------------------------------------------------------------------
# 8. Type hints
# ---------------------------------------------------------------------------

class TestHistoricalPipelineTypeHints:
    """All parameters and the return type of __init__ must be annotated."""

    def _get_annotations(self):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        return get_type_hints(HistoricalPipeline.__init__)

    def test_dataset_is_annotated(self):
        assert "dataset" in self._get_annotations()

    def test_field_evaluators_is_annotated(self):
        assert "field_evaluators" in self._get_annotations()

    def test_metrics_is_annotated(self):
        assert "metrics" in self._get_annotations()

    def test_evaluator_registry_is_annotated(self):
        assert "evaluator_registry" in self._get_annotations()

    def test_metric_registry_is_annotated(self):
        assert "metric_registry" in self._get_annotations()

    def test_experiment_name_is_annotated(self):
        assert "experiment_name" in self._get_annotations()

    def test_return_type_is_annotated(self):
        assert "return" in self._get_annotations()


# ---------------------------------------------------------------------------
# 9. run() returns ExperimentResult with correct structure (happy path)
# ---------------------------------------------------------------------------

@pytest.fixture()
def dataset_with_predictions() -> list[dict]:
    """Return a two-row dataset that includes predictions."""
    return [
        {"input": "q1", "expected_output": "a1", "prediction": "p1"},
        {"input": "q2", "expected_output": "a2", "prediction": "p2"},
    ]


@pytest.fixture()
def pipeline_with_predictions(
    dataset_with_predictions: list[dict],
    evaluator_registry: EvaluatorRegistry,
    metric_registry: MetricRegistry,
):
    """Return a HistoricalPipeline configured to use dataset_with_predictions."""
    from assayer.runner.historical_pipeline import HistoricalPipeline

    return HistoricalPipeline(
        dataset=dataset_with_predictions,
        field_evaluators={"stub": ["stub_eval"]},
        metrics=["accuracy"],
        evaluator_registry=evaluator_registry,
        metric_registry=metric_registry,
        experiment_name="test_experiment",
    )


class TestHistoricalPipelineRunReturnsExperimentResult:
    """run() returns ExperimentResult with correct experiment_name, runs, and metrics."""

    def test_run_returns_experiment_result_instance(
        self, pipeline_with_predictions
    ):
        """run() returns an ExperimentResult object."""
        result = pipeline_with_predictions.run()
        assert isinstance(result, ExperimentResult)

    def test_run_experiment_name_matches_constructor(
        self, pipeline_with_predictions
    ):
        """ExperimentResult.experiment_name equals what was passed to constructor."""
        result = pipeline_with_predictions.run()
        assert result.experiment_name == "test_experiment"

    def test_run_returns_one_run_per_record(
        self, pipeline_with_predictions, dataset_with_predictions
    ):
        """ExperimentResult.runs has one RunResult per dataset record."""
        result = pipeline_with_predictions.run()
        assert len(result.runs) == len(dataset_with_predictions)

    def test_run_metrics_contains_registered_metric(
        self, pipeline_with_predictions
    ):
        """ExperimentResult.metrics contains the metric registered in metric_registry."""
        result = pipeline_with_predictions.run()
        assert "accuracy" in result.metrics

    def test_run_metrics_value_matches_registry_function(
        self,
        dataset_with_predictions: list[dict],
        evaluator_registry: EvaluatorRegistry,
    ):
        """The metric value equals what the registered metric function returns."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        sentinel_value = 0.42
        reg = MetricRegistry()
        reg.register("custom_metric", lambda preds, refs: sentinel_value)

        pipeline = HistoricalPipeline(
            dataset=dataset_with_predictions,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["custom_metric"],
            evaluator_registry=evaluator_registry,
            metric_registry=reg,
            experiment_name="sentinel_exp",
        )

        result = pipeline.run()
        assert result.metrics["custom_metric"] == sentinel_value

    def test_run_empty_metrics_list_returns_empty_metrics_dict(
        self,
        dataset_with_predictions: list[dict],
        evaluator_registry: EvaluatorRegistry,
    ):
        """When no metrics are specified, ExperimentResult.metrics is empty."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=dataset_with_predictions,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=[],
            evaluator_registry=evaluator_registry,
            metric_registry=MetricRegistry(),
            experiment_name="no_metrics_exp",
        )

        result = pipeline.run()
        assert result.metrics == {}

    def test_run_default_experiment_name_propagated(
        self,
        dataset_with_predictions: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """ExperimentResult.experiment_name uses 'unnamed_experiment' default."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=dataset_with_predictions,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

        result = pipeline.run()
        assert result.experiment_name == "unnamed_experiment"


# ---------------------------------------------------------------------------
# 10. run() RunResult contents
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunResultContents:
    """Each RunResult has correct input, output, token_usage, and evaluations."""

    def test_run_result_output_equals_prediction(
        self, pipeline_with_predictions, dataset_with_predictions
    ):
        """RunResult.output is the record's 'prediction' value, not 'expected_output'."""
        result = pipeline_with_predictions.run()
        for i, run in enumerate(result.runs):
            assert run.output == dataset_with_predictions[i]["prediction"]

    def test_run_result_input_equals_record_input(
        self, pipeline_with_predictions, dataset_with_predictions
    ):
        """RunResult.input is the record's 'input' value."""
        result = pipeline_with_predictions.run()
        for i, run in enumerate(result.runs):
            assert run.input == dataset_with_predictions[i]["input"]

    def test_run_result_token_usage_input_tokens_is_zero(
        self, pipeline_with_predictions
    ):
        """RunResult.token_usage.input_tokens is 0 for every run."""
        result = pipeline_with_predictions.run()
        for run in result.runs:
            assert run.token_usage.input_tokens == 0

    def test_run_result_token_usage_output_tokens_is_zero(
        self, pipeline_with_predictions
    ):
        """RunResult.token_usage.output_tokens is 0 for every run."""
        result = pipeline_with_predictions.run()
        for run in result.runs:
            assert run.token_usage.output_tokens == 0

    def test_run_result_token_usage_cost_usd_is_none(
        self, pipeline_with_predictions
    ):
        """RunResult.token_usage.cost_usd is None for every run."""
        result = pipeline_with_predictions.run()
        for run in result.runs:
            assert run.token_usage.cost_usd is None

    def test_run_result_token_usage_is_token_usage_instance(
        self, pipeline_with_predictions
    ):
        """RunResult.token_usage is a TokenUsage instance."""
        result = pipeline_with_predictions.run()
        for run in result.runs:
            assert isinstance(run.token_usage, TokenUsage)

    def test_run_result_evaluations_is_a_list(
        self, pipeline_with_predictions
    ):
        """RunResult.evaluations is a list."""
        result = pipeline_with_predictions.run()
        for run in result.runs:
            assert isinstance(run.evaluations, list)

    def test_all_runs_are_run_result_instances(
        self, pipeline_with_predictions
    ):
        """Every item in ExperimentResult.runs is a RunResult."""
        result = pipeline_with_predictions.run()
        for run in result.runs:
            assert isinstance(run, RunResult)


# ---------------------------------------------------------------------------
# 11. run() raises ValueError for missing 'prediction' key
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunMissingPrediction:
    """run() raises ValueError with record index when 'prediction' key is absent."""

    def _make_pipeline(
        self,
        dataset: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        from assayer.runner.historical_pipeline import HistoricalPipeline

        return HistoricalPipeline(
            dataset=dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

    def test_missing_prediction_raises_value_error(
        self, evaluator_registry, metric_registry
    ):
        """run() raises ValueError when the first record is missing 'prediction'."""
        dataset = [{"input": "x", "expected_output": "y"}]
        pipeline = self._make_pipeline(dataset, evaluator_registry, metric_registry)
        with pytest.raises(ValueError):
            pipeline.run()

    def test_missing_prediction_error_contains_index_zero(
        self, evaluator_registry, metric_registry
    ):
        """ValueError message contains the index 0 when first record is missing."""
        dataset = [{"input": "x", "expected_output": "y"}]
        pipeline = self._make_pipeline(dataset, evaluator_registry, metric_registry)
        with pytest.raises(ValueError, match="0"):
            pipeline.run()

    def test_missing_prediction_error_contains_index_one(
        self, evaluator_registry, metric_registry
    ):
        """ValueError message contains index 1 when second record is missing."""
        dataset = [
            {"input": "x", "expected_output": "y", "prediction": "p"},
            {"input": "x2", "expected_output": "y2"},  # missing prediction
        ]
        pipeline = self._make_pipeline(dataset, evaluator_registry, metric_registry)
        with pytest.raises(ValueError, match="1"):
            pipeline.run()

    def test_missing_prediction_error_message_format(
        self, evaluator_registry, metric_registry
    ):
        """ValueError message matches the exact format from the spec."""
        dataset = [{"input": "x", "expected_output": "y"}]
        pipeline = self._make_pipeline(dataset, evaluator_registry, metric_registry)
        with pytest.raises(ValueError, match="Record at index 0 is missing 'prediction'"):
            pipeline.run()

    def test_valid_records_before_missing_prediction_do_not_raise(
        self, evaluator_registry, metric_registry
    ):
        """Records processed before the bad one do not trigger the error."""
        dataset = [
            {"input": "x1", "expected_output": "y1", "prediction": "p1"},
            {"input": "x2", "expected_output": "y2", "prediction": "p2"},
            {"input": "x3", "expected_output": "y3"},  # index 2 is missing
        ]
        pipeline = self._make_pipeline(dataset, evaluator_registry, metric_registry)
        with pytest.raises(ValueError, match="2"):
            pipeline.run()


# ---------------------------------------------------------------------------
# 12. run() routes through FieldRouter (not calling external functions)
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunUsesFieldRouter:
    """run() delegates evaluation to _field_router.route(), not to any external fn."""

    def test_field_router_route_is_called_once_per_record(
        self,
        dataset_with_predictions: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """_field_router.route() is called exactly once for each dataset record."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=dataset_with_predictions,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

        mock_router = MagicMock()
        mock_router.route.return_value = []
        pipeline._field_router = mock_router

        pipeline.run()

        assert mock_router.route.call_count == len(dataset_with_predictions)

    def test_field_router_route_called_with_prediction_and_expected(
        self,
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """_field_router.route() receives prediction and expected_output as arguments."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        dataset = [{"input": "q", "expected_output": "ref_val", "prediction": "pred_val"}]

        pipeline = HistoricalPipeline(
            dataset=dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

        mock_router = MagicMock()
        mock_router.route.return_value = []
        pipeline._field_router = mock_router

        pipeline.run()

        mock_router.route.assert_called_once_with("pred_val", "ref_val")

    def test_run_result_evaluations_come_from_field_router(
        self,
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """RunResult.evaluations is whatever _field_router.route() returns."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        dataset = [{"input": "q", "expected_output": "ref_val", "prediction": "pred_val"}]

        pipeline = HistoricalPipeline(
            dataset=dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

        sentinel_evaluations = [MagicMock()]
        mock_router = MagicMock()
        mock_router.route.return_value = sentinel_evaluations
        pipeline._field_router = mock_router

        result = pipeline.run()

        assert result.runs[0].evaluations is sentinel_evaluations


# ---------------------------------------------------------------------------
# 13. run() loads dataset via load_dataset
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunLoadsDataset:
    """run() calls load_dataset() to resolve the dataset source."""

    def test_run_loads_dataset_from_string_path(
        self,
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
        tmp_path,
    ):
        """run() accepts a file path string and loads records from that file."""
        import json
        from assayer.runner.historical_pipeline import HistoricalPipeline

        records = [
            {"input": "a", "expected_output": "b", "prediction": "c"},
        ]
        dataset_file = tmp_path / "hist.json"
        dataset_file.write_text(json.dumps(records))

        pipeline = HistoricalPipeline(
            dataset=str(dataset_file),
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

        result = pipeline.run()
        assert len(result.runs) == 1
        assert result.runs[0].output == "c"

    def test_run_calls_load_dataset_with_self_dataset(
        self,
        dataset_with_predictions: list[dict],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
    ):
        """run() passes self.dataset to load_dataset()."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        pipeline = HistoricalPipeline(
            dataset=dataset_with_predictions,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["accuracy"],
            evaluator_registry=evaluator_registry,
            metric_registry=metric_registry,
        )

        with patch(
            "assayer.runner.historical_pipeline.load_dataset",
            return_value=dataset_with_predictions,
        ) as mock_load:
            pipeline.run()

        mock_load.assert_called_once_with(dataset_with_predictions)


# ---------------------------------------------------------------------------
# 14. run() aggregate metrics use metric_registry.get(name)
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunAggregateMetrics:
    """run() computes aggregate metrics via metric_registry.get(name)."""

    def test_metric_receives_all_predictions(
        self,
        evaluator_registry: EvaluatorRegistry,
    ):
        """The metric function is called with all predictions in dataset order."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        captured = {}

        def capture_metric(preds, refs):
            captured["preds"] = preds
            captured["refs"] = refs
            return 1.0

        reg = MetricRegistry()
        reg.register("cap_metric", capture_metric)

        dataset = [
            {"input": "i1", "expected_output": "e1", "prediction": "pred1"},
            {"input": "i2", "expected_output": "e2", "prediction": "pred2"},
        ]

        pipeline = HistoricalPipeline(
            dataset=dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["cap_metric"],
            evaluator_registry=evaluator_registry,
            metric_registry=reg,
        )

        pipeline.run()

        assert captured["preds"] == ["pred1", "pred2"]

    def test_metric_receives_all_references(
        self,
        evaluator_registry: EvaluatorRegistry,
    ):
        """The metric function is called with all expected_outputs in dataset order."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        captured = {}

        def capture_metric(preds, refs):
            captured["preds"] = preds
            captured["refs"] = refs
            return 1.0

        reg = MetricRegistry()
        reg.register("cap_metric", capture_metric)

        dataset = [
            {"input": "i1", "expected_output": "e1", "prediction": "pred1"},
            {"input": "i2", "expected_output": "e2", "prediction": "pred2"},
        ]

        pipeline = HistoricalPipeline(
            dataset=dataset,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["cap_metric"],
            evaluator_registry=evaluator_registry,
            metric_registry=reg,
        )

        pipeline.run()

        assert captured["refs"] == ["e1", "e2"]

    def test_multiple_metrics_all_computed(
        self,
        dataset_with_predictions: list[dict],
        evaluator_registry: EvaluatorRegistry,
    ):
        """When multiple metrics are specified, all appear in ExperimentResult.metrics."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        reg = MetricRegistry()
        reg.register("metric_a", lambda p, r: 0.1)
        reg.register("metric_b", lambda p, r: 0.2)

        pipeline = HistoricalPipeline(
            dataset=dataset_with_predictions,
            field_evaluators={"stub": ["stub_eval"]},
            metrics=["metric_a", "metric_b"],
            evaluator_registry=evaluator_registry,
            metric_registry=reg,
        )

        result = pipeline.run()

        assert "metric_a" in result.metrics
        assert "metric_b" in result.metrics
        assert result.metrics["metric_a"] == 0.1
        assert result.metrics["metric_b"] == 0.2


# ---------------------------------------------------------------------------
# 15. run() docstring and type hints
# ---------------------------------------------------------------------------

class TestHistoricalPipelineRunDocstringAndTypeHints:
    """run() must have a Google-style docstring and a proper return type annotation."""

    def test_run_has_docstring(self):
        """run() method has a non-empty docstring."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert HistoricalPipeline.run.__doc__ is not None
        assert len(HistoricalPipeline.run.__doc__.strip()) > 0

    def test_run_docstring_contains_returns_section(self):
        """run() docstring has a 'Returns:' section (Google style)."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert "Returns:" in HistoricalPipeline.run.__doc__

    def test_run_docstring_contains_raises_section(self):
        """run() docstring has a 'Raises:' section (Google style)."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        assert "Raises:" in HistoricalPipeline.run.__doc__

    def test_run_return_type_annotation_is_experiment_result(self):
        """run() return annotation is ExperimentResult."""
        from assayer.runner.historical_pipeline import HistoricalPipeline

        hints = get_type_hints(HistoricalPipeline.run)
        assert "return" in hints
        assert hints["return"] is ExperimentResult

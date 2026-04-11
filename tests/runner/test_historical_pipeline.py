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
"""

import inspect
from typing import Any, get_type_hints

import pytest

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation
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

    def test_run_raises_not_implemented_error(
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
        with pytest.raises(NotImplementedError):
            pipeline.run()


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

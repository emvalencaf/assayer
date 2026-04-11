"""Tests for ConsistencyPipeline constructor and fail-fast validation.

Covers:
- Class and module existence
- Constructor signature (has target_fn, no metrics)
- Instance attribute storage
- Default parameter values
- Fail-fast KeyError on unregistered evaluator names
- One ConsistencyEvaluator instantiated per field with correct k and min_k
- Google-style docstrings on class and __init__
- Full type hints on all parameters and return type
- Placeholder run() raises NotImplementedError
"""

import inspect
from typing import Any, get_type_hints

import pytest

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation
from assayer.registries.evaluator_registry import EvaluatorRegistry


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
    """Return a registry pre-populated with two evaluators."""
    reg = EvaluatorRegistry()
    reg.register("stub_eval", _StubEvaluator)
    reg.register("stub_eval_b", _StubEvaluator)
    return reg


@pytest.fixture()
def target_fn():
    """Return a simple callable target function."""
    def fn(input_: Any) -> str:
        return "result"
    return fn


@pytest.fixture()
def minimal_dataset() -> list[dict]:
    """Return a minimal one-row dataset."""
    return [{"input": "hello", "expected_output": "world"}]


@pytest.fixture()
def minimal_pipeline(target_fn, minimal_dataset, evaluator_registry):
    """Return a ConsistencyPipeline with minimal valid configuration."""
    from assayer.runner.consistency_pipeline import ConsistencyPipeline

    return ConsistencyPipeline(
        target_fn=target_fn,
        dataset=minimal_dataset,
        field_evaluators={"output": "stub_eval"},
        evaluator_registry=evaluator_registry,
    )


# ---------------------------------------------------------------------------
# 1. Import / existence
# ---------------------------------------------------------------------------

class TestConsistencyPipelineImport:
    """ConsistencyPipeline exists and is importable."""

    def test_class_importable(self):
        """ConsistencyPipeline can be imported from its module."""
        from assayer.runner.consistency_pipeline import ConsistencyPipeline  # noqa: F401

    def test_class_is_a_class(self):
        """ConsistencyPipeline is a proper class."""
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        assert inspect.isclass(ConsistencyPipeline)


# ---------------------------------------------------------------------------
# 2. Constructor signature
# ---------------------------------------------------------------------------

class TestConsistencyPipelineSignature:
    """Constructor has the expected parameters."""

    def _get_params(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        return list(inspect.signature(ConsistencyPipeline.__init__).parameters.keys())

    def test_has_target_fn_param(self):
        assert "target_fn" in self._get_params()

    def test_has_dataset_param(self):
        assert "dataset" in self._get_params()

    def test_has_field_evaluators_param(self):
        assert "field_evaluators" in self._get_params()

    def test_has_evaluator_registry_param(self):
        assert "evaluator_registry" in self._get_params()

    def test_has_k_param(self):
        assert "k" in self._get_params()

    def test_has_min_k_param(self):
        assert "min_k" in self._get_params()

    def test_has_experiment_name_param(self):
        assert "experiment_name" in self._get_params()

    def test_no_metrics_param(self):
        """metrics must NOT be present in the constructor."""
        assert "metrics" not in self._get_params()

    def test_k_default_is_5(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        sig = inspect.signature(ConsistencyPipeline.__init__)
        param = sig.parameters["k"]
        assert param.default != inspect.Parameter.empty
        assert param.default == 5

    def test_min_k_default_is_none(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        sig = inspect.signature(ConsistencyPipeline.__init__)
        param = sig.parameters["min_k"]
        assert param.default != inspect.Parameter.empty
        assert param.default is None

    def test_experiment_name_default_is_unnamed_experiment(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        sig = inspect.signature(ConsistencyPipeline.__init__)
        param = sig.parameters["experiment_name"]
        assert param.default != inspect.Parameter.empty
        assert param.default == "unnamed_experiment"

    def test_init_return_annotation_is_none(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        sig = inspect.signature(ConsistencyPipeline.__init__)
        assert sig.return_annotation is None


# ---------------------------------------------------------------------------
# 3. Instance attribute storage
# ---------------------------------------------------------------------------

class TestConsistencyPipelineAttributes:
    """Constructor stores all parameters as instance attributes."""

    def test_stores_target_fn(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        assert pipeline.target_fn is target_fn

    def test_stores_dataset_list(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        assert pipeline.dataset is minimal_dataset

    def test_stores_dataset_string(self, target_fn, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset="path/to/dataset.jsonl",
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        assert pipeline.dataset == "path/to/dataset.jsonl"

    def test_stores_field_evaluators(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        field_evaluators = {"output": "stub_eval"}
        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators=field_evaluators,
            evaluator_registry=evaluator_registry,
        )
        assert pipeline.field_evaluators == field_evaluators

    def test_stores_evaluator_registry(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        assert pipeline.evaluator_registry is evaluator_registry

    def test_stores_k(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
            k=10,
        )
        assert pipeline.k == 10

    def test_stores_min_k(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
            min_k=3,
        )
        assert pipeline.min_k == 3

    def test_stores_experiment_name(self, target_fn, minimal_dataset, evaluator_registry):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
            experiment_name="my_experiment",
        )
        assert pipeline.experiment_name == "my_experiment"

    def test_default_experiment_name(self, minimal_pipeline):
        assert minimal_pipeline.experiment_name == "unnamed_experiment"

    def test_default_k(self, minimal_pipeline):
        assert minimal_pipeline.k == 5

    def test_default_min_k(self, minimal_pipeline):
        assert minimal_pipeline.min_k is None


# ---------------------------------------------------------------------------
# 4. ConsistencyEvaluator instantiation per field
# ---------------------------------------------------------------------------

class TestConsistencyEvaluatorInstantiation:
    """One ConsistencyEvaluator is created per field_evaluators entry."""

    def test_single_field_creates_one_consistency_evaluator(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline
        from assayer.evaluators.consistency import ConsistencyEvaluator

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        assert "output" in pipeline._consistency_evaluators
        assert isinstance(pipeline._consistency_evaluators["output"], ConsistencyEvaluator)

    def test_two_fields_create_two_consistency_evaluators(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline
        from assayer.evaluators.consistency import ConsistencyEvaluator

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"field_a": "stub_eval", "field_b": "stub_eval_b"},
            evaluator_registry=evaluator_registry,
        )
        assert len(pipeline._consistency_evaluators) == 2
        assert isinstance(pipeline._consistency_evaluators["field_a"], ConsistencyEvaluator)
        assert isinstance(pipeline._consistency_evaluators["field_b"], ConsistencyEvaluator)

    def test_consistency_evaluator_receives_correct_k(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
            k=7,
        )
        evaluator = pipeline._consistency_evaluators["output"]
        assert evaluator._k == 7

    def test_consistency_evaluator_receives_correct_min_k(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
            min_k=3,
        )
        evaluator = pipeline._consistency_evaluators["output"]
        assert evaluator._min_k == 3

    def test_consistency_evaluator_min_k_none_by_default(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"output": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        evaluator = pipeline._consistency_evaluators["output"]
        assert evaluator._min_k is None

    def test_empty_field_evaluators_creates_no_evaluators(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={},
            evaluator_registry=evaluator_registry,
        )
        assert pipeline._consistency_evaluators == {}

    def test_base_evaluator_instantiated_with_field_name(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        """The wrapped base evaluator is instantiated with field_name keyword arg."""
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=minimal_dataset,
            field_evaluators={"my_field": "stub_eval"},
            evaluator_registry=evaluator_registry,
        )
        # The inner evaluator's name should be the evaluator_name used to register it
        inner_evaluator = pipeline._consistency_evaluators["my_field"]._evaluator
        assert inner_evaluator.name == "stub_eval"


# ---------------------------------------------------------------------------
# 5. Fail-fast validation (KeyError on unregistered evaluator)
# ---------------------------------------------------------------------------

class TestConsistencyPipelineFailFast:
    """Constructor raises KeyError for unregistered evaluator names."""

    def test_unregistered_evaluator_raises_key_error(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        with pytest.raises(KeyError):
            ConsistencyPipeline(
                target_fn=target_fn,
                dataset=minimal_dataset,
                field_evaluators={"output": "nonexistent_evaluator"},
                evaluator_registry=evaluator_registry,
            )

    def test_partially_unregistered_raises_key_error(
        self, target_fn, minimal_dataset, evaluator_registry
    ):
        """KeyError raised even if only one evaluator name is unregistered."""
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        with pytest.raises(KeyError):
            ConsistencyPipeline(
                target_fn=target_fn,
                dataset=minimal_dataset,
                field_evaluators={
                    "field_a": "stub_eval",
                    "field_b": "does_not_exist",
                },
                evaluator_registry=evaluator_registry,
            )

    def test_empty_registry_raises_key_error(self, target_fn, minimal_dataset):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        empty_registry = EvaluatorRegistry()

        with pytest.raises(KeyError):
            ConsistencyPipeline(
                target_fn=target_fn,
                dataset=minimal_dataset,
                field_evaluators={"output": "stub_eval"},
                evaluator_registry=empty_registry,
            )


# ---------------------------------------------------------------------------
# 6. Placeholder run() method
# ---------------------------------------------------------------------------

class TestConsistencyPipelineRunPlaceholder:
    """run() raises NotImplementedError."""

    def test_run_method_exists(self, minimal_pipeline):
        assert hasattr(minimal_pipeline, "run")
        assert callable(minimal_pipeline.run)

    def test_run_raises_not_implemented_error(self, minimal_pipeline):
        with pytest.raises(NotImplementedError):
            minimal_pipeline.run()


# ---------------------------------------------------------------------------
# 7. Google-style docstrings
# ---------------------------------------------------------------------------

class TestConsistencyPipelineDocstrings:
    """Class and __init__ have Google-style docstrings."""

    def test_class_has_docstring(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        assert ConsistencyPipeline.__doc__ is not None
        assert len(ConsistencyPipeline.__doc__.strip()) > 0

    def test_init_has_docstring(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        assert ConsistencyPipeline.__init__.__doc__ is not None
        assert len(ConsistencyPipeline.__init__.__doc__.strip()) > 0

    def test_class_docstring_has_args_section(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        # Google-style docstrings include an Args: section
        doc = ConsistencyPipeline.__doc__ or ""
        init_doc = ConsistencyPipeline.__init__.__doc__ or ""
        combined = doc + init_doc
        assert "Args:" in combined

    def test_class_docstring_has_raises_section(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        doc = ConsistencyPipeline.__doc__ or ""
        init_doc = ConsistencyPipeline.__init__.__doc__ or ""
        combined = doc + init_doc
        assert "Raises:" in combined


# ---------------------------------------------------------------------------
# 8. Type hints
# ---------------------------------------------------------------------------

class TestConsistencyPipelineTypeHints:
    """All parameters and return type have type hints."""

    def test_init_has_type_hints(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        hints = get_type_hints(ConsistencyPipeline.__init__)
        params = list(
            inspect.signature(ConsistencyPipeline.__init__).parameters.keys()
        )
        # Exclude 'self' from annotation check
        for param in params:
            if param == "self":
                continue
            assert param in hints, f"Parameter '{param}' is missing a type hint"

    def test_init_has_return_type_hint(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        hints = get_type_hints(ConsistencyPipeline.__init__)
        assert "return" in hints
        assert hints["return"] is type(None)

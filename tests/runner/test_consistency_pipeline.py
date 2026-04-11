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

    def test_run_is_callable(self, minimal_pipeline):
        assert callable(minimal_pipeline.run)


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


# ---------------------------------------------------------------------------
# TASK-002: Tests for ConsistencyPipeline.run()
# ---------------------------------------------------------------------------

import statistics
from unittest.mock import MagicMock, patch

from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation
from assayer.models.consistency_report import ConsistencyReport
from assayer.models.consistency_run_result import ConsistencyRunResult
from assayer.models.consistency_summary import ConsistencySummary


def _make_field_eval(
    agreement_rate: float = 1.0,
    entropy: float = 0.0,
    score_std: float = 0.0,
    correct_rate: float = 1.0,
    pass_at_k: bool = True,
    recall_at_k: float = 1.0,
) -> ConsistencyFieldEvaluation:
    """Build a ConsistencyFieldEvaluation with controllable metric values."""
    return ConsistencyFieldEvaluation(
        group_key=None,
        n=5,
        agreement_rate=agreement_rate,
        dominant_label=None,
        entropy=entropy,
        score_std=score_std,
        correct_rate=correct_rate,
        pass_at_k=pass_at_k,
        recall_at_k=recall_at_k,
        raw_results=[],
    )


@pytest.fixture()
def run_pipeline(evaluator_registry, target_fn):
    """Factory fixture: returns a helper that builds and runs ConsistencyPipeline.

    The helper patches load_dataset and mock-injects evaluate_live results so
    that production code is not called.
    """
    def _build_and_run(
        dataset: list[dict],
        field_evaluators_map: dict[str, str],
        field_eval_results: dict[str, list[ConsistencyFieldEvaluation]],
        k: int = 5,
        experiment_name: str = "test_experiment",
    ):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        pipeline = ConsistencyPipeline(
            target_fn=target_fn,
            dataset=dataset,
            field_evaluators=field_evaluators_map,
            evaluator_registry=evaluator_registry,
            k=k,
            experiment_name=experiment_name,
        )

        # Patch each consistency evaluator's evaluate_live with a side_effect
        # that pops results from the per-field list in order.
        call_counters: dict[str, int] = {field: 0 for field in field_eval_results}
        for field_name, ce in pipeline._consistency_evaluators.items():
            results_for_field = field_eval_results[field_name]
            counter = {"n": 0}

            def _side_effect(_target_fn, _input, _reference, _results=results_for_field, _c=counter):
                idx = _c["n"]
                _c["n"] += 1
                return _results[idx]

            ce.evaluate_live = MagicMock(side_effect=_side_effect)

        # Patch load_dataset wherever it will be imported inside the pipeline module.
        # We patch both the source module and the pipeline module (in case the
        # implementation imports it either way). Using create=True so the patch
        # works even before the implementation adds the import.
        with patch(
            "assayer.runner.dataset_loader.load_dataset",
            side_effect=lambda src: src,
        ), patch(
            "assayer.runner.consistency_pipeline.load_dataset",
            side_effect=lambda src: src,
            create=True,
        ):
            report = pipeline.run()

        return report, pipeline

    return _build_and_run


class TestRunReturnsConsistencyReport:
    """run() returns a ConsistencyReport with correct top-level fields."""

    def test_returns_consistency_report_instance(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_result = _make_field_eval()
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_result]},
        )
        assert isinstance(report, ConsistencyReport)

    def test_report_experiment_name_matches(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_result = _make_field_eval()
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_result]},
            experiment_name="my_exp",
        )
        assert report.experiment_name == "my_exp"

    def test_report_k_matches_pipeline_k(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_result = _make_field_eval()
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_result]},
            k=7,
        )
        assert report.k == 7

    def test_report_per_field_keys_match_field_evaluators(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"field_a": "stub_eval", "field_b": "stub_eval_b"},
            field_eval_results={
                "field_a": [_make_field_eval()],
                "field_b": [_make_field_eval()],
            },
        )
        assert set(report.per_field.keys()) == {"field_a", "field_b"}

    def test_report_runs_field_is_a_list(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_result = _make_field_eval()
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_result]},
        )
        assert isinstance(report.runs, list)


class TestRunCallsEvaluateLive:
    """run() calls evaluate_live once per field per input."""

    def test_evaluate_live_called_once_for_single_record_single_field(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_result = _make_field_eval()
        _, pipeline = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_result]},
        )
        pipeline._consistency_evaluators["output"].evaluate_live.assert_called_once()

    def test_evaluate_live_called_with_correct_args(self, run_pipeline, target_fn):
        dataset = [{"input": "hello", "expected_output": "world"}]
        eval_result = _make_field_eval()
        _, pipeline = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_result]},
        )
        pipeline._consistency_evaluators["output"].evaluate_live.assert_called_once_with(
            target_fn, "hello", "world"
        )

    def test_evaluate_live_called_per_record(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
            {"input": "q3", "expected_output": "a3"},
        ]
        _, pipeline = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [_make_field_eval() for _ in range(3)]},
        )
        assert pipeline._consistency_evaluators["output"].evaluate_live.call_count == 3

    def test_evaluate_live_called_for_each_field(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        _, pipeline = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"field_a": "stub_eval", "field_b": "stub_eval_b"},
            field_eval_results={
                "field_a": [_make_field_eval()],
                "field_b": [_make_field_eval()],
            },
        )
        pipeline._consistency_evaluators["field_a"].evaluate_live.assert_called_once()
        pipeline._consistency_evaluators["field_b"].evaluate_live.assert_called_once()

    def test_evaluate_live_called_n_records_x_n_fields(self, run_pipeline):
        """With 2 records and 2 fields, evaluate_live is called 2 times per field."""
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        _, pipeline = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"field_a": "stub_eval", "field_b": "stub_eval_b"},
            field_eval_results={
                "field_a": [_make_field_eval(), _make_field_eval()],
                "field_b": [_make_field_eval(), _make_field_eval()],
            },
        )
        assert pipeline._consistency_evaluators["field_a"].evaluate_live.call_count == 2
        assert pipeline._consistency_evaluators["field_b"].evaluate_live.call_count == 2


class TestRunPerFieldSummary:
    """per_field[field] is a ConsistencySummary with correct aggregated values."""

    def test_per_field_value_is_consistency_summary(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [_make_field_eval()]},
        )
        assert isinstance(report.per_field["output"], ConsistencySummary)

    def test_mean_agreement_rate_is_average_of_evals(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(agreement_rate=0.4), _make_field_eval(agreement_rate=0.8)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        expected = statistics.mean(e.agreement_rate for e in evals)
        assert report.per_field["output"].mean_agreement_rate == pytest.approx(expected)

    def test_mean_entropy_is_average_of_evals(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(entropy=0.2), _make_field_eval(entropy=0.6)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        expected = statistics.mean(e.entropy for e in evals)
        assert report.per_field["output"].mean_entropy == pytest.approx(expected)

    def test_mean_score_std_is_average_of_evals(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(score_std=0.1), _make_field_eval(score_std=0.3)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        expected = statistics.mean(e.score_std for e in evals)
        assert report.per_field["output"].mean_score_std == pytest.approx(expected)

    def test_mean_correct_rate_is_average_of_evals(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(correct_rate=0.2), _make_field_eval(correct_rate=0.8)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        expected = statistics.mean(e.correct_rate for e in evals)
        assert report.per_field["output"].mean_correct_rate == pytest.approx(expected)

    def test_mean_recall_at_k_is_average_of_evals(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(recall_at_k=0.3), _make_field_eval(recall_at_k=0.7)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        expected = statistics.mean(e.recall_at_k for e in evals)
        assert report.per_field["output"].mean_recall_at_k == pytest.approx(expected)

    def test_pass_at_k_rate_is_proportion_of_passing_evals(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
            {"input": "q3", "expected_output": "a3"},
            {"input": "q4", "expected_output": "a4"},
        ]
        evals = [
            _make_field_eval(pass_at_k=True),
            _make_field_eval(pass_at_k=False),
            _make_field_eval(pass_at_k=True),
            _make_field_eval(pass_at_k=False),
        ]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        assert report.per_field["output"].pass_at_k_rate == pytest.approx(0.5)

    def test_pass_at_k_rate_all_passing(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(pass_at_k=True), _make_field_eval(pass_at_k=True)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        assert report.per_field["output"].pass_at_k_rate == pytest.approx(1.0)

    def test_pass_at_k_rate_none_passing(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
        ]
        evals = [_make_field_eval(pass_at_k=False), _make_field_eval(pass_at_k=False)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        assert report.per_field["output"].pass_at_k_rate == pytest.approx(0.0)


class TestRunWorstGroups:
    """worst_groups contains up to 10 entries sorted by ascending agreement_rate."""

    def test_worst_groups_sorted_ascending_by_agreement_rate(self, run_pipeline):
        n = 5
        dataset = [{"input": f"q{i}", "expected_output": f"a{i}"} for i in range(n)]
        rates = [0.9, 0.2, 0.5, 0.1, 0.7]
        evals = [_make_field_eval(agreement_rate=r) for r in rates]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        wg = report.per_field["output"].worst_groups
        rates_in_wg = [e.agreement_rate for e in wg]
        assert rates_in_wg == sorted(rates_in_wg)

    def test_worst_groups_capped_at_10(self, run_pipeline):
        n = 15
        dataset = [{"input": f"q{i}", "expected_output": f"a{i}"} for i in range(n)]
        evals = [_make_field_eval(agreement_rate=i / n) for i in range(n)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        assert len(report.per_field["output"].worst_groups) == 10

    def test_worst_groups_fewer_than_10_if_dataset_small(self, run_pipeline):
        n = 3
        dataset = [{"input": f"q{i}", "expected_output": f"a{i}"} for i in range(n)]
        evals = [_make_field_eval(agreement_rate=0.5) for _ in range(n)]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        assert len(report.per_field["output"].worst_groups) == n

    def test_worst_groups_contains_lowest_agreement_rates(self, run_pipeline):
        """With 15 items, worst_groups should hold the 10 lowest agreement rates."""
        n = 15
        dataset = [{"input": f"q{i}", "expected_output": f"a{i}"} for i in range(n)]
        rates = [i / n for i in range(n)]  # 0.0, 0.067, ..., 0.933
        evals = [_make_field_eval(agreement_rate=r) for r in rates]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": evals},
        )
        wg_rates = sorted(e.agreement_rate for e in report.per_field["output"].worst_groups)
        expected_worst = sorted(rates)[:10]
        assert wg_rates == pytest.approx(expected_worst)


class TestRunRunsList:
    """runs contains one ConsistencyRunResult per dataset input."""

    def test_runs_has_one_entry_per_record(self, run_pipeline):
        dataset = [
            {"input": "q1", "expected_output": "a1"},
            {"input": "q2", "expected_output": "a2"},
            {"input": "q3", "expected_output": "a3"},
        ]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [_make_field_eval() for _ in range(3)]},
        )
        assert len(report.runs) == 3

    def test_runs_entries_are_consistency_run_result(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [_make_field_eval()]},
        )
        assert isinstance(report.runs[0], ConsistencyRunResult)

    def test_run_result_input_matches_record_input(self, run_pipeline):
        dataset = [
            {"input": "hello", "expected_output": "world"},
            {"input": "foo", "expected_output": "bar"},
        ]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [_make_field_eval(), _make_field_eval()]},
        )
        assert report.runs[0].input == "hello"
        assert report.runs[1].input == "foo"

    def test_run_result_per_field_evaluations_has_correct_field(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [_make_field_eval()]},
        )
        assert "output" in report.runs[0].per_field_evaluations

    def test_run_result_per_field_evaluations_is_consistency_field_evaluation(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_obj = _make_field_eval(agreement_rate=0.6)
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_obj]},
        )
        assert isinstance(
            report.runs[0].per_field_evaluations["output"],
            ConsistencyFieldEvaluation,
        )

    def test_run_result_per_field_evaluations_contains_correct_eval_object(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        eval_obj = _make_field_eval(agreement_rate=0.42)
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": [eval_obj]},
        )
        assert report.runs[0].per_field_evaluations["output"] is eval_obj

    def test_run_result_has_all_fields_when_multiple_fields(self, run_pipeline):
        dataset = [{"input": "q1", "expected_output": "a1"}]
        report, _ = run_pipeline(
            dataset=dataset,
            field_evaluators_map={"field_a": "stub_eval", "field_b": "stub_eval_b"},
            field_eval_results={
                "field_a": [_make_field_eval()],
                "field_b": [_make_field_eval()],
            },
        )
        assert "field_a" in report.runs[0].per_field_evaluations
        assert "field_b" in report.runs[0].per_field_evaluations


class TestRunEmptyDataset:
    """Empty dataset produces ConsistencyReport with empty runs and empty per_field."""

    def test_empty_dataset_returns_consistency_report(self, run_pipeline):
        report, _ = run_pipeline(
            dataset=[],
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": []},
        )
        assert isinstance(report, ConsistencyReport)

    def test_empty_dataset_runs_is_empty(self, run_pipeline):
        report, _ = run_pipeline(
            dataset=[],
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": []},
        )
        assert report.runs == []

    def test_empty_dataset_per_field_has_no_entries_with_data(self, run_pipeline):
        """With an empty dataset, per_field summaries should have zero-valued metrics."""
        report, _ = run_pipeline(
            dataset=[],
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": []},
        )
        # per_field should still have the key, but with zero-valued summary
        if "output" in report.per_field:
            summary = report.per_field["output"]
            assert summary.mean_agreement_rate == 0.0
            assert summary.mean_entropy == 0.0
            assert summary.mean_score_std == 0.0
            assert summary.mean_correct_rate == 0.0
            assert summary.pass_at_k_rate == 0.0
            assert summary.mean_recall_at_k == 0.0
            assert summary.per_group == []
            assert summary.worst_groups == []
        else:
            # Alternatively, per_field may simply be empty
            assert report.per_field == {}

    def test_empty_dataset_evaluate_live_never_called(self, run_pipeline):
        _, pipeline = run_pipeline(
            dataset=[],
            field_evaluators_map={"output": "stub_eval"},
            field_eval_results={"output": []},
        )
        pipeline._consistency_evaluators["output"].evaluate_live.assert_not_called()


class TestRunDocstringAndTypeHints:
    """run() has a Google-style docstring and a return type hint."""

    def test_run_has_docstring(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        assert ConsistencyPipeline.run.__doc__ is not None
        assert len(ConsistencyPipeline.run.__doc__.strip()) > 0

    def test_run_docstring_has_returns_section(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        doc = ConsistencyPipeline.run.__doc__ or ""
        assert "Returns:" in doc

    def test_run_has_return_type_hint(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        hints = get_type_hints(ConsistencyPipeline.run)
        assert "return" in hints

    def test_run_return_type_hint_is_consistency_report(self):
        from assayer.runner.consistency_pipeline import ConsistencyPipeline

        hints = get_type_hints(ConsistencyPipeline.run)
        assert hints["return"] is ConsistencyReport

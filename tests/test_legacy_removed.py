"""The legacy API is gone: a clean break, with no alias left behind."""

import importlib

import pytest

REMOVED_MODULES = [
    "assayer.evaluators",
    "assayer.runner.pipeline",
    "assayer.runner.historical_pipeline",
    "assayer.runner.consistency_pipeline",
    "assayer.runner.field_router",
    "assayer.runner.dataset_loader",
    "assayer.runner.token_extractor",
    "assayer.runner.pricing",
    "assayer.registries.metric_registry",
    "assayer.registries.evaluator_registry",
    "assayer.models.experiment_result",
    "assayer.models.run_result",
    "assayer.models.field_evaluation",
    "assayer.integrations.langsmith",
]

REMOVED_NAMES = [
    ("assayer.runner", "EvaluationPipeline"),
    ("assayer.runner", "HistoricalPipeline"),
    ("assayer.runner", "ConsistencyPipeline"),
    ("assayer.runner", "FieldRouter"),
    ("assayer.runner", "compare_experiments"),
    ("assayer.models", "ExperimentResult"),
    ("assayer.models", "RunResult"),
    ("assayer.models", "FieldEvaluation"),
    ("assayer.models", "ConsistencyReport"),
    ("assayer.registries", "MetricRegistry"),
    ("assayer.registries", "EvaluatorRegistry"),
    ("assayer.registries", "default_metric_registry"),
    ("assayer.integrations", "LangSmithPublisher"),
    ("assayer.metrics", "register_chat_metrics"),
    ("assayer.metrics", "register_classification_metrics"),
    ("assayer.metrics", "register_ner_metrics"),
    ("assayer.metrics", "register_ner_evaluators"),
]


@pytest.mark.parametrize("module", REMOVED_MODULES)
def test_removed_module_does_not_import(module):
    with pytest.raises(ImportError):
        importlib.import_module(module)


@pytest.mark.parametrize(("module", "name"), REMOVED_NAMES)
def test_removed_name_is_not_exported(module, name):
    assert not hasattr(importlib.import_module(module), name)

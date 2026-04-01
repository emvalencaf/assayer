"""Tests for register_chat_metrics function.

Tests for the register_chat_metrics function that registers all four built-in
chat metrics (bleu, rouge_l, bert_score, semantic_similarity) in a MetricRegistry.
"""

import pytest
from typing import Callable

from assayer.registries.metric_registry import MetricRegistry
from assayer.metrics.chat import bleu, rouge_l, bert_score, make_semantic_similarity


def test_register_chat_metrics_imports_successfully():
    """Test that register_chat_metrics can be imported from metrics module."""
    # This will fail initially as register_chat_metrics doesn't exist yet
    from assayer.metrics import register_chat_metrics

    # Function should be callable
    assert callable(register_chat_metrics)


def test_register_chat_metrics_has_correct_signature():
    """Test that register_chat_metrics has the expected signature."""
    from assayer.metrics import register_chat_metrics
    import inspect

    # Get function signature
    sig = inspect.signature(register_chat_metrics)
    params = list(sig.parameters.keys())

    # Should have exactly one parameter named 'registry'
    assert len(params) == 1
    assert params[0] == "registry"

    # Return type should be None
    assert sig.return_annotation == None or str(sig.return_annotation) == "None"

    # Parameter should have MetricRegistry type hint
    registry_param = sig.parameters["registry"]
    assert str(registry_param.annotation) == "MetricRegistry" or "MetricRegistry" in str(registry_param.annotation)


def test_register_chat_metrics_has_google_style_docstring():
    """Test that register_chat_metrics has a Google-style docstring."""
    from assayer.metrics import register_chat_metrics

    # Should have a docstring
    assert register_chat_metrics.__doc__ is not None
    docstring = register_chat_metrics.__doc__.strip()

    # Google-style docstrings typically have Args: and Returns: sections
    assert "Args:" in docstring
    assert "registry" in docstring  # Should document the registry parameter

    # Should have a description
    assert len(docstring.split('\n')[0]) > 10  # First line should be substantial description


def test_register_chat_metrics_registers_all_four_metrics():
    """Test that register_chat_metrics registers exactly the four expected metrics."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()

    # Call register_chat_metrics
    register_chat_metrics(registry)

    # Should register exactly these four metrics
    expected_metrics = {"bleu", "rouge_l", "bert_score", "semantic_similarity"}
    registered_metrics = set(registry.list_metrics())

    assert registered_metrics == expected_metrics


def test_register_chat_metrics_resolves_to_correct_callables():
    """Test that each registered metric resolves to the correct callable."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()
    register_chat_metrics(registry)

    # Test bleu metric
    bleu_fn = registry.get("bleu")
    assert callable(bleu_fn)
    assert bleu_fn is bleu  # Should be the same function object

    # Test rouge_l metric
    rouge_l_fn = registry.get("rouge_l")
    assert callable(rouge_l_fn)
    assert rouge_l_fn is rouge_l  # Should be the same function object

    # Test bert_score metric
    bert_score_fn = registry.get("bert_score")
    assert callable(bert_score_fn)
    assert bert_score_fn is bert_score  # Should be the same function object

    # Test semantic_similarity metric (should be the result of make_semantic_similarity())
    semantic_sim_fn = registry.get("semantic_similarity")
    assert callable(semantic_sim_fn)
    # Should NOT be the factory function itself, but the returned metric function
    assert semantic_sim_fn is not make_semantic_similarity
    # Should be a function that takes two list arguments
    import inspect
    sig = inspect.signature(semantic_sim_fn)
    assert len(sig.parameters) == 2


def test_registered_metrics_are_functional():
    """Test that all registered metrics can be called and return floats."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()
    register_chat_metrics(registry)

    # Test data
    predictions = ["hello world", "this is a test"]
    references = ["hello world", "this is a test"]

    # Each metric should be callable and return a float
    for metric_name in ["bleu", "rouge_l", "bert_score", "semantic_similarity"]:
        metric_fn = registry.get(metric_name)
        result = metric_fn(predictions, references)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0


def test_semantic_similarity_uses_default_model():
    """Test that the registered semantic_similarity uses the default model."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()
    register_chat_metrics(registry)

    semantic_sim_fn = registry.get("semantic_similarity")

    # Create a fresh instance with default model to compare
    default_model_fn = make_semantic_similarity()

    # Both should behave identically (though we can't easily test the model name directly)
    test_preds = ["hello"]
    test_refs = ["hello"]

    # Both should produce the same result (perfect match should be close to 1.0)
    result1 = semantic_sim_fn(test_preds, test_refs)
    result2 = default_model_fn(test_preds, test_refs)

    # Results should be identical since both use the same default model
    assert abs(result1 - result2) < 0.001


def test_register_chat_metrics_twice_raises_keyerror():
    """Test that calling register_chat_metrics twice on the same registry raises KeyError."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()

    # First call should succeed
    register_chat_metrics(registry)

    # Second call should raise KeyError due to duplicate registration
    with pytest.raises(KeyError, match="already registered"):
        register_chat_metrics(registry)


def test_register_chat_metrics_preserves_existing_metrics():
    """Test that register_chat_metrics doesn't interfere with existing metrics in the registry."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()

    # Register a custom metric first
    def custom_metric(predictions, references):
        return 0.5

    registry.register("custom", custom_metric)

    # Register chat metrics
    register_chat_metrics(registry)

    # Should have all five metrics now
    all_metrics = set(registry.list_metrics())
    expected_metrics = {"custom", "bleu", "rouge_l", "bert_score", "semantic_similarity"}
    assert all_metrics == expected_metrics

    # Custom metric should still be accessible and functional
    custom_fn = registry.get("custom")
    assert custom_fn is custom_metric
    assert custom_fn([], []) == 0.5


def test_register_chat_metrics_with_empty_registry():
    """Test register_chat_metrics with a fresh empty registry."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()

    # Registry should start empty
    assert registry.list_metrics() == []

    # Register chat metrics
    register_chat_metrics(registry)

    # Should now have exactly four metrics
    metrics = registry.list_metrics()
    assert len(metrics) == 4
    assert set(metrics) == {"bert_score", "bleu", "rouge_l", "semantic_similarity"}


def test_register_chat_metrics_type_hints():
    """Test that register_chat_metrics has proper type hints."""
    from assayer.metrics import register_chat_metrics
    import inspect

    # Get type hints
    hints = inspect.signature(register_chat_metrics).parameters

    # registry parameter should have MetricRegistry type hint
    registry_param = hints["registry"]
    annotation_str = str(registry_param.annotation)
    assert "MetricRegistry" in annotation_str

    # Return annotation should be None
    return_annotation = inspect.signature(register_chat_metrics).return_annotation
    assert return_annotation == None or str(return_annotation) == "None"


def test_registered_metrics_handle_edge_cases():
    """Test that all registered metrics handle edge cases properly."""
    from assayer.metrics import register_chat_metrics

    registry = MetricRegistry()
    register_chat_metrics(registry)

    # Test with empty lists (should return 0.0)
    for metric_name in ["bleu", "rouge_l", "bert_score", "semantic_similarity"]:
        metric_fn = registry.get(metric_name)

        # Empty predictions and references
        result = metric_fn([], [])
        assert result == 0.0

        # Empty predictions only
        result = metric_fn([], ["reference"])
        assert result == 0.0

        # Empty references only
        result = metric_fn(["prediction"], [])
        assert result == 0.0
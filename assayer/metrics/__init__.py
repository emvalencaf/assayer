"""Metric implementations for evaluating model outputs."""

from assayer.registries.metric_registry import MetricRegistry
from assayer.metrics.chat import bleu, rouge_l, bert_score, make_semantic_similarity


def register_chat_metrics(registry: MetricRegistry) -> None:
    """Register all built-in chat metrics in the provided MetricRegistry.

    Registers the four core chat quality metrics: BLEU, ROUGE-L, BERTScore,
    and semantic similarity (using default model) for evaluating conversational
    model outputs against reference responses.

    Args:
        registry: The MetricRegistry instance to register metrics into.

    Returns:
        None

    Raises:
        KeyError: If any metric name is already registered in the registry.
    """
    # Register the individual metric functions
    registry.register("bleu", bleu)
    registry.register("rouge_l", rouge_l)
    registry.register("bert_score", bert_score)

    # Register semantic similarity using the default model
    semantic_similarity_fn = make_semantic_similarity()
    registry.register("semantic_similarity", semantic_similarity_fn)
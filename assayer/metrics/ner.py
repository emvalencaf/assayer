"""NER metrics for evaluating named entity recognition predictions."""

from assayer.evaluators.ner import EntitySpan, NEREvaluator, NERMatcher
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry


def ner_macro_f1(
    predictions: list[list[EntitySpan]],
    references: list[list[EntitySpan]],
) -> float:
    """Compute mean macro F1 across all examples.

    Calculates the macro F1 score for each example pair using NERMatcher,
    then returns the mean of all macro F1 scores. Uses exact matching semantics
    where EntitySpan objects must have identical text, entity_type, start, and end.

    Args:
        predictions: List of predicted entity span lists, one per example.
        references: List of reference entity span lists, one per example.

    Returns:
        float: Mean macro F1 score across all examples (0.0-1.0).
               Returns 0.0 for empty input lists.

    Example:
        >>> pred_spans = [[EntitySpan("John", "PERSON", 0, 4)]]
        >>> ref_spans = [[EntitySpan("John", "PERSON", 0, 4)]]
        >>> ner_macro_f1(pred_spans, ref_spans)
        1.0
        >>> ner_macro_f1([], [])
        0.0
    """
    # Handle empty input lists
    if not predictions or not references:
        return 0.0

    # Calculate macro F1 for each example pair
    matcher = NERMatcher()
    scores = [
        matcher.match(pred, ref).macro_f1
        for pred, ref in zip(predictions, references, strict=False)
    ]

    # Return mean of all macro F1 scores
    return sum(scores) / len(scores) if scores else 0.0


def register_ner_metrics(registry: MetricRegistry) -> None:
    """Register NER metrics in the provided MetricRegistry.

    Registers the ner_macro_f1 metric function in the provided registry
    under the name "ner_macro_f1".

    Args:
        registry: The MetricRegistry instance to register metrics in.

    Raises:
        KeyError: If the metric name "ner_macro_f1" is already registered.

    Example:
        >>> from assayer.registries.metric_registry import MetricRegistry
        >>> registry = MetricRegistry()
        >>> register_ner_metrics(registry)
        >>> metric_fn = registry.get("ner_macro_f1")
    """
    registry.register("ner_macro_f1", ner_macro_f1)


def register_ner_evaluators(registry: EvaluatorRegistry) -> None:
    """Register NER evaluators in the provided EvaluatorRegistry.

    Registers the NEREvaluator class in the provided registry under the
    name "ner".

    Args:
        registry: The EvaluatorRegistry instance to register evaluators in.

    Raises:
        KeyError: If the evaluator name "ner" is already registered.

    Example:
        >>> from assayer.registries.evaluator_registry import EvaluatorRegistry
        >>> registry = EvaluatorRegistry()
        >>> register_ner_evaluators(registry)
        >>> evaluator_cls = registry.get("ner")
    """
    registry.register("ner", NEREvaluator)

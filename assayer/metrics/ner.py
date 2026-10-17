"""NER metrics for evaluating named entity recognition predictions."""

from assayer.metrics.ner_matching import EntitySpan, NERMatcher


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

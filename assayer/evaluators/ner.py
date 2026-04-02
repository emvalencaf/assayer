"""Named Entity Recognition (NER) evaluator components."""

from dataclasses import dataclass
from typing import List, Dict, Any

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation


@dataclass(frozen=True)
class EntitySpan:
    """Represents a named entity span with position information.

    A frozen dataclass representing an identified entity in text with its type,
    content, and character-level position boundaries. The frozen attribute makes
    instances hashable and immutable, enabling set operations for TP/FP/FN counting.

    Args:
        text: The textual content of the entity span. Must not be empty or whitespace-only.
        entity_type: The type/category of the entity (e.g., "PERSON", "ORG"). Must not be empty or whitespace-only.
        start: Character offset where the entity begins (inclusive, 0-indexed). Must be >= 0.
        end: Character offset where the entity ends (exclusive). Must be > start.

    Raises:
        ValueError: If text is empty/whitespace-only, entity_type is empty/whitespace-only,
                   start is negative, or end <= start.

    Example:
        >>> span = EntitySpan(text="John Doe", entity_type="PERSON", start=0, end=8)
        >>> span.text
        'John Doe'
        >>> span.entity_type
        'PERSON'
    """
    text: str
    entity_type: str
    start: int   # character offset, inclusive, 0-indexed
    end: int     # character offset, exclusive

    def __post_init__(self) -> None:
        """Validate the EntitySpan fields after initialization.

        Raises:
            ValueError: If any validation rule is violated.
        """
        if not self.text or not self.text.strip():
            raise ValueError("EntitySpan.text must not be empty")
        if not self.entity_type or not self.entity_type.strip():
            raise ValueError("EntitySpan.entity_type must not be empty")
        if self.start < 0:
            raise ValueError("EntitySpan.start must be >= 0")
        if self.end <= self.start:
            raise ValueError("EntitySpan.end must be > start")


@dataclass
class NERMatchResult:
    """Result of comparing predicted vs reference entity spans.

    Contains per-type precision, recall, F1-score metrics and overall macro F1.
    Used by NERMatcher to return detailed evaluation results for named entity
    recognition systems.

    Args:
        per_type_precision: Precision score for each entity type (0.0-1.0).
        per_type_recall: Recall score for each entity type (0.0-1.0).
        per_type_f1: F1-score for each entity type (0.0-1.0).
        macro_f1: Unweighted average of per-type F1 scores (0.0-1.0).

    Example:
        >>> result = NERMatchResult(
        ...     per_type_precision={"PERSON": 0.9, "ORG": 0.8},
        ...     per_type_recall={"PERSON": 0.85, "ORG": 0.75},
        ...     per_type_f1={"PERSON": 0.875, "ORG": 0.775},
        ...     macro_f1=0.825
        ... )
        >>> result.macro_f1
        0.825
    """
    per_type_precision: Dict[str, float]
    per_type_recall: Dict[str, float]
    per_type_f1: Dict[str, float]
    macro_f1: float


class NERMatcher:
    """Matcher for evaluating named entity recognition results.

    Compares predicted entity spans against reference spans using exact matching.
    Two EntitySpan objects match if all fields (text, entity_type, start, end) are identical.
    Provides per-type precision, recall, and F1 metrics plus macro-averaged F1.

    Example:
        >>> matcher = NERMatcher()
        >>> predicted = [EntitySpan("Apple", "ORG", 0, 5)]
        >>> reference = [EntitySpan("Apple", "ORG", 0, 5)]
        >>> result = matcher.match(predicted, reference)
        >>> result.macro_f1
        1.0
    """

    def match(
        self,
        predicted: List[EntitySpan],
        reference: List[EntitySpan],
    ) -> NERMatchResult:
        """Compare predicted spans against reference spans.

        Uses exact matching: spans must have identical text, entity_type, start, and end.
        Computes precision, recall, and F1 per entity type, then macro F1 across types.

        Args:
            predicted: List of predicted entity spans.
            reference: List of reference (ground truth) entity spans.

        Returns:
            NERMatchResult containing per-type metrics and macro F1.

        Example:
            >>> matcher = NERMatcher()
            >>> predicted = [EntitySpan("John", "PERSON", 0, 4)]
            >>> reference = [EntitySpan("John", "PERSON", 0, 4)]
            >>> result = matcher.match(predicted, reference)
            >>> result.per_type_f1["PERSON"]
            1.0
        """
        # Collect all entity types from both lists
        types = {s.entity_type for s in predicted + reference}

        per_type_precision = {}
        per_type_recall = {}
        per_type_f1 = {}

        # Handle empty case
        if not types:
            return NERMatchResult(
                per_type_precision={},
                per_type_recall={},
                per_type_f1={},
                macro_f1=0.0
            )

        # For each type, calculate precision, recall, and F1
        for entity_type in types:
            # Get sets of spans for this type
            pred_set = {s for s in predicted if s.entity_type == entity_type}
            ref_set = {s for s in reference if s.entity_type == entity_type}

            # Calculate true positives (intersection of sets)
            tp = len(pred_set & ref_set)

            # Calculate precision
            precision = tp / len(pred_set) if pred_set else 0.0

            # Calculate recall
            recall = tp / len(ref_set) if ref_set else 0.0

            # Calculate F1
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            per_type_precision[entity_type] = precision
            per_type_recall[entity_type] = recall
            per_type_f1[entity_type] = f1

        # Calculate macro F1 (unweighted mean of per-type F1 values)
        macro_f1 = sum(per_type_f1.values()) / len(per_type_f1) if per_type_f1 else 0.0

        return NERMatchResult(
            per_type_precision=per_type_precision,
            per_type_recall=per_type_recall,
            per_type_f1=per_type_f1,
            macro_f1=macro_f1
        )


class NEREvaluator(BaseEvaluator):
    """Evaluator for Named Entity Recognition (NER) tasks.

    Evaluates predicted entity spans against reference spans using exact matching.
    Two EntitySpan objects match if all fields (text, entity_type, start, end) are
    identical. Provides per-type precision, recall, and F1 metrics plus macro-averaged F1.

    Args:
        field_name: Name of the field being evaluated (e.g., "entities", "extracted_entities").

    Example:
        >>> evaluator = NEREvaluator(field_name="entities")
        >>> predicted = [EntitySpan("John", "PERSON", 0, 4)]
        >>> reference = [EntitySpan("John", "PERSON", 0, 4)]
        >>> result = evaluator.evaluate(predicted, reference)
        >>> result.score
        1.0
    """

    def __init__(self, field_name: str) -> None:
        """Initialize the NER evaluator with a field name.

        Args:
            field_name: Name of the field being evaluated. Must be non-empty.

        Raises:
            ValueError: If field_name is empty or whitespace-only after stripping.
        """
        # BaseEvaluator requires a name parameter - using "ner" as the evaluator name
        super().__init__(name="ner")

        # Validate and store field_name separately
        stripped_field_name = field_name.strip()
        if not stripped_field_name:
            raise ValueError("field_name must not be empty")
        self.field_name = stripped_field_name

    def evaluate(
        self,
        prediction: List[EntitySpan],
        reference: List[EntitySpan],
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Evaluate predicted entity spans against reference spans.

        Uses exact matching: spans must have identical text, entity_type, start, and end.
        Computes precision, recall, and F1 per entity type, then macro F1 across types.

        Args:
            prediction: List of predicted entity spans to evaluate.
            reference: List of reference (ground truth) entity spans.
            **kwargs: Additional keyword arguments (ignored but accepted for interface compatibility).

        Returns:
            FieldEvaluation containing the evaluation results with the following structure:
            - field_name: The field name provided during initialization
            - evaluator_method: Always "ner_exact_match"
            - expected_value: The reference spans
            - obtained_value: The predicted spans
            - score: Macro F1 score (0.0-1.0)
            - prompt_hash: Always None (not applicable for non-LLM evaluator)
            - metadata: Dictionary containing per-type metrics and macro F1

        Example:
            >>> evaluator = NEREvaluator(field_name="entities")
            >>> predicted = [EntitySpan("John", "PERSON", 0, 4)]
            >>> reference = [EntitySpan("John", "PERSON", 0, 4)]
            >>> result = evaluator.evaluate(predicted, reference)
            >>> result.metadata["macro_f1"]
            1.0
        """
        # Use NERMatcher to compute the matching results
        matcher = NERMatcher()
        match_result = matcher.match(prediction, reference)

        # Build metadata according to the design specification
        metadata = {
            "per_type_f1": match_result.per_type_f1,
            "per_type_precision": match_result.per_type_precision,
            "per_type_recall": match_result.per_type_recall,
            "macro_f1": match_result.macro_f1,
        }

        # Return FieldEvaluation with all required fields
        return FieldEvaluation(
            field_name=self.field_name,
            evaluator_method="ner_exact_match",
            expected_value=reference,
            obtained_value=prediction,
            score=match_result.macro_f1,
            prompt_hash=None,
            metadata=metadata
        )
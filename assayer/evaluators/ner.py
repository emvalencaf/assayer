"""Named Entity Recognition (NER) evaluator components."""

from dataclasses import dataclass


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
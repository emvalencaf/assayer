"""A Field that is a list of objects: how to score it, and its validated form."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, get_args

from assayer.metrics import Metric
from assayer.runner.field_map.field_metric import FieldMetric

Align = Literal["key", "best_match", "positional"]
ALIGNMENTS = get_args(Align)


@dataclass(frozen=True)
class ListField:
    """How to score a Field that is a list of objects.

    Each predicted item is paired with an expected one (the Alignment), the pairs
    are scored property by property, and the items left without a pair are
    penalised by `list_precision`, `list_recall` and `list_f1` Scores.

    Args:
        properties: Maps the dotted path of a property, relative to an item, to a
            list of metrics as in the field map, or to a nested `ListField` for
            an array inside the item (aligned the same way, recursively).
        align: How items are paired: "best_match" (greedy by descending
            similarity, the mean of the pair's property Scores, ties by
            position), "key" (items with equal `key`) or "positional" (same index).
        key: Property whose value identifies an item; required by "key".
        threshold: Lowest similarity for "best_match" to pair two items.
    """

    properties: Mapping[str, Any]
    align: Align = "best_match"
    key: str | None = None
    threshold: float = 0.5


@dataclass(frozen=True)
class ListSpec:
    """A validated `ListField`, with its properties built into pairs."""

    path: str
    align: Align
    key: str | None
    threshold: float
    properties: list["FieldMetric | ListSpec"]

    @property
    def similarity_name(self) -> str:
        """Name of the Score that stands for this entry when items are compared."""
        return "list_f1"

    def metrics(self) -> list[Metric]:
        """The metrics this entry applies, nested properties included."""
        return [metric for entry in self.properties for metric in entry.metrics()]

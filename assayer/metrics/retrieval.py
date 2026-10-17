"""Retrieval metrics: how good the ranked `retrieval` Steps of a Trajectory are.

A `retrieval` Step's `output` is the ranked list of what it retrieved, best first. Each
item is a string (its text) or a mapping with an `id` and a `text` (or `content`). The
items of all the retrieval Steps of a Trajectory are read in order as one ranking.
"""

import re
from collections.abc import Callable
from typing import Literal

from assayer.metrics.metric import Metric
from assayer.metrics.retrieved import RetrievedItem, retrieved_items
from assayer.models import Case, Trajectory

MatchMode = Literal["id", "string"]
_REFERENCE_FIELD = {"id": "reference_context_ids", "string": "reference_contexts"}
_MIN_SNIPPET = 20  # characters a retrieved text needs to count by lying inside a reference


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _matches(mode: MatchMode, item: RetrievedItem, reference: str) -> bool:
    """Whether a retrieved item is the reference.

    By id: the ids are equal. By string: the item's text holds the reference, or is a
    snippet of it of at least `_MIN_SNIPPET` characters, so a stray word never counts.
    """
    if mode == "id":
        if item.id is None:
            raise ValueError("a retrieved item has no id to match against reference_context_ids")
        return item.id == reference
    wanted, found = _normalise(reference), _normalise(item.text or "")
    if not wanted or not found:
        return False
    return wanted in found or (len(found) >= _MIN_SNIPPET and found in wanted)


def _references(mode: MatchMode, case: Case) -> list[str]:
    references = getattr(case, _REFERENCE_FIELD[mode])
    if not references:
        raise ValueError(f"{_REFERENCE_FIELD[mode]} is empty: nothing to compare the retrieval to")
    return references


def _retrieval_metric(
    name: str,
    match: MatchMode,
    score: Callable[[list[bool], list[bool]], float],
) -> Metric:
    """Build a metric from the relevance of each retrieved item and of each reference.

    Args:
        name: Name of the metric.
        match: How items are compared to the reference.
        score: Called with, per retrieved item in rank order, whether it is relevant, and,
            per reference, whether it was retrieved.
    """
    if match not in _REFERENCE_FIELD:
        raise ValueError("match must be 'id' or 'string'")

    def fn(trajectory: Trajectory, case: Case) -> float:
        references = _references(match, case)
        items = retrieved_items(trajectory)
        relevant = [any(_matches(match, i, ref) for ref in references) for i in items]
        found = [any(_matches(match, i, ref) for i in items) for ref in references]
        return score(relevant, found)

    return Metric(name=name, level="trajectory", fn=fn, requires=(_REFERENCE_FIELD[match],))


def _average_precision(relevant: list[bool], found: list[bool]) -> float:
    hits = precisions = 0
    for rank, is_relevant in enumerate(relevant, 1):
        if is_relevant:
            hits += 1
            precisions += hits / rank
    return precisions / hits if hits else 0.0


def _recall(relevant: list[bool], found: list[bool]) -> float:
    return sum(found) / len(found)


def make_context_precision(match: MatchMode = "id", name: str = "context_precision") -> Metric:
    """Build the metric for how well the relevant retrieved items are ranked first.

    The Score is the average precision of the ranking: the mean, over the relevant
    items retrieved, of the share of relevant items among the ones up to it, so a
    relevant item ranked higher scores better. Nothing relevant retrieved is 0.

    Args:
        match: "id" compares item ids to `Case.reference_context_ids`; "string" compares
            item texts to `Case.reference_contexts`, ignoring case and whitespace, an
            item being relevant when its text holds a reference or is a snippet of
            one at least 20 characters long.
        name: Name of the metric; becomes the name of its Scores.

    Returns:
        A deterministic trajectory-level Metric. A Case without the reference it needs,
        or a Trajectory without a retrieval Step, is an evaluation failure, never a 0.

    Raises:
        ValueError: If match is not "id" or "string".
    """
    return _retrieval_metric(name, match, _average_precision)


def make_context_recall(match: MatchMode = "id", name: str = "context_recall") -> Metric:
    """Build the metric for the share of reference contexts that were retrieved.

    Args:
        match: "id" or "string", as in `make_context_precision`.
        name: Name of the metric; becomes the name of its Scores.

    Returns:
        A deterministic trajectory-level Metric. A Case without the reference it needs,
        or a Trajectory without a retrieval Step, is an evaluation failure, never a 0.

    Raises:
        ValueError: If match is not "id" or "string".
    """
    return _retrieval_metric(name, match, _recall)


def register_retrieval_metrics(registry) -> None:
    """Register the context precision and recall metrics into a registry.

    Registers `context_precision_id`, `context_precision_string`, `context_recall_id`
    and `context_recall_string`.

    Args:
        registry: The Registry to fill.

    Raises:
        KeyError: If one of the names is already registered.
    """
    for mode in ("id", "string"):
        registry.register(make_context_precision(mode, name=f"context_precision_{mode}"))
        registry.register(make_context_recall(mode, name=f"context_recall_{mode}"))

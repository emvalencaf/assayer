"""Retrieval metrics: how good the ranked `retrieval` Steps of a Trajectory are.

A `retrieval` Step's `output` is the ranked list of what it retrieved, best first. Each
item is a string (its text) or a mapping with an `id` and a `text` (or `content`). The
items of all the retrieval Steps of a Trajectory are read in order as one ranking.
"""

import re
from collections.abc import Mapping
from typing import Any, Literal

from assayer.metrics.metric import Metric
from assayer.models import Case, Trajectory

MatchMode = Literal["id", "string"]
_REFERENCE_FIELD = {"id": "reference_context_ids", "string": "reference_contexts"}


def retrieved_items(trajectory: Trajectory) -> list[tuple[str | None, str | None]]:
    """The ranked `(id, text)` items the retrieval Steps of a Trajectory returned.

    Args:
        trajectory: The Trajectory to read.

    Returns:
        The items in order; an id or text the item does not carry is None.

    Raises:
        ValueError: If the Trajectory has no retrieval Step, or an item is neither a
            string nor a mapping.
    """
    steps = [step for step in trajectory.steps if step.kind == "retrieval"]
    if not steps:
        raise ValueError("the Trajectory has no retrieval Step")
    items = []
    for step in steps:
        output = step.output
        for item in [] if output is None else [output] if _is_item(output) else output:
            if isinstance(item, str):
                items.append((None, item))
            elif isinstance(item, Mapping):
                text = item.get("text", item.get("content"))
                items.append((item.get("id"), None if text is None else str(text)))
            else:
                raise ValueError(f"a retrieved item must be a string or a mapping, got {item!r}")
    return items


def _is_item(output: Any) -> bool:
    return isinstance(output, (str, Mapping))


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def _matches(mode: MatchMode, retrieved: tuple[str | None, str | None], reference: str) -> bool:
    """Whether a retrieved item is the reference: same id, or one text holds the other."""
    item_id, text = retrieved
    if mode == "id":
        if item_id is None:
            raise ValueError("a retrieved item has no id to match against reference_context_ids")
        return item_id == reference
    wanted, found = _normalise(reference), _normalise(text or "")
    return bool(found) and bool(wanted) and (wanted in found or found in wanted)


def _references(mode: MatchMode, case: Case) -> list[str]:
    references = getattr(case, _REFERENCE_FIELD[mode])
    if not references:
        raise ValueError(f"{_REFERENCE_FIELD[mode]} is empty: nothing to compare the retrieval to")
    return references


def _check_mode(mode: str) -> None:
    if mode not in _REFERENCE_FIELD:
        raise ValueError("match must be 'id' or 'string'")


def make_context_precision(match: MatchMode = "id", name: str = "context_precision") -> Metric:
    """Build the metric for how well the relevant retrieved items are ranked first.

    The Score is the average precision of the ranking: the mean, over the relevant
    items retrieved, of the share of relevant items among the ones up to it, so a
    relevant item ranked higher scores better. Nothing relevant retrieved is 0.

    Args:
        match: "id" compares item ids to `Case.reference_context_ids`; "string" compares
            item texts to `Case.reference_contexts`, ignoring case and whitespace, an
            item being relevant when its text holds a reference or the reverse.
        name: Name of the metric; becomes the name of its Scores.

    Returns:
        A deterministic trajectory-level Metric. A Case without the reference it needs,
        or a Trajectory without a retrieval Step, is an evaluation failure, never a 0.

    Raises:
        ValueError: If match is not "id" or "string".
    """
    _check_mode(match)

    def context_precision(trajectory: Trajectory, case: Case) -> float:
        references = _references(match, case)
        relevant = [
            any(_matches(match, item, ref) for ref in references)
            for item in retrieved_items(trajectory)
        ]
        hits = precisions = 0
        for rank, is_relevant in enumerate(relevant, 1):
            if is_relevant:
                hits += 1
                precisions += hits / rank
        return precisions / hits if hits else 0.0

    return Metric(
        name=name,
        level="trajectory",
        fn=context_precision,
        requires=(_REFERENCE_FIELD[match],),
    )


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
    _check_mode(match)

    def context_recall(trajectory: Trajectory, case: Case) -> float:
        references = _references(match, case)
        items = retrieved_items(trajectory)
        found = sum(any(_matches(match, item, ref) for item in items) for ref in references)
        return found / len(references)

    return Metric(
        name=name,
        level="trajectory",
        fn=context_recall,
        requires=(_REFERENCE_FIELD[match],),
    )


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

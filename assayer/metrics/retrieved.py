"""Reading the ranked items that the `retrieval` Steps of a Trajectory returned.

A `retrieval` Step's `output` is the ranked list of what it retrieved, best first. Each
item is a string (its text) or a mapping with an `id` and a `text` (or `content`). The
items of all the retrieval Steps of a Trajectory are read in order as one ranking.
"""

from collections.abc import Mapping
from typing import NamedTuple

from assayer.models import Trajectory


class RetrievedItem(NamedTuple):
    """One retrieved item; an id or text the item does not carry is None."""

    id: str | None
    text: str | None


def retrieved_items(trajectory: Trajectory) -> list[RetrievedItem]:
    """The ranked items the retrieval Steps of a Trajectory returned.

    Args:
        trajectory: The Trajectory to read.

    Returns:
        The items in rank order.

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
        if output is None:
            continue
        for item in [output] if isinstance(output, (str, Mapping)) else output:
            if isinstance(item, str):
                items.append(RetrievedItem(None, item))
            elif isinstance(item, Mapping):
                text = item.get("text", item.get("content"))
                items.append(RetrievedItem(item.get("id"), None if text is None else str(text)))
            else:
                raise ValueError(f"a retrieved item must be a string or a mapping, got {item!r}")
    return items

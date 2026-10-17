"""Dotted paths into a structured output."""

from collections.abc import Mapping, Sequence
from typing import Any


def resolve(value: Any, path: str) -> Any:
    """Read a dotted path out of nested dictionaries and lists.

    Args:
        value: The structured output.
        path: Dotted path; a numeric segment indexes a list.

    Returns:
        What the path points at, or None when any step of it is absent.
    """
    for segment in path.split("."):
        if isinstance(value, Mapping):
            value = value.get(segment)
        elif (
            isinstance(value, Sequence)
            and not isinstance(value, str)
            and segment.isascii()
            and segment.isdigit()
        ):
            index = int(segment)
            value = value[index] if index < len(value) else None
        else:
            return None
    return value

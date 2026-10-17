"""The map from output Fields (dotted paths) to the metrics that score them."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from assayer.metrics import Metric


@dataclass(frozen=True)
class FieldMetric:
    """One metric applied to one Field, with the parameters of that pair.

    Args:
        path: Dotted path of the Field, such as "address.city".
        metric: The metric that scores it.
        params: Keyword parameters passed to the metric's function.
    """

    path: str
    metric: Metric
    params: dict[str, Any] = field(default_factory=dict)


def build_field_map(field_metrics: Mapping[str, Sequence[Any]] | None) -> list[FieldMetric]:
    """Validate a field map and flatten it into (Field, metric, parameters) pairs.

    Args:
        field_metrics: Maps a dotted path to a list whose entries are a Metric, or
            a `(Metric, params)` pair with the parameters for that Field only.

    Returns:
        The pairs, in map order.

    Raises:
        TypeError: If the map is not a mapping, a value is not a list, an entry is
            not a Metric or `(Metric, params)`, or params is not a mapping.
        ValueError: If a path is blank or has an empty segment, a metric is listed twice
            under one path, or a metric is not trajectory-level (a Field is cut out
            of a Trajectory's output).
    """
    if field_metrics is None:
        return []
    if not isinstance(field_metrics, Mapping):
        raise TypeError("field_metrics must be a mapping from dotted path to a list of metrics")

    pairs = []
    for path, entries in field_metrics.items():
        if not isinstance(path, str) or not path.strip() or "" in path.split("."):
            raise ValueError(f"invalid field path {path!r}: use dotted names such as 'a.b'")
        if isinstance(entries, (str, Metric)) or not isinstance(entries, Sequence):
            raise TypeError(f"field {path!r} must map to a list of metrics")
        for entry in entries:
            metric, params = entry if isinstance(entry, tuple) and len(entry) == 2 else (entry, {})
            if not isinstance(metric, Metric):
                raise TypeError(
                    f"field {path!r}: expected a Metric or (Metric, params), got {entry!r}"
                )
            if not isinstance(params, Mapping):
                raise TypeError(f"field {path!r}: parameters of {metric.name!r} must be a mapping")
            if metric.level != "trajectory":
                raise ValueError(
                    f"field {path!r}: metric {metric.name!r} must be trajectory-level, "
                    f"not {metric.level!r}"
                )
            if any(p.path == path and p.metric.name == metric.name for p in pairs):
                raise ValueError(
                    f"field {path!r}: metric {metric.name!r} is listed twice; "
                    "their Scores could not be told apart"
                )
            pairs.append(FieldMetric(path, metric, dict(params)))
    return pairs


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

"""The map from output Fields (dotted paths) to the metrics that score them."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, get_args

from assayer.metrics import Metric

Align = Literal["key", "best_match", "positional"]
ALIGNMENTS = get_args(Align)


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


def build_field_map(
    field_metrics: Mapping[str, Sequence[Any] | ListField] | None,
) -> list[FieldMetric | ListSpec]:
    """Validate a field map and flatten it into (Field, metric, parameters) pairs.

    Args:
        field_metrics: Maps a dotted path to a list whose entries are a Metric, or
            a `(Metric, params)` pair with the parameters for that Field only; or
            to a `ListField` for a list of objects.

    Returns:
        The pairs, in map order; a `ListSpec` for each list Field.

    Raises:
        TypeError: If the map is not a mapping, a value is not a list, an entry is
            not a Metric or `(Metric, params)`, or params is not a mapping.
        ValueError: If a path is blank or has an empty segment, a metric is listed twice
            under one path, or a metric is not trajectory-level (a Field is cut out
            of a Trajectory's output); or a `ListField` has an unknown `align`, a
            "key" alignment without `key`, a `threshold` outside [0, 1], or a
            "best_match" alignment without properties.
    """
    if field_metrics is None:
        return []
    if not isinstance(field_metrics, Mapping):
        raise TypeError("field_metrics must be a mapping from dotted path to a list of metrics")

    pairs: list[FieldMetric | ListSpec] = []
    for path, entries in field_metrics.items():
        if not isinstance(path, str) or not path.strip() or "" in path.split("."):
            raise ValueError(f"invalid field path {path!r}: use dotted names such as 'a.b'")
        if isinstance(entries, ListField):
            pairs.append(_build_list(path, entries))
            continue
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
            if any(
                isinstance(p, FieldMetric) and p.path == path and p.metric.name == metric.name
                for p in pairs
            ):
                raise ValueError(
                    f"field {path!r}: metric {metric.name!r} is listed twice; "
                    "their Scores could not be told apart"
                )
            pairs.append(FieldMetric(path, metric, dict(params)))
    return pairs


def _build_list(path: str, spec: ListField) -> ListSpec:
    if spec.align not in ALIGNMENTS:
        raise ValueError(f"field {path!r}: align must be one of {ALIGNMENTS}, not {spec.align!r}")
    if spec.align == "key" and not spec.key:
        raise ValueError(f"field {path!r}: align='key' needs the key property")
    if isinstance(spec.threshold, bool) or not (
        isinstance(spec.threshold, (int, float)) and 0 <= spec.threshold <= 1
    ):
        raise ValueError(f"field {path!r}: threshold must be a number between 0 and 1")
    properties = build_field_map(spec.properties)
    if spec.align == "best_match" and not properties:
        raise ValueError(f"field {path!r}: best_match needs properties to compare items by")
    return ListSpec(path, spec.align, spec.key, float(spec.threshold), properties)


def metrics_of(entries: Sequence[FieldMetric | ListSpec]) -> list[Metric]:
    """List every metric used by a built field map, nested properties included."""
    metrics: list[Metric] = []
    for entry in entries:
        if isinstance(entry, ListSpec):
            metrics.extend(metrics_of(entry.properties))
        else:
            metrics.append(entry.metric)
    return metrics


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

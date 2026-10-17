"""Validates a field map and builds its entries."""

from collections.abc import Mapping, Sequence
from typing import Any

from assayer.metrics import Metric
from assayer.runner.field_map.field_metric import FieldMetric
from assayer.runner.field_map.list_field import ALIGNMENTS, ListField, ListSpec


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
    return [metric for entry in entries for metric in entry.metrics()]

"""Loads a field map from YAML or JSON and validates it."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from assayer.metrics import register_corpus_metrics, register_field_metrics
from assayer.registries import Registry
from assayer.runner.field_map.builder import build_field_map
from assayer.runner.field_map.list_field import ListField

_LIST_OPTIONS = ("align", "key", "threshold", "properties")


class FieldMapError(ValueError):
    """A field map is malformed: raised at load, before any Runner is built."""


def load_field_map(path: str | Path, registry: Registry | None = None) -> dict[str, Any]:
    """Read a field map from a `.json`, `.yaml` or `.yml` file and validate it.

    Args:
        path: The file. YAML needs the `yaml` extra (`pip install 'assayer[yaml]'`).
        registry: Resolves the metric names; defaults to the field-level and corpus
            metrics (see `parse_field_map`).

    Returns:
        A map to pass as `Runner(field_metrics=...)`.

    Raises:
        FieldMapError: If the extension is unknown, the file cannot be read or does not
            parse, or the map is invalid.
        ImportError: If the file is YAML and the `yaml` extra is not installed.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".json", ".yaml", ".yml"):
        raise FieldMapError(f"{path}: unsupported extension {suffix!r}; use .json, .yaml or .yml")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise FieldMapError(f"{path}: cannot be read: {exc}") from exc
    try:
        if suffix == ".json":
            data = json.loads(text)
        else:
            data = _load_yaml(text)
    except ValueError as exc:
        raise FieldMapError(f"{path}: not valid {suffix.lstrip('.')}: {exc}") from exc
    try:
        return parse_field_map(data, registry)
    except FieldMapError as exc:
        raise FieldMapError(f"{path}: {exc}") from exc


def _load_yaml(text: str) -> Any:
    try:
        import yaml
    except ImportError as exc:
        raise ImportError(
            "Loading a YAML field map needs the yaml extra: pip install 'assayer[yaml]'"
        ) from exc
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(str(exc)) from exc


def parse_field_map(data: Any, registry: Registry | None = None) -> dict[str, Any]:
    """Resolve a field map given as plain data into one a Runner accepts.

    Each dotted path maps to a list of entries, a metric name or `{name: params}`;
    or to a mapping with `properties` (and optionally `align`, `key`, `threshold`)
    for an array of objects, whose properties are a map of the same shape.

    Args:
        data: The parsed YAML or JSON.
        registry: Resolves the metric names. Defaults to a registry with the field-level
            metrics (`exact_match`, `normalized_exact_match`, `numeric_tolerance`,
            `list_f1`) and the corpus metrics (`f1`, `rouge_l`, ...).

    Returns:
        A map of Metrics, `(Metric, params)` pairs and `ListField`s.

    Raises:
        FieldMapError: If the map is not a mapping, names an unknown metric, has
            malformed entries or options, or breaks any rule `Runner(field_metrics=...)` checks.
    """
    if registry is None:
        registry = Registry()
        register_field_metrics(registry)
        register_corpus_metrics(registry)
    field_map = _resolve(data, registry)
    try:
        build_field_map(field_map)
    except (TypeError, ValueError) as exc:
        raise FieldMapError(str(exc)) from exc
    return field_map


def _resolve(data: Any, registry: Registry) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise FieldMapError("a field map must be a mapping from dotted path to metrics")
    return {str(path): _field(str(path), value, registry) for path, value in data.items()}


def _field(path: str, value: Any, registry: Registry) -> Any:
    if isinstance(value, Mapping):
        unknown = sorted(set(value) - set(_LIST_OPTIONS))
        if unknown:
            raise FieldMapError(f"field {path!r}: unknown option {unknown[0]!r} for a list field")
        properties = value.get("properties")
        if not isinstance(properties, Mapping):
            raise FieldMapError(f"field {path!r}: a list field needs a 'properties' map")
        options = {k: v for k, v in value.items() if k != "properties"}
        return ListField(properties=_resolve(properties, registry), **options)
    if not isinstance(value, list):
        raise FieldMapError(f"field {path!r} must map to a list of metrics")
    return [_entry(path, entry, registry) for entry in value]


def _entry(path: str, entry: Any, registry: Registry) -> Any:
    if isinstance(entry, str):
        name, params = entry, None
    elif isinstance(entry, Mapping) and len(entry) == 1:
        name, params = next(iter(entry.items()))
        if not isinstance(name, str):
            raise FieldMapError(f"field {path!r}: a metric name must be a string, not {name!r}")
        if not isinstance(params, Mapping):
            raise FieldMapError(f"field {path!r}: parameters of {name!r} must be a mapping")
    elif isinstance(entry, Mapping):
        raise FieldMapError(f"field {path!r}: write one metric per entry as 'name: {{params}}'")
    else:
        raise FieldMapError(f"field {path!r}: expected a metric name, got {entry!r}")
    try:
        metric = registry.get(name)
    except KeyError:
        raise FieldMapError(f"field {path!r}: unknown metric {name!r}") from None
    return metric if params is None else (metric, dict(params))

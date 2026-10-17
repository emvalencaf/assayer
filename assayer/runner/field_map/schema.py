"""Turns a JSON Schema (or Pydantic model) into an editable field map."""

import json
import re
from dataclasses import dataclass, field
from typing import Any

SHORT_STRING_MAX_LENGTH = 64
_KEY_NAMES = ("id", "key", "uuid")
_KEY_SUFFIX = re.compile(r"(_id|_key|[a-z]Id|[a-z]Key)$")

# Metrics per type. Experiment-level metrics (f1, rouge_l) need a corpus, so inside the
# items of a list they give way to trajectory-level ones.
_CLASS = (["exact_match", "f1"], ["exact_match"])
_SHORT_STRING = (["normalized_exact_match"], ["normalized_exact_match"])
_FREE_STRING = (["rouge_l"], ["normalized_exact_match"])
_NUMBER = ([{"numeric_tolerance": {"tolerance": 0}}],) * 2
_LIST = (["list_f1"], ["list_f1"])
_OTHER = (["exact_match"], ["exact_match"])


@dataclass
class FieldMapDraft:
    """An editable field map drafted from a schema.

    Args:
        spec: The map in the file format `parse_field_map` reads: each dotted path
            maps to a list of metric entries (a name, or `{name: params}`), or to
            a mapping with `align` and `properties` for an array of objects.
        key_hints: For each array of objects (by path), the id-like property found
            in its items. Never used to pair items; written as a comment only.
    """

    spec: dict[str, Any]
    key_hints: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> str:
        """The map as JSON text (JSON has no comments, so the key hints are left out)."""
        return json.dumps(self.spec, indent=2)

    def to_yaml(self) -> str:
        """The map as YAML text, with a commented `key` hint under each array of objects.

        No YAML library is needed to write it; reading it back needs `assayer[yaml]`.
        """
        lines: list[str] = []
        self._emit(self.spec, "", 0, lines)
        return "\n".join(lines) + "\n"

    def _emit(self, spec: dict[str, Any], prefix: str, depth: int, lines: list[str]) -> None:
        pad = "  " * depth
        for path, value in spec.items():
            lines.append(f"{pad}{json.dumps(path)}:")
            if isinstance(value, list):
                lines.extend(f"{pad}  - {json.dumps(entry)}" for entry in value)
                continue
            lines.append(f"{pad}  align: {value['align']}")
            if "key" in value:
                lines.append(f"{pad}  key: {json.dumps(value['key'])}")
            hint = self.key_hints.get(prefix + path)
            if hint and "key" not in value:
                lines.append(f"{pad}  # key: {hint}  # with align: key, pairs items by it")
            if not value["properties"]:
                lines.append(f"{pad}  properties: {{}}")
                continue
            lines.append(f"{pad}  properties:")
            self._emit(value["properties"], f"{prefix}{path}.", depth + 2, lines)


def schema_to_field_map(schema: Any) -> FieldMapDraft:
    """Draft a field map from a JSON Schema or a Pydantic model.

    Default metrics by type:

    * enum, const or boolean: `exact_match` and `f1`.
    * string with a `format`, a `pattern` or a `maxLength` of at most 64: `normalized_exact_match`.
    * any other string: `rouge_l`.
    * integer or number: `numeric_tolerance` with `tolerance: 0`.
    * array of anything but objects: `list_f1`.
    * object: its properties, at dotted paths.
    * array of objects: a `best_match` list Field over the item's properties.
    * anything else: `exact_match`.

    Inside a list item, `f1` and `rouge_l` are left out (a single item has no corpus to be
    scored over) and a free string gets `normalized_exact_match`. An id-like property of an
    item (`id`, `key`, `uuid`, `*_id`, `*_key`) is not scored; it only yields a key hint, unless
    it is the item's only property: then the list aligns by that `key`, with no properties.

    Args:
        schema: A JSON Schema as a dictionary, or a Pydantic model class (anything with
            `model_json_schema()`; Pydantic is not imported).

    Returns:
        The draft; edit `spec` or its YAML and load it with `parse_field_map`.

    Raises:
        ValueError: If the schema does not describe an object with properties, or a property
            has a union of several types or a `$ref` that does not resolve; the message names
            the property, so it can be simplified or dropped from the schema.
    """
    if hasattr(schema, "model_json_schema"):
        schema = schema.model_json_schema()
    root = schema
    node = _resolve(schema, root)
    if _type_of(node) != "object" or not node.get("properties"):
        raise ValueError("the schema must describe an object with properties")
    draft = FieldMapDraft({})
    _object_fields(node, root, "", False, draft.spec, draft.key_hints, "")
    return draft


def _resolve(node: Any, root: dict) -> dict:
    """Follow `$ref`s and drop `null` from unions, so a node has one type.

    Raises:
        ValueError: If a union keeps more than one type, or `$ref`s do not end.
    """
    for _ in range(32):
        if not isinstance(node, dict):
            return {}
        if "$ref" in node:
            target: Any = root
            for part in node["$ref"].removeprefix("#/").split("/"):
                target = target.get(part, {}) if isinstance(target, dict) else {}
            node = target
            continue
        for union in ("anyOf", "oneOf"):
            if union in node:
                options = [o for o in node[union] if _resolve(o, root).get("type") != "null"]
                if len(options) == 1:
                    node = options[0]
                    break
                raise ValueError(f"{union} with {len(options)} non-null options is not supported")
        else:
            return node
    raise ValueError("$ref chain does not end")


def _type_of(node: dict) -> str | None:
    kind = node.get("type")
    if isinstance(kind, list):
        kind = next((k for k in kind if k != "null"), None)
    return kind


def _is_key(name: str) -> bool:
    return name.lower() in _KEY_NAMES or bool(_KEY_SUFFIX.search(name))


def _defaults(node: dict) -> tuple[list, list]:
    if "enum" in node or "const" in node:
        return _CLASS
    kind = _type_of(node)
    if kind == "boolean":
        return _CLASS
    if kind == "string":
        short = (
            "format" in node
            or "pattern" in node
            or node.get("maxLength", SHORT_STRING_MAX_LENGTH + 1) <= SHORT_STRING_MAX_LENGTH
        )
        return _SHORT_STRING if short else _FREE_STRING
    if kind in ("integer", "number"):
        return _NUMBER
    if kind == "array":
        return _LIST
    return _OTHER


def _object_fields(
    node: dict,
    root: dict,
    prefix: str,
    in_item: bool,
    out: dict[str, Any],
    hints: dict[str, str],
    hint_prefix: str,
) -> None:
    for name, raw in node.get("properties", {}).items():
        path = f"{prefix}{name}"
        try:
            child = _resolve(raw, root)
            kind = _type_of(child)
            item = _resolve(child.get("items", {}), root) if kind == "array" else {}
        except ValueError as exc:
            raise ValueError(f"property '{hint_prefix}{path}': {exc}") from exc
        if kind == "object" and child.get("properties"):
            _object_fields(child, root, f"{path}.", in_item, out, hints, hint_prefix)
        elif kind == "array" and _type_of(item) == "object" and item.get("properties"):
            out[path] = _list_field(item, root, hints, hint_prefix + path)
        else:
            out[path] = list(_defaults(child)[in_item])


def _list_field(item: dict, root: dict, hints: dict[str, str], full_path: str) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    _object_fields(item, root, "", True, properties, hints, f"{full_path}.")
    keys = [name for name in item["properties"] if _is_key(name)]
    if keys:
        hints[full_path] = min(keys, key=lambda k: (k.lower() not in _KEY_NAMES, keys.index(k)))
        # the key property is only a hint; scoring it would not help pair the items
        properties = {p: v for p, v in properties.items() if p.split(".")[0] not in keys}
        if not properties:
            # nothing else to compare the items by: the key is the only way to pair them
            return {"align": "key", "key": hints[full_path], "properties": {}}
    return {"align": "best_match", "properties": properties}

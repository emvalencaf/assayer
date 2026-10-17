"""Tests for turning a JSON Schema into an editable field map."""

import json

import pytest

from assayer.models import Case, Dataset
from assayer.runner import Runner, parse_field_map, schema_to_field_map

SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"enum": ["open", "closed"]},
        "urgent": {"type": "boolean"},
        "code": {"type": "string", "maxLength": 8},
        "summary": {"type": "string"},
        "amount": {"type": "number"},
        "count": {"type": "integer"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "address": {
            "type": "object",
            "properties": {"city": {"type": "string", "maxLength": 20}, "zip": {"type": "integer"}},
        },
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string", "maxLength": 20},
                    "qty": {"type": "integer"},
                    "kind": {"enum": ["a", "b"]},
                    "notes": {"type": "string"},
                },
            },
        },
    },
}


def _names(entries):
    return [e if isinstance(e, str) else next(iter(e)) for e in entries]


class TestDefaultMetrics:
    def test_each_type_gets_its_documented_default(self):
        spec = schema_to_field_map(SCHEMA).spec

        assert _names(spec["status"]) == ["exact_match", "f1"]
        assert _names(spec["urgent"]) == ["exact_match", "f1"]
        assert _names(spec["code"]) == ["normalized_exact_match"]
        assert _names(spec["summary"]) == ["rouge_l"]
        assert spec["amount"] == [{"numeric_tolerance": {"tolerance": 0}}]
        assert spec["count"] == [{"numeric_tolerance": {"tolerance": 0}}]
        assert _names(spec["tags"]) == ["list_f1"]

    def test_objects_recurse_into_dotted_paths(self):
        spec = schema_to_field_map(SCHEMA).spec

        assert _names(spec["address.city"]) == ["normalized_exact_match"]
        assert "address.zip" in spec
        assert "address" not in spec

    def test_an_array_of_objects_becomes_a_best_match_list_field(self):
        lines = schema_to_field_map(SCHEMA).spec["lines"]

        assert lines["align"] == "best_match"
        props = lines["properties"]
        # corpus-level metrics cannot score a list item, so only trajectory-level ones remain
        assert _names(props["kind"]) == ["exact_match"]
        assert _names(props["notes"]) == ["normalized_exact_match"]
        assert _names(props["name"]) == ["normalized_exact_match"]
        assert "qty" in props

    def test_nullable_and_referenced_types_are_understood(self):
        schema = {
            "type": "object",
            "properties": {
                "nick": {"anyOf": [{"type": "string", "maxLength": 5}, {"type": "null"}]},
                "age": {"type": ["integer", "null"]},
                "home": {"$ref": "#/$defs/Home"},
            },
            "$defs": {"Home": {"type": "object", "properties": {"city": {"type": "string"}}}},
        }

        spec = schema_to_field_map(schema).spec

        assert _names(spec["nick"]) == ["normalized_exact_match"]
        assert _names(spec["age"]) == ["numeric_tolerance"]
        assert _names(spec["home.city"]) == ["rouge_l"]

    def test_a_pydantic_model_is_accepted(self):
        class Model:
            @classmethod
            def model_json_schema(cls):
                return SCHEMA

        assert schema_to_field_map(Model).spec == schema_to_field_map(SCHEMA).spec


class TestKeyHint:
    def test_an_id_property_only_yields_a_commented_key_hint(self):
        draft = schema_to_field_map(SCHEMA)

        assert "id" not in draft.spec["lines"]["properties"]
        assert draft.key_hints == {"lines": "id"}
        assert "# key: id" in draft.to_yaml()
        uncommented = [ln for ln in draft.to_yaml().splitlines() if not ln.lstrip().startswith("#")]
        assert not any("key" in ln for ln in uncommented)

    def test_a_key_hint_never_changes_the_alignment(self):
        draft = schema_to_field_map(SCHEMA)

        assert draft.spec["lines"]["align"] == "best_match"
        assert "key" not in draft.spec["lines"]

    def test_an_item_with_only_a_key_property_still_has_something_to_compare(self):
        schema = {
            "type": "object",
            "properties": {
                "rows": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"id": {"type": "string"}}},
                }
            },
        }

        draft = schema_to_field_map(schema)

        assert list(draft.spec["rows"]["properties"]) == ["id"]
        parse_field_map(draft.spec)


class TestEditableOutput:
    def test_the_json_output_loads_back_and_drives_a_runner(self):
        draft = schema_to_field_map(SCHEMA)
        field_map = parse_field_map(json.loads(draft.to_json()))
        output = {
            "status": "open",
            "lines": [{"name": "bolt", "qty": 2, "kind": "a", "notes": "n"}],
        }
        case = Case(input="x", id="c1", expected_output=output)

        experiment = Runner(field_metrics=field_map).score(Dataset("d", [case]), [output])

        by_field = {(s.field, s.name): s.value for s in experiment.scores}
        assert by_field[("status", "exact_match")] == 1.0
        assert by_field[("lines.name", "normalized_exact_match")] == 1.0
        assert by_field[("lines", "list_f1")] == 1.0

    def test_the_yaml_output_loads_back(self):
        yaml = pytest.importorskip("yaml")
        draft = schema_to_field_map(SCHEMA)

        assert (
            parse_field_map(yaml.safe_load(draft.to_yaml())).keys()
            == parse_field_map(draft.spec).keys()
        )


def test_a_schema_that_is_not_an_object_is_rejected():
    with pytest.raises(ValueError, match="object"):
        schema_to_field_map({"type": "string"})

"""Tests for loading a field map from YAML or JSON and validating it."""

import json

import pytest

from assayer.models import Case, Dataset
from assayer.runner import FieldMapError, ListField, Runner, load_field_map, parse_field_map

MAP = {
    "label": ["exact_match"],
    "score": [{"numeric_tolerance": {"tolerance": 1}}],
    "items": {
        "align": "key",
        "key": "id",
        "threshold": 0.7,
        "properties": {"name": ["normalized_exact_match"]},
    },
}


def _run(field_map):
    output = {"label": "a", "score": 5, "items": [{"id": "1", "name": "Bolt"}]}
    predicted = {"label": "a", "score": 6, "items": [{"id": "1", "name": " bolt "}]}
    case = Case(input="x", id="c1", expected_output=output)
    experiment = Runner(field_metrics=field_map).score(Dataset("d", [case]), [predicted])
    return {(s.field, s.name): s.value for s in experiment.scores}


class TestLoading:
    def test_a_json_file_loads_into_a_map_a_runner_accepts(self, tmp_path):
        path = tmp_path / "map.json"
        path.write_text(json.dumps(MAP))

        scores = _run(load_field_map(path))

        assert scores[("label", "exact_match")] == 1.0
        assert scores[("score", "numeric_tolerance")] == 1.0
        assert scores[("items.name", "normalized_exact_match")] == 1.0

    def test_a_yaml_file_loads_the_same_map(self, tmp_path):
        pytest.importorskip("yaml")
        path = tmp_path / "map.yaml"
        path.write_text(
            """
label: [exact_match]
score:
  - numeric_tolerance: {tolerance: 1}
items:
  align: key
  key: id          # pairs items by id
  threshold: 0.7
  properties:
    name: [normalized_exact_match]
"""
        )

        assert _run(load_field_map(path)) == _run(parse_field_map(MAP))

    def test_the_list_field_keeps_its_options(self):
        items = parse_field_map(MAP)["items"]

        assert isinstance(items, ListField)
        assert (items.align, items.key, items.threshold) == ("key", "id", 0.7)

    def test_a_custom_registry_supplies_the_metrics(self):
        from assayer.metrics import Metric
        from assayer.registries import Registry

        registry = Registry()
        registry.register(Metric("mine", "trajectory", lambda t, c: 1.0))

        assert parse_field_map({"a": ["mine"]}, registry)["a"][0].name == "mine"

    def test_yaml_without_the_extra_names_it(self, tmp_path, monkeypatch):
        import builtins

        real = builtins.__import__

        def no_yaml(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("no yaml")
            return real(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", no_yaml)
        path = tmp_path / "map.yml"
        path.write_text("a: [exact_match]")

        with pytest.raises(ImportError, match=r"assayer\[yaml\]"):
            load_field_map(path)


class TestInvalidMaps:
    @pytest.mark.parametrize(
        ("data", "message"),
        [
            (["exact_match"], "mapping"),
            ({"a": "exact_match"}, "'a'.*list"),
            ({"a": ["nope"]}, "unknown metric 'nope'"),
            ({"a": [3]}, "'a'.*metric name"),
            ({"a": [{"exact_match": 1}]}, "'a'.*parameters.*mapping"),
            ({"a": [{"exact_match": {}, "f1": {}}]}, "'a'.*one metric"),
            ({"a": ["exact_match", "exact_match"]}, "listed twice"),
            ({"a..b": ["exact_match"]}, "invalid field path"),
            ({"a": ["bleu"], "b": {"properties": {"c": ["bleu"]}}}, "trajectory-level"),
            ({"a": ["exact_match", {"f1": {}}, "bleu"]}, None),
            ({"a": {"align": "fuzzy", "properties": {"b": ["exact_match"]}}}, "align"),
            ({"a": {"align": "key", "properties": {"b": ["exact_match"]}}}, "key"),
            ({"a": {"threshold": 2, "properties": {"b": ["exact_match"]}}}, "threshold"),
            ({"a": {"properties": {}}}, "properties"),
            ({"a": {"props": {"b": ["exact_match"]}}}, "unknown option.*props"),
            ({"a": {"align": "positional"}}, "properties"),
        ],
    )
    def test_fail_at_load_with_a_clear_error(self, data, message):
        if message is None:
            parse_field_map(data)
            return
        with pytest.raises(FieldMapError, match=message):
            parse_field_map(data)

    def test_the_error_is_a_value_error(self):
        assert issubclass(FieldMapError, ValueError)

    def test_a_file_that_does_not_parse_is_reported_with_its_name(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{not json")

        with pytest.raises(FieldMapError, match="broken.json"):
            load_field_map(path)

    def test_an_unknown_extension_is_rejected(self, tmp_path):
        path = tmp_path / "map.txt"
        path.write_text("{}")

        with pytest.raises(FieldMapError, match=r"\.json.*\.yaml"):
            load_field_map(path)

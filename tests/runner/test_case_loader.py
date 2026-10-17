"""Tests for load_cases."""

import pytest

from assayer.metrics import Metric
from assayer.runner import load_cases


def _metric(*requires):
    return Metric(name="m", level="trajectory", fn=lambda t, c: 1.0, requires=requires)


def test_builds_cases_from_a_list():
    dataset = load_cases([{"input": "a", "id": "c1"}])

    assert [c.id for c in dataset.cases] == ["c1"]


def test_requires_of_non_case_fields_are_not_checked_at_load():
    assert len(load_cases([{"input": "a"}], [_metric("final_state")]).cases) == 1


def test_missing_required_field_names_the_case():
    with pytest.raises(ValueError, match="Case 1 .*expected_output"):
        load_cases(
            [{"input": "a", "expected_output": "x"}, {"input": "b"}], [_metric("expected_output")]
        )


def test_missing_file_and_non_list_json(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_cases(str(tmp_path / "nope.json"))
    path = tmp_path / "d.json"
    path.write_text("{}")
    with pytest.raises(TypeError):
        load_cases(str(path))


def test_an_empty_list_and_an_empty_json_file_are_empty_datasets(tmp_path):
    path = tmp_path / "d.json"
    path.write_text("[]")

    assert load_cases([]).cases == []
    assert load_cases(str(path)).cases == []


def test_json_file_loads_and_is_named_after_the_file(tmp_path):
    path = tmp_path / "tickets.json"
    path.write_text('[{"input": "a", "expected_output": "x", "id": "c1"}]')

    dataset = load_cases(str(path), [_metric("expected_output")])

    assert (dataset.name, dataset.cases[0].expected_output) == ("tickets", "x")


def test_a_file_missing_a_required_key_is_rejected(tmp_path):
    path = tmp_path / "d.json"
    path.write_text('[{"input": "a"}]')

    with pytest.raises(ValueError, match="expected_output"):
        load_cases(str(path), [_metric("expected_output")])


def test_non_dictionary_entry_and_unknown_key_are_rejected():
    with pytest.raises(ValueError, match="dictionary"):
        load_cases(["a"])
    with pytest.raises(ValueError, match="unknown keys"):
        load_cases([{"input": "a", "extra": 1}])

"""Tests for dotted paths."""

from assayer.path import resolve


def test_reads_nested_dictionaries_and_list_indexes():
    assert resolve({"a": {"b": [{"c": 7}]}}, "a.b.0.c") == 7


def test_absent_step_is_none():
    assert resolve({"a": 1}, "a.b") is None
    assert resolve({"a": [1]}, "a.3") is None
    assert resolve({"a": "text"}, "a.0") is None  # a string is not indexed

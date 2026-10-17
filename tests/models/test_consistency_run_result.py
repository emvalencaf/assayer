"""Tests for ConsistencyRunResult dataclass (SPEC-001-TASK-001)."""

import dataclasses
from typing import Any, get_type_hints

import pytest

from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation


def make_field_evaluation() -> ConsistencyFieldEvaluation:
    """Create a minimal valid ConsistencyFieldEvaluation for use in tests."""
    return ConsistencyFieldEvaluation(
        group_key="grp",
        n=1,
        agreement_rate=1.0,
        dominant_label="label_a",
        entropy=0.0,
        score_std=0.0,
        correct_rate=1.0,
        pass_at_k=True,
        recall_at_k=1.0,
    )


class TestConsistencyRunResultIsDataclass:
    """Verify that ConsistencyRunResult is a proper @dataclass."""

    def test_module_is_importable(self):
        """ConsistencyRunResult must be importable from its canonical module path."""
        try:
            from assayer.models.consistency_run_result import ConsistencyRunResult  # noqa: F401
        except ImportError as exc:
            pytest.fail(f"Could not import ConsistencyRunResult: {exc}")

    def test_class_is_decorated_as_dataclass(self):
        """ConsistencyRunResult must be decorated with @dataclass."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        assert dataclasses.is_dataclass(ConsistencyRunResult), (
            "ConsistencyRunResult must be a @dataclass"
        )

    def test_class_is_a_class_not_an_instance(self):
        """dataclasses.is_dataclass returns True for the class itself, not only instances."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        assert isinstance(ConsistencyRunResult, type), "ConsistencyRunResult must be a class"


class TestConsistencyRunResultFields:
    """Verify that ConsistencyRunResult exposes the correct fields with correct types."""

    def test_has_input_field(self):
        """ConsistencyRunResult must have a field named 'input'."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        field_names = {f.name for f in dataclasses.fields(ConsistencyRunResult)}
        assert "input" in field_names, "Field 'input' is missing from ConsistencyRunResult"

    def test_has_per_field_evaluations_field(self):
        """ConsistencyRunResult must have a field named 'per_field_evaluations'."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        field_names = {f.name for f in dataclasses.fields(ConsistencyRunResult)}
        assert "per_field_evaluations" in field_names, (
            "Field 'per_field_evaluations' is missing from ConsistencyRunResult"
        )

    def test_input_field_type_hint_is_any(self):
        """The 'input' field must be annotated with type Any."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        hints = get_type_hints(ConsistencyRunResult)
        assert "input" in hints, "Field 'input' must have a type hint"
        assert hints["input"] is Any, (
            f"Field 'input' must be annotated as Any, got {hints['input']}"
        )

    def test_per_field_evaluations_type_hint(self):
        """The 'per_field_evaluations' field must be annotated as dict[str, ConsistencyFieldEvaluation]."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        hints = get_type_hints(ConsistencyRunResult)
        assert "per_field_evaluations" in hints, (
            "Field 'per_field_evaluations' must have a type hint"
        )
        hint = hints["per_field_evaluations"]
        # The origin must be dict
        origin = getattr(hint, "__origin__", None)
        assert origin is dict, f"'per_field_evaluations' must be annotated as dict[...], got {hint}"
        args = getattr(hint, "__args__", ())
        assert len(args) == 2, (
            f"'per_field_evaluations' dict must have two type parameters, got {hint}"
        )
        assert args[0] is str, f"'per_field_evaluations' key type must be str, got {args[0]}"
        assert args[1] is ConsistencyFieldEvaluation, (
            f"'per_field_evaluations' value type must be ConsistencyFieldEvaluation, got {args[1]}"
        )

    def test_exactly_two_fields(self):
        """ConsistencyRunResult must have exactly the two specified fields."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        field_names = [f.name for f in dataclasses.fields(ConsistencyRunResult)]
        assert set(field_names) == {"input", "per_field_evaluations"}, (
            f"Expected fields {{'input', 'per_field_evaluations'}}, got {set(field_names)}"
        )


class TestConsistencyRunResultInstantiation:
    """Verify that ConsistencyRunResult can be instantiated correctly."""

    def test_instantiation_with_simple_input_and_empty_dict(self):
        """ConsistencyRunResult can be created with a simple input and empty per_field_evaluations."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        result = ConsistencyRunResult(input="hello", per_field_evaluations={})
        assert result.input == "hello"
        assert result.per_field_evaluations == {}

    def test_instantiation_with_dict_input(self):
        """ConsistencyRunResult.input accepts a dict (Any allows all types)."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        payload = {"key": "value", "number": 42}
        result = ConsistencyRunResult(input=payload, per_field_evaluations={})
        assert result.input == payload

    def test_instantiation_with_none_input(self):
        """ConsistencyRunResult.input accepts None (Any allows None)."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        result = ConsistencyRunResult(input=None, per_field_evaluations={})
        assert result.input is None

    def test_instantiation_with_integer_input(self):
        """ConsistencyRunResult.input accepts an integer."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        result = ConsistencyRunResult(input=99, per_field_evaluations={})
        assert result.input == 99

    def test_instantiation_with_list_input(self):
        """ConsistencyRunResult.input accepts a list."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        result = ConsistencyRunResult(input=[1, 2, 3], per_field_evaluations={})
        assert result.input == [1, 2, 3]

    def test_per_field_evaluations_stores_consistency_field_evaluations(self):
        """per_field_evaluations stores ConsistencyFieldEvaluation instances keyed by str."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        fe = make_field_evaluation()
        result = ConsistencyRunResult(
            input="test",
            per_field_evaluations={"field_a": fe},
        )
        assert "field_a" in result.per_field_evaluations
        assert result.per_field_evaluations["field_a"] is fe

    def test_per_field_evaluations_with_multiple_entries(self):
        """per_field_evaluations can hold multiple key-value pairs."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        fe1 = make_field_evaluation()
        fe2 = ConsistencyFieldEvaluation(
            group_key=None,
            n=3,
            agreement_rate=0.7,
            dominant_label=None,
            entropy=1.2,
            score_std=0.3,
            correct_rate=0.6,
            pass_at_k=False,
            recall_at_k=0.5,
        )
        result = ConsistencyRunResult(
            input={"prompt": "hi"},
            per_field_evaluations={"field_x": fe1, "field_y": fe2},
        )
        assert len(result.per_field_evaluations) == 2
        assert result.per_field_evaluations["field_x"] is fe1
        assert result.per_field_evaluations["field_y"] is fe2

    def test_input_value_is_stored_unchanged(self):
        """The input field stores the exact object passed, with no transformation."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        obj = object()
        result = ConsistencyRunResult(input=obj, per_field_evaluations={})
        assert result.input is obj


class TestConsistencyRunResultDocstring:
    """Verify that ConsistencyRunResult has a proper Google-style docstring."""

    def test_class_has_docstring(self):
        """ConsistencyRunResult must have a non-empty docstring."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        assert ConsistencyRunResult.__doc__ is not None, (
            "ConsistencyRunResult must have a docstring"
        )
        assert ConsistencyRunResult.__doc__.strip() != "", (
            "ConsistencyRunResult docstring must not be empty"
        )

    def test_docstring_contains_args_section(self):
        """The docstring must contain an 'Args:' section (Google style)."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        doc = ConsistencyRunResult.__doc__ or ""
        assert "Args:" in doc, "ConsistencyRunResult docstring must include an 'Args:' section"

    def test_docstring_documents_input_field(self):
        """The docstring Args section must mention the 'input' field."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        doc = ConsistencyRunResult.__doc__ or ""
        assert "input" in doc, "ConsistencyRunResult docstring must document the 'input' field"

    def test_docstring_documents_per_field_evaluations_field(self):
        """The docstring Args section must mention the 'per_field_evaluations' field."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        doc = ConsistencyRunResult.__doc__ or ""
        assert "per_field_evaluations" in doc, (
            "ConsistencyRunResult docstring must document the 'per_field_evaluations' field"
        )

    def test_docstring_has_description_before_args(self):
        """The docstring must have descriptive text before the Args section."""
        from assayer.models.consistency_run_result import ConsistencyRunResult

        doc = (ConsistencyRunResult.__doc__ or "").strip()
        args_index = doc.find("Args:")
        assert args_index > 0, (
            "ConsistencyRunResult docstring must contain a description before the 'Args:' section"
        )
        description_part = doc[:args_index].strip()
        assert len(description_part) > 0, (
            "ConsistencyRunResult docstring must have a non-empty description before 'Args:'"
        )

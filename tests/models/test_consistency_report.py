"""Tests for ConsistencyReport dataclass (SPEC-001-TASK-002)."""

import dataclasses
from typing import get_type_hints

import pytest

from assayer.models.consistency_run_result import ConsistencyRunResult
from assayer.models.consistency_summary import ConsistencySummary


def make_consistency_summary() -> ConsistencySummary:
    """Create a minimal valid ConsistencySummary for use in tests."""
    return ConsistencySummary(
        mean_agreement_rate=1.0,
        mean_entropy=0.0,
        mean_score_std=0.0,
        mean_correct_rate=1.0,
        pass_at_k_rate=1.0,
        mean_recall_at_k=1.0,
    )


def make_consistency_run_result() -> ConsistencyRunResult:
    """Create a minimal valid ConsistencyRunResult for use in tests."""
    return ConsistencyRunResult(input="sample_input", per_field_evaluations={})


class TestConsistencyReportIsDataclass:
    """Verify that ConsistencyReport is a proper @dataclass."""

    def test_module_is_importable(self):
        """ConsistencyReport must be importable from its canonical module path."""
        try:
            from assayer.models.consistency_report import ConsistencyReport  # noqa: F401
        except ImportError as exc:
            pytest.fail(f"Could not import ConsistencyReport: {exc}")

    def test_class_is_decorated_as_dataclass(self):
        """ConsistencyReport must be decorated with @dataclass."""
        from assayer.models.consistency_report import ConsistencyReport

        assert dataclasses.is_dataclass(ConsistencyReport), "ConsistencyReport must be a @dataclass"

    def test_class_is_a_class_not_an_instance(self):
        """dataclasses.is_dataclass returns True for the class itself, not only instances."""
        from assayer.models.consistency_report import ConsistencyReport

        assert isinstance(ConsistencyReport, type), "ConsistencyReport must be a class"


class TestConsistencyReportFields:
    """Verify that ConsistencyReport exposes the correct fields with correct types."""

    def test_has_experiment_name_field(self):
        """ConsistencyReport must have a field named 'experiment_name'."""
        from assayer.models.consistency_report import ConsistencyReport

        field_names = {f.name for f in dataclasses.fields(ConsistencyReport)}
        assert "experiment_name" in field_names, (
            "Field 'experiment_name' is missing from ConsistencyReport"
        )

    def test_has_k_field(self):
        """ConsistencyReport must have a field named 'k'."""
        from assayer.models.consistency_report import ConsistencyReport

        field_names = {f.name for f in dataclasses.fields(ConsistencyReport)}
        assert "k" in field_names, "Field 'k' is missing from ConsistencyReport"

    def test_has_per_field_field(self):
        """ConsistencyReport must have a field named 'per_field'."""
        from assayer.models.consistency_report import ConsistencyReport

        field_names = {f.name for f in dataclasses.fields(ConsistencyReport)}
        assert "per_field" in field_names, "Field 'per_field' is missing from ConsistencyReport"

    def test_has_runs_field(self):
        """ConsistencyReport must have a field named 'runs'."""
        from assayer.models.consistency_report import ConsistencyReport

        field_names = {f.name for f in dataclasses.fields(ConsistencyReport)}
        assert "runs" in field_names, "Field 'runs' is missing from ConsistencyReport"

    def test_experiment_name_type_hint_is_str(self):
        """The 'experiment_name' field must be annotated with type str."""
        from assayer.models.consistency_report import ConsistencyReport

        hints = get_type_hints(ConsistencyReport)
        assert "experiment_name" in hints, "Field 'experiment_name' must have a type hint"
        assert hints["experiment_name"] is str, (
            f"Field 'experiment_name' must be annotated as str, got {hints['experiment_name']}"
        )

    def test_k_type_hint_is_int(self):
        """The 'k' field must be annotated with type int."""
        from assayer.models.consistency_report import ConsistencyReport

        hints = get_type_hints(ConsistencyReport)
        assert "k" in hints, "Field 'k' must have a type hint"
        assert hints["k"] is int, f"Field 'k' must be annotated as int, got {hints['k']}"

    def test_per_field_type_hint(self):
        """The 'per_field' field must be annotated as dict[str, ConsistencySummary]."""
        from assayer.models.consistency_report import ConsistencyReport

        hints = get_type_hints(ConsistencyReport)
        assert "per_field" in hints, "Field 'per_field' must have a type hint"
        hint = hints["per_field"]
        origin = getattr(hint, "__origin__", None)
        assert origin is dict, f"'per_field' must be annotated as dict[...], got {hint}"
        args = getattr(hint, "__args__", ())
        assert len(args) == 2, f"'per_field' dict must have two type parameters, got {hint}"
        assert args[0] is str, f"'per_field' key type must be str, got {args[0]}"
        assert args[1] is ConsistencySummary, (
            f"'per_field' value type must be ConsistencySummary, got {args[1]}"
        )

    def test_runs_type_hint(self):
        """The 'runs' field must be annotated as list[ConsistencyRunResult]."""
        from assayer.models.consistency_report import ConsistencyReport

        hints = get_type_hints(ConsistencyReport)
        assert "runs" in hints, "Field 'runs' must have a type hint"
        hint = hints["runs"]
        origin = getattr(hint, "__origin__", None)
        assert origin is list, f"'runs' must be annotated as list[...], got {hint}"
        args = getattr(hint, "__args__", ())
        assert len(args) == 1, f"'runs' list must have one type parameter, got {hint}"
        assert args[0] is ConsistencyRunResult, (
            f"'runs' element type must be ConsistencyRunResult, got {args[0]}"
        )

    def test_exactly_four_fields(self):
        """ConsistencyReport must have exactly the four specified fields."""
        from assayer.models.consistency_report import ConsistencyReport

        field_names = {f.name for f in dataclasses.fields(ConsistencyReport)}
        assert field_names == {"experiment_name", "k", "per_field", "runs"}, (
            f"Expected fields {{'experiment_name', 'k', 'per_field', 'runs'}}, got {field_names}"
        )


class TestConsistencyReportInstantiation:
    """Verify that ConsistencyReport can be instantiated correctly."""

    def test_instantiation_with_valid_arguments(self):
        """ConsistencyReport can be created with valid arguments."""
        from assayer.models.consistency_report import ConsistencyReport

        report = ConsistencyReport(
            experiment_name="my_experiment",
            k=3,
            per_field={},
            runs=[],
        )
        assert report.experiment_name == "my_experiment"
        assert report.k == 3
        assert report.per_field == {}
        assert report.runs == []

    def test_instantiation_with_per_field_entries(self):
        """ConsistencyReport stores per_field mapping of ConsistencySummary instances."""
        from assayer.models.consistency_report import ConsistencyReport

        summary = make_consistency_summary()
        report = ConsistencyReport(
            experiment_name="exp",
            k=1,
            per_field={"field_a": summary},
            runs=[],
        )
        assert "field_a" in report.per_field
        assert report.per_field["field_a"] is summary

    def test_instantiation_with_runs_entries(self):
        """ConsistencyReport stores runs as a list of ConsistencyRunResult."""
        from assayer.models.consistency_report import ConsistencyReport

        run = make_consistency_run_result()
        report = ConsistencyReport(
            experiment_name="exp",
            k=2,
            per_field={},
            runs=[run],
        )
        assert len(report.runs) == 1
        assert report.runs[0] is run

    def test_instantiation_stores_values_unchanged(self):
        """ConsistencyReport stores the exact objects passed as arguments."""
        from assayer.models.consistency_report import ConsistencyReport

        summary = make_consistency_summary()
        run = make_consistency_run_result()
        per_field = {"field_x": summary}
        runs = [run]

        report = ConsistencyReport(
            experiment_name="test_exp",
            k=5,
            per_field=per_field,
            runs=runs,
        )
        assert report.per_field is per_field
        assert report.runs is runs

    def test_k_equal_to_one_is_valid(self):
        """k=1 is the minimum valid value and must not raise."""
        from assayer.models.consistency_report import ConsistencyReport

        report = ConsistencyReport(
            experiment_name="exp",
            k=1,
            per_field={},
            runs=[],
        )
        assert report.k == 1

    def test_multiple_runs_and_per_field_entries(self):
        """ConsistencyReport stores multiple runs and multiple per_field entries."""
        from assayer.models.consistency_report import ConsistencyReport

        summary_a = make_consistency_summary()
        summary_b = ConsistencySummary(
            mean_agreement_rate=0.5,
            mean_entropy=0.8,
            mean_score_std=0.2,
            mean_correct_rate=0.5,
            pass_at_k_rate=0.5,
            mean_recall_at_k=0.5,
        )
        run1 = make_consistency_run_result()
        run2 = ConsistencyRunResult(input={"key": "val"}, per_field_evaluations={})

        report = ConsistencyReport(
            experiment_name="full_exp",
            k=3,
            per_field={"field_a": summary_a, "field_b": summary_b},
            runs=[run1, run2],
        )
        assert len(report.per_field) == 2
        assert len(report.runs) == 2


class TestConsistencyReportValidation:
    """Verify that __post_init__ raises ValueError for invalid inputs."""

    def test_empty_experiment_name_raises_value_error(self):
        """__post_init__ must raise ValueError when experiment_name is an empty string."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="",
                k=1,
                per_field={},
                runs=[],
            )

    def test_whitespace_only_experiment_name_raises_value_error(self):
        """__post_init__ must raise ValueError when experiment_name is whitespace-only."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="   ",
                k=1,
                per_field={},
                runs=[],
            )

    def test_tab_only_experiment_name_raises_value_error(self):
        """__post_init__ must raise ValueError when experiment_name is a tab character."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="\t",
                k=1,
                per_field={},
                runs=[],
            )

    def test_newline_only_experiment_name_raises_value_error(self):
        """__post_init__ must raise ValueError when experiment_name is only newlines."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="\n\n",
                k=1,
                per_field={},
                runs=[],
            )

    def test_k_zero_raises_value_error(self):
        """__post_init__ must raise ValueError when k is 0."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="exp",
                k=0,
                per_field={},
                runs=[],
            )

    def test_k_negative_raises_value_error(self):
        """__post_init__ must raise ValueError when k is negative."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="exp",
                k=-1,
                per_field={},
                runs=[],
            )

    def test_k_large_negative_raises_value_error(self):
        """__post_init__ must raise ValueError when k is a large negative integer."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="exp",
                k=-100,
                per_field={},
                runs=[],
            )

    def test_valid_experiment_name_with_spaces_does_not_raise(self):
        """experiment_name with non-whitespace content mixed with spaces is valid."""
        from assayer.models.consistency_report import ConsistencyReport

        report = ConsistencyReport(
            experiment_name="  valid name  ",
            k=1,
            per_field={},
            runs=[],
        )
        assert report.experiment_name == "  valid name  "

    def test_both_invalid_raises_value_error(self):
        """When both experiment_name and k are invalid, ValueError must be raised."""
        from assayer.models.consistency_report import ConsistencyReport

        with pytest.raises(ValueError):
            ConsistencyReport(
                experiment_name="",
                k=0,
                per_field={},
                runs=[],
            )


class TestConsistencyReportDocstring:
    """Verify that ConsistencyReport has a proper Google-style docstring."""

    def test_class_has_docstring(self):
        """ConsistencyReport must have a non-empty docstring."""
        from assayer.models.consistency_report import ConsistencyReport

        assert ConsistencyReport.__doc__ is not None, "ConsistencyReport must have a docstring"
        assert ConsistencyReport.__doc__.strip() != "", (
            "ConsistencyReport docstring must not be empty"
        )

    def test_docstring_contains_args_section(self):
        """The docstring must contain an 'Args:' section (Google style)."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = ConsistencyReport.__doc__ or ""
        assert "Args:" in doc, "ConsistencyReport docstring must include an 'Args:' section"

    def test_docstring_contains_raises_section(self):
        """The docstring must contain a 'Raises:' section (Google style)."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = ConsistencyReport.__doc__ or ""
        assert "Raises:" in doc, "ConsistencyReport docstring must include a 'Raises:' section"

    def test_docstring_documents_experiment_name_field(self):
        """The docstring Args section must mention 'experiment_name'."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = ConsistencyReport.__doc__ or ""
        assert "experiment_name" in doc, (
            "ConsistencyReport docstring must document the 'experiment_name' field"
        )

    def test_docstring_documents_k_field(self):
        """The docstring Args section must mention the 'k' field."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = ConsistencyReport.__doc__ or ""
        assert "k" in doc, "ConsistencyReport docstring must document the 'k' field"

    def test_docstring_documents_per_field_field(self):
        """The docstring Args section must mention 'per_field'."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = ConsistencyReport.__doc__ or ""
        assert "per_field" in doc, "ConsistencyReport docstring must document the 'per_field' field"

    def test_docstring_documents_runs_field(self):
        """The docstring Args section must mention 'runs'."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = ConsistencyReport.__doc__ or ""
        assert "runs" in doc, "ConsistencyReport docstring must document the 'runs' field"

    def test_docstring_has_description_before_args(self):
        """The docstring must have descriptive text before the Args section."""
        from assayer.models.consistency_report import ConsistencyReport

        doc = (ConsistencyReport.__doc__ or "").strip()
        args_index = doc.find("Args:")
        assert args_index > 0, (
            "ConsistencyReport docstring must contain a description before the 'Args:' section"
        )
        description_part = doc[:args_index].strip()
        assert len(description_part) > 0, (
            "ConsistencyReport docstring must have a non-empty description before 'Args:'"
        )


class TestConsistencyReportPublicExports:
    """Verify that both models are exported from assayer.models."""

    def test_consistency_run_result_importable_from_assayer_models(self):
        """ConsistencyRunResult must be importable from assayer.models."""
        try:
            from assayer.models import ConsistencyRunResult  # noqa: F401
        except ImportError as exc:
            pytest.fail(f"Could not import ConsistencyRunResult from assayer.models: {exc}")

    def test_consistency_report_importable_from_assayer_models(self):
        """ConsistencyReport must be importable from assayer.models."""
        try:
            from assayer.models import ConsistencyReport  # noqa: F401
        except ImportError as exc:
            pytest.fail(f"Could not import ConsistencyReport from assayer.models: {exc}")

    def test_consistency_run_result_in_all(self):
        """ConsistencyRunResult must be listed in assayer.models.__all__."""
        import assayer.models as models_module

        assert hasattr(models_module, "__all__"), "assayer.models must define __all__"
        assert "ConsistencyRunResult" in models_module.__all__, (
            "ConsistencyRunResult must be listed in assayer.models.__all__"
        )

    def test_consistency_report_in_all(self):
        """ConsistencyReport must be listed in assayer.models.__all__."""
        import assayer.models as models_module

        assert hasattr(models_module, "__all__"), "assayer.models must define __all__"
        assert "ConsistencyReport" in models_module.__all__, (
            "ConsistencyReport must be listed in assayer.models.__all__"
        )

    def test_both_models_accessible_as_attributes(self):
        """Both ConsistencyRunResult and ConsistencyReport must be accessible as module attributes."""
        import assayer.models as models_module

        assert hasattr(models_module, "ConsistencyRunResult"), (
            "assayer.models must expose ConsistencyRunResult as a module attribute"
        )
        assert hasattr(models_module, "ConsistencyReport"), (
            "assayer.models must expose ConsistencyReport as a module attribute"
        )

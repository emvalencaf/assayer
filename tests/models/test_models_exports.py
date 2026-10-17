"""Tests for module isolation and __all__ exports in assayer.models module."""

import ast
import importlib
import sys
from pathlib import Path

import pytest


class TestModelsModuleIsolation:
    """Test cases for module isolation requirements from AC-SPEC-008."""

    def test_models_module_has_no_assayer_imports(self):
        """Test AC-SPEC-008: assayer/models.py does not import from any other assayer.* module."""
        # Read the models.py file content
        models_file_path = (
            Path(__file__).resolve().parents[2] / "assayer" / "models" / "__init__.py"
        )

        with open(models_file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse the AST to examine import statements
        tree = ast.parse(content, filename=str(models_file_path))

        # Collect all import statements
        assayer_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("assayer") and not alias.name.startswith(
                        "assayer.models"
                    ):
                        assayer_imports.append(f"import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if (
                    node.module
                    and node.module.startswith("assayer")
                    and not node.module.startswith("assayer.models")
                ):
                    names = [alias.name for alias in node.names]
                    assayer_imports.append(f"from {node.module} import {', '.join(names)}")

        # Assert no imports from assayer.* modules
        assert assayer_imports == [], (
            f"assayer/models.py must not import from any other assayer.* module. "
            f"Found imports: {assayer_imports}"
        )


class TestModelsExports:
    """Test cases for __all__ exports and importability."""

    def test_models_all_contains_expected_symbols(self):
        """Test that __all__ exports exactly TokenUsage, FieldEvaluation, RunResult, ExperimentResult."""
        import assayer.models

        expected_symbols = {
            "TokenUsage",
            "FieldEvaluation",
            "RunResult",
            "ExperimentResult",
            "ConsistencyFieldEvaluation",
            "ConsistencySummary",
            "ConsistencyRunResult",
            "ConsistencyReport",
        }

        # Check that __all__ exists
        assert hasattr(assayer.models, "__all__"), "assayer.models must define __all__"

        # Get actual symbols from __all__
        actual_symbols = set(assayer.models.__all__)

        # Assert exact match
        assert actual_symbols == expected_symbols, (
            f"__all__ must contain exactly {expected_symbols}. Found: {actual_symbols}"
        )

    def test_all_symbols_are_importable_from_models(self):
        """Test that all four classes are importable via 'from assayer.models import <ClassName>'."""
        expected_symbols = ["TokenUsage", "FieldEvaluation", "RunResult", "ExperimentResult"]

        # Import the models module fresh to avoid cached imports
        if "assayer.models" in sys.modules:
            importlib.reload(sys.modules["assayer.models"])

        import assayer.models

        # Test each symbol is importable and is a class
        for symbol_name in expected_symbols:
            # Check symbol exists in module
            assert hasattr(assayer.models, symbol_name), (
                f"{symbol_name} must be available in assayer.models module"
            )

            # Get the symbol
            symbol = getattr(assayer.models, symbol_name)

            # Verify it's a class (should be a dataclass)
            assert isinstance(symbol, type), f"{symbol_name} must be a class, got {type(symbol)}"

    def test_direct_import_from_models_works(self):
        """Test that direct import statements work for each class."""
        # Test individual imports work without raising ImportError
        try:
            from assayer.models import TokenUsage

            assert TokenUsage is not None
        except ImportError as e:
            pytest.fail(f"Failed to import TokenUsage: {e}")

        try:
            from assayer.models import FieldEvaluation

            assert FieldEvaluation is not None
        except ImportError as e:
            pytest.fail(f"Failed to import FieldEvaluation: {e}")

        try:
            from assayer.models import RunResult

            assert RunResult is not None
        except ImportError as e:
            pytest.fail(f"Failed to import RunResult: {e}")

        try:
            from assayer.models import ExperimentResult

            assert ExperimentResult is not None
        except ImportError as e:
            pytest.fail(f"Failed to import ExperimentResult: {e}")

    def test_all_import_from_models_works(self):
        """Test that importing all symbols at once works."""
        try:
            from assayer.models import ExperimentResult, FieldEvaluation, RunResult, TokenUsage

            # Verify all symbols are not None
            assert TokenUsage is not None
            assert FieldEvaluation is not None
            assert RunResult is not None
            assert ExperimentResult is not None

        except ImportError as e:
            pytest.fail(f"Failed to import all symbols from assayer.models: {e}")


class TestExperimentResultExists:
    """Test that ExperimentResult class exists (may not be implemented yet)."""

    def test_experiment_result_class_exists(self):
        """Test that ExperimentResult is defined in the module."""
        import assayer.models

        # This test is expected to fail initially since ExperimentResult may not exist yet
        assert hasattr(assayer.models, "ExperimentResult"), (
            "ExperimentResult class must be defined in assayer.models module"
        )

        # Verify it's a class
        experiment_result = assayer.models.ExperimentResult
        assert isinstance(experiment_result, type), (
            f"ExperimentResult must be a class, got {type(experiment_result)}"
        )

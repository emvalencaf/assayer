"""Tests for module isolation and __all__ exports in assayer.models module."""

import ast
from pathlib import Path


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
        import assayer.models

        assert set(assayer.models.__all__) == {
            "Case",
            "Comparison",
            "Dataset",
            "EvaluationFailure",
            "Experiment",
            "PricingConfig",
            "Score",
            "Step",
            "TokenUsage",
            "Trajectory",
            "add_usage",
        }

    def test_all_symbols_are_importable_from_models(self):
        import assayer.models

        for name in assayer.models.__all__:
            assert hasattr(assayer.models, name), name

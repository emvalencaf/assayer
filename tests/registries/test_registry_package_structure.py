"""
Test suite for TASK-001: Create package structure for evaluators and registries.

Tests that the required package structure exists and modules can be imported.
"""

import pathlib
import sys

import pytest


class TestRegistryPackageStructure:
    """Test package structure for evaluators and registries modules."""

    def test_assayer_evaluators_init_exists(self) -> None:
        """Test that assayer/evaluators/__init__.py exists and is a valid Python file."""
        init_path = pathlib.Path("assayer/evaluators/__init__.py")

        # Check file exists
        assert init_path.exists(), "assayer/evaluators/__init__.py must exist"

        # Check it's a file (not a directory)
        assert init_path.is_file(), "assayer/evaluators/__init__.py must be a file"

        # Check it's a valid Python file by attempting to compile it
        with open(init_path, encoding="utf-8") as f:
            content = f.read()

        try:
            compile(content, str(init_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"assayer/evaluators/__init__.py contains invalid Python syntax: {e}")

    def test_assayer_registries_init_exists(self) -> None:
        """Test that assayer/registries/__init__.py exists and is a valid Python file."""
        init_path = pathlib.Path("assayer/registries/__init__.py")

        # Check file exists
        assert init_path.exists(), "assayer/registries/__init__.py must exist"

        # Check it's a file (not a directory)
        assert init_path.is_file(), "assayer/registries/__init__.py must be a file"

        # Check it's a valid Python file by attempting to compile it
        with open(init_path, encoding="utf-8") as f:
            content = f.read()

        try:
            compile(content, str(init_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"assayer/registries/__init__.py contains invalid Python syntax: {e}")

    def test_assayer_init_exists(self) -> None:
        """Test that assayer/__init__.py exists."""
        init_path = pathlib.Path("assayer/__init__.py")

        # Check file exists
        assert init_path.exists(), "assayer/__init__.py must exist"

        # Check it's a file (not a directory)
        assert init_path.is_file(), "assayer/__init__.py must be a file"

    def test_import_assayer_evaluators_succeeds(self) -> None:
        """Test that 'import assayer.evaluators' does not raise errors."""
        try:
            # Remove from sys.modules if already imported to ensure fresh import
            if "assayer.evaluators" in sys.modules:
                del sys.modules["assayer.evaluators"]

            import assayer.evaluators  # noqa: F401

        except Exception as e:
            pytest.fail(f"Importing assayer.evaluators raised an error: {type(e).__name__}: {e}")

    def test_import_assayer_registries_succeeds(self) -> None:
        """Test that 'import assayer.registries' does not raise errors."""
        try:
            # Remove from sys.modules if already imported to ensure fresh import
            if "assayer.registries" in sys.modules:
                del sys.modules["assayer.registries"]

            import assayer.registries  # noqa: F401

        except Exception as e:
            pytest.fail(f"Importing assayer.registries raised an error: {type(e).__name__}: {e}")

    def test_evaluators_directory_exists(self) -> None:
        """Test that the evaluators directory exists."""
        evaluators_dir = pathlib.Path("assayer/evaluators")

        assert evaluators_dir.exists(), "assayer/evaluators directory must exist"
        assert evaluators_dir.is_dir(), "assayer/evaluators must be a directory"

    def test_registries_directory_exists(self) -> None:
        """Test that the registries directory exists."""
        registries_dir = pathlib.Path("assayer/registries")

        assert registries_dir.exists(), "assayer/registries directory must exist"
        assert registries_dir.is_dir(), "assayer/registries must be a directory"

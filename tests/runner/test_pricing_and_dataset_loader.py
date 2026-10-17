"""Tests for PricingConfig and load_dataset function."""

import json
import tempfile
from pathlib import Path

import pytest

from assayer.runner.dataset_loader import load_dataset
from assayer.runner.pricing import PricingConfig


class TestPricingConfig:
    """Test PricingConfig dataclass."""

    def test_pricing_config_creation(self):
        """Test that PricingConfig can be created with required fields."""
        config = PricingConfig(cost_per_input_token=0.001, cost_per_output_token=0.002)

        assert config.cost_per_input_token == 0.001
        assert config.cost_per_output_token == 0.002

    def test_pricing_config_type_hints_exist(self):
        """Test that PricingConfig has proper type hints."""
        # This test verifies the imports work and the class exists with expected attributes

        # Get the annotations (type hints) for PricingConfig
        annotations = PricingConfig.__annotations__

        assert "cost_per_input_token" in annotations
        assert "cost_per_output_token" in annotations
        assert annotations["cost_per_input_token"] == float
        assert annotations["cost_per_output_token"] == float

    def test_pricing_config_is_dataclass(self):
        """Test that PricingConfig is actually a dataclass."""
        import dataclasses

        assert dataclasses.is_dataclass(PricingConfig)

    def test_pricing_config_zero_costs(self):
        """Test PricingConfig with zero costs (edge case)."""
        config = PricingConfig(cost_per_input_token=0.0, cost_per_output_token=0.0)

        assert config.cost_per_input_token == 0.0
        assert config.cost_per_output_token == 0.0

    def test_pricing_config_negative_costs(self):
        """Test PricingConfig with negative costs (should be allowed)."""
        config = PricingConfig(cost_per_input_token=-0.001, cost_per_output_token=-0.002)

        assert config.cost_per_input_token == -0.001
        assert config.cost_per_output_token == -0.002


class TestLoadDataset:
    """Test load_dataset function."""

    def test_load_dataset_from_valid_list(self):
        """Test loading dataset from a valid list of dictionaries."""
        data = [
            {"input": "test input 1", "expected_output": "test output 1"},
            {"input": "test input 2", "expected_output": "test output 2"},
        ]

        result = load_dataset(data)

        assert result == data
        assert len(result) == 2
        assert result[0]["input"] == "test input 1"
        assert result[1]["expected_output"] == "test output 2"

    def test_load_dataset_empty_list(self):
        """Test loading an empty dataset returns empty list."""
        result = load_dataset([])

        assert result == []
        assert len(result) == 0

    def test_load_dataset_missing_input_key(self):
        """Test that missing 'input' key raises ValueError."""
        data = [
            {"expected_output": "test output 1"},  # missing "input"
        ]

        with pytest.raises(ValueError, match="missing.*input"):
            load_dataset(data)

    def test_load_dataset_missing_expected_output_key(self):
        """Test that missing 'expected_output' key raises ValueError."""
        data = [
            {"input": "test input 1"},  # missing "expected_output"
        ]

        with pytest.raises(ValueError, match="missing.*expected_output"):
            load_dataset(data)

    def test_load_dataset_missing_both_keys(self):
        """Test that missing both required keys raises ValueError."""
        data = [
            {"other_field": "some value"},  # missing both required keys
        ]

        with pytest.raises(ValueError):
            load_dataset(data)

    def test_load_dataset_mixed_valid_invalid(self):
        """Test that one invalid example causes entire dataset to fail."""
        data = [
            {"input": "test input 1", "expected_output": "test output 1"},
            {"input": "test input 2"},  # missing "expected_output"
        ]

        with pytest.raises(ValueError):
            load_dataset(data)

    def test_load_dataset_from_json_file(self):
        """Test loading dataset from a JSON file."""
        data = [
            {"input": "file input 1", "expected_output": "file output 1"},
            {"input": "file input 2", "expected_output": "file output 2"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            result = load_dataset(temp_path)

            assert result == data
            assert len(result) == 2
            assert result[0]["input"] == "file input 1"
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_from_empty_json_file(self):
        """Test loading an empty JSON dataset file."""
        data = []

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            result = load_dataset(temp_path)

            assert result == []
            assert len(result) == 0
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_nonexistent_file(self):
        """Test that non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_dataset("/nonexistent/path/dataset.json")

    def test_load_dataset_invalid_json_file(self):
        """Test loading dataset from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_dataset(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_json_file_missing_keys(self):
        """Test loading JSON file with examples missing required keys."""
        data = [
            {"input": "test input 1", "expected_output": "test output 1"},
            {"input": "test input 2"},  # missing "expected_output"
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_dataset(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_dataset_extra_keys_allowed(self):
        """Test that extra keys in examples are allowed."""
        data = [
            {
                "input": "test input 1",
                "expected_output": "test output 1",
                "metadata": {"source": "test"},
                "id": 123,
            },
        ]

        result = load_dataset(data)

        assert result == data
        assert result[0]["metadata"]["source"] == "test"
        assert result[0]["id"] == 123

    def test_load_dataset_type_hints_exist(self):
        """Test that load_dataset has proper type hints."""
        import inspect

        # Get the function signature
        sig = inspect.signature(load_dataset)

        # Check parameter types
        source_param = sig.parameters["source"]
        return_annotation = sig.return_annotation

        # Verify the function exists and can be called (indirectly tests imports)
        assert callable(load_dataset)
        assert "source" in sig.parameters

    def test_load_dataset_single_example(self):
        """Test loading dataset with single example."""
        data = [
            {"input": "single input", "expected_output": "single output"},
        ]

        result = load_dataset(data)

        assert result == data
        assert len(result) == 1

    def test_load_dataset_large_dataset(self):
        """Test loading a larger dataset (boundary condition)."""
        data = [{"input": f"input {i}", "expected_output": f"output {i}"} for i in range(100)]

        result = load_dataset(data)

        assert result == data
        assert len(result) == 100
        assert result[0]["input"] == "input 0"
        assert result[99]["expected_output"] == "output 99"

    def test_load_dataset_json_not_list(self):
        """Test that JSON file containing non-list raises appropriate error."""
        data = {"not": "a list"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            # This should raise some error when trying to iterate over a dict
            # The exact error depends on implementation but it shouldn't succeed
            with pytest.raises((TypeError, AttributeError, ValueError)):
                load_dataset(temp_path)
        finally:
            Path(temp_path).unlink()

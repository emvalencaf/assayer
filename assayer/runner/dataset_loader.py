"""Dataset loading utilities for evaluation pipelines."""

import json


def load_dataset(source: list[dict] | str) -> list[dict]:
    """Load and validate a dataset from a list of dictionaries or JSON file.

    This function accepts either a list of dictionaries directly or a path to a
    JSON file containing such a list. All examples in the dataset must contain
    both "input" and "expected_output" keys.

    Args:
        source: Either a list of dictionaries representing the dataset, or a
            string path to a JSON file containing the dataset.

    Returns:
        A validated list of dictionaries, where each dictionary contains at
        minimum the keys "input" and "expected_output".

    Raises:
        ValueError: If any example in the dataset is missing the required
            "input" or "expected_output" keys.
        FileNotFoundError: If the provided file path does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        TypeError: If the JSON file contains data that is not a list.
    """
    # If source is a string, treat it as a file path
    if isinstance(source, str):
        try:
            with open(source, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Dataset file not found: {source}") from None
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in file: {source}", e.doc, e.pos) from e

        # Ensure the loaded data is a list
        if not isinstance(data, list):
            raise TypeError(f"JSON file must contain a list, got {type(data).__name__}")
    else:
        # Source is already a list
        data = source

    # Validate that each example has the required keys
    for i, example in enumerate(data):
        if not isinstance(example, dict):
            raise ValueError(f"Example {i} must be a dictionary, got {type(example).__name__}")

        if "input" not in example:
            raise ValueError(f"Example {i} is missing required key: 'input'")

        if "expected_output" not in example:
            raise ValueError(f"Example {i} is missing required key: 'expected_output'")

    return data

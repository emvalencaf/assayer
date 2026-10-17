"""Loading a Dataset of Cases, validated against what the chosen metrics require."""

import json
from collections.abc import Iterable
from dataclasses import fields
from pathlib import Path

from assayer.metrics import Metric
from assayer.models import Case, Dataset

_CASE_FIELDS = {f.name for f in fields(Case)}


def load_cases(source: list[dict] | str, metrics: Iterable[Metric] = ()) -> Dataset:
    """Build a Dataset from a list of dictionaries or a JSON file.

    Only `input` and the Case fields that the metrics declare in `requires` are
    mandatory; every other field may be absent.

    Args:
        source: A list of dictionaries, or the path to a JSON file holding one.
            A Dataset loaded from a file is named after the file.
        metrics: The metrics the Dataset will be scored with.

    Returns:
        The Dataset.

    Raises:
        FileNotFoundError: If the path does not exist.
        TypeError: If the JSON file does not hold a list.
        ValueError: If an entry is not a dictionary, has an unknown key, or lacks
            `input` or a field required by a metric.
    """
    name = "dataset"
    if isinstance(source, str):
        name = Path(source).stem
        try:
            with open(source, encoding="utf-8") as f:
                entries = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Dataset file not found: {source}") from None
        if not isinstance(entries, list):
            raise TypeError(f"JSON file must contain a list, got {type(entries).__name__}")
    else:
        entries = source

    required = {"input"} | {r for m in metrics for r in m.requires if r in _CASE_FIELDS}
    cases = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(f"Case {i} must be a dictionary, got {type(entry).__name__}")
        unknown = set(entry) - _CASE_FIELDS
        if unknown:
            raise ValueError(f"Case {i} has unknown keys: {sorted(unknown)}")
        for key in sorted(required):
            if entry.get(key) is None:
                raise ValueError(f"Case {i} is missing required key: '{key}'")
        cases.append(Case(**entry))
    return Dataset(name=name, cases=cases)

---
id: TASK-001
spec: runner
status: done
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement PricingConfig and dataset loader

## What to do
Create the runner package structure and implement:
- `assayer/runner/pricing.py` — `PricingConfig` dataclass
- `assayer/runner/dataset_loader.py` — `load_dataset(source: list[dict] | str) -> list[dict]`

Dataset loader must validate that each example has `"input"` and `"expected_output"` keys, and support loading from a JSON file path.

## Acceptance Criteria
- [x] `PricingConfig` is a dataclass with `cost_per_input_token: float` and `cost_per_output_token: float`
- [x] `load_dataset` accepts a list of dicts and returns it validated
- [x] `load_dataset` accepts a `.json` file path and loads it
- [x] Raises `ValueError` if any example is missing `"input"` or `"expected_output"`
- [x] Raises `FileNotFoundError` for a non-existent file path
- [x] Google-style docstrings and full type hints

## Dependencies
- none

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/runner/test_pricing_and_dataset_loader.py`

Comprehensive tests covering:
- `PricingConfig` dataclass creation, type hints, and edge cases (zero/negative costs)  
- `load_dataset()` with valid list input and empty list
- `load_dataset()` with JSON file path (valid, empty, non-existent)
- Validation errors for missing "input" or "expected_output" keys
- Edge cases: invalid JSON, non-list JSON, extra keys allowed, large datasets

## Implementation Notes

## Commit
Hash:

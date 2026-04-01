---
id: TASK-001
spec: runner
status: pending
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
- [ ] `PricingConfig` is a dataclass with `cost_per_input_token: float` and `cost_per_output_token: float`
- [ ] `load_dataset` accepts a list of dicts and returns it validated
- [ ] `load_dataset` accepts a `.json` file path and loads it
- [ ] Raises `ValueError` if any example is missing `"input"` or `"expected_output"`
- [ ] Raises `FileNotFoundError` for a non-existent file path
- [ ] Google-style docstrings and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

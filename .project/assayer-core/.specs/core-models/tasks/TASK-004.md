---
id: TASK-004
spec: core-models
status: done
depends-on: [TASK-003]
created: 2026-03-30
---

# TASK-004: Implement ExperimentResult dataclass with compare stub

## What to do

Add the `ExperimentResult` dataclass to `assayer/models.py`.

Fields:
- `experiment_name: str` -- human-readable experiment name. Must be non-empty and non-whitespace-only.
- `runs: list[RunResult]` (default: empty list via `field(default_factory=list)`)

Methods:
- `compare(self, other: ExperimentResult) -> dict` -- raises `NotImplementedError("compare() is implemented in the runner spec")`.

Add a `__post_init__` method that raises `ValueError` when `experiment_name` is empty or whitespace-only (after `.strip()`).

Include Google-style docstrings and full type hints.

## Acceptance Criteria

- AC-SPEC-006: `ExperimentResult` holds `experiment_name` and a list of `RunResult`; raises `ValueError` when `experiment_name` is empty.
- AC-SPEC-007: `ExperimentResult.compare(other)` raises `NotImplementedError`.
- `ExperimentResult` with an empty `runs` list is valid.
- Whitespace-only `experiment_name` raises `ValueError`.

## Dependencies

- TASK-003 (`RunResult` must exist).

## Tests

Test file: `tests/test_models_experiment_result.py`

Comprehensive test coverage for ExperimentResult class including:
- Construction with valid experiment names and run lists
- Default empty runs list behavior
- Validation of empty/whitespace-only experiment names
- compare() method raising NotImplementedError
- Edge cases with multiple runs and special characters

## Implementation Notes

Successfully implemented the `ExperimentResult` dataclass with the following characteristics:

- **Location**: Appended to `assayer/models.py` after the `RunResult` class
- **Fields**:
  - `experiment_name: str` - validated to not be empty or whitespace-only
  - `runs: list[RunResult]` - defaults to empty list using `field(default_factory=list)`
- **Validation**: `__post_init__` method raises `ValueError` when `experiment_name.strip()` is empty
- **Compare method**: Raises `NotImplementedError("compare() is implemented in the runner spec")` as specified
- **Documentation**: Full Google-style docstrings with Args, Returns, Raises sections
- **Type hints**: Complete type annotations including forward reference for compare method parameter
- **Exports**: Added `ExperimentResult` to module `__all__` list to satisfy export tests

All 55 tests pass, including 13 specific tests for `ExperimentResult` covering:
- Valid construction scenarios
- Default runs behavior
- Validation of empty/whitespace experiment names
- Compare method NotImplementedError
- Edge cases with multiple runs and special characters


## Commit

Hash: 051ce5b

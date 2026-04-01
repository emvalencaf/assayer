---
id: TASK-001
spec: core-models
status: done
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement TokenUsage dataclass with validation

## What to do

Create the file `assayer/models.py` and implement the `TokenUsage` dataclass.

Fields:
- `input_tokens: int`
- `output_tokens: int`
- `cost_usd: float | None`

Add a `__post_init__` method that raises `ValueError` when:
- `input_tokens < 0`
- `output_tokens < 0`
- `cost_usd` is not `None` and `cost_usd < 0`

Include Google-style docstrings and full type hints.

This task also creates the module file with its module-level docstring. Subsequent tasks append to this file.

## Acceptance Criteria

- AC-SPEC-001: `TokenUsage` can be instantiated with valid values; attributes return provided values.
- AC-SPEC-002: `TokenUsage.__post_init__` raises `ValueError` for negative `input_tokens`, negative `output_tokens`, or negative `cost_usd`.
- `TokenUsage(input_tokens=0, output_tokens=0, cost_usd=None)` succeeds.
- `TokenUsage(input_tokens=0, output_tokens=0, cost_usd=0.0)` succeeds.

## Dependencies

None.

## Tests

Test file: `tests/test_models_token_usage.py`

Comprehensive test suite covering:
- Valid instantiation with all acceptance criteria (AC-SPEC-001, AC-SPEC-002)
- Edge cases: zero tokens, None cost_usd, zero cost_usd
- Validation errors for negative values
- Boundary conditions with large values and fractional costs

All tests confirmed to fail without implementation (ModuleNotFoundError: No module named 'assayer').

## Implementation Notes

Created `/home/emvalenca/personal_projects/assayer/assayer/models.py` with the `TokenUsage` dataclass implementing:

- Fields: `input_tokens: int`, `output_tokens: int`, `cost_usd: Union[float, None]`
- Full type hints using `Union[float, None]` for Python 3.11 compatibility
- Google-style docstrings for the class and `__post_init__` method
- Validation in `__post_init__` that raises `ValueError` with descriptive messages for:
  - Negative input_tokens
  - Negative output_tokens
  - Negative cost_usd (when not None)
- Module-level docstring describing the purpose of the models module

Also created `/home/emvalenca/personal_projects/assayer/assayer/__init__.py` to establish the package structure.

All 10 tests in `tests/test_models_token_usage.py` pass, covering all acceptance criteria and edge cases including:
- Valid instantiation with various value combinations
- Proper validation of negative values
- Support for None cost_usd and zero values
- Large token counts and fractional costs



## Commit

Hash: e88083e

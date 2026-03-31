---
id: TASK-002
spec: core-models
status: done
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-002: Implement FieldEvaluation dataclass with validation

## What to do

Add the `FieldEvaluation` dataclass to `assayer/models.py`.

Fields:
- `field_name: str`
- `evaluator_method: str`
- `expected_value: Any`
- `obtained_value: Any`
- `score: float`
- `prompt_hash: str | None`
- `metadata: dict` (default: empty dict via `field(default_factory=dict)`)

Add a `__post_init__` method that raises `ValueError` when:
- `field_name` is empty or whitespace-only (after `.strip()`)
- `evaluator_method` is empty or whitespace-only (after `.strip()`)
- `score < 0.0` or `score > 1.0`

Include Google-style docstrings and full type hints.

## Acceptance Criteria

- AC-SPEC-003: `FieldEvaluation` can be instantiated with all seven fields; `metadata` defaults to empty dict.
- AC-SPEC-004: Raises `ValueError` for empty `field_name`, empty `evaluator_method`, or `score` outside [0.0, 1.0].
- Boundary values `score=0.0` and `score=1.0` are accepted.
- `expected_value=None` is accepted.
- `prompt_hash=None` is accepted.
- Whitespace-only `field_name` raises `ValueError`.

## Dependencies

- TASK-001 (module file must exist).

## Tests

Test file: `tests/test_models_field_evaluation.py`

Comprehensive tests covering:
- Valid instantiation with all seven fields (AC-SPEC-003)
- Default metadata behavior (empty dict when not provided)
- Validation logic in __post_init__ method (AC-SPEC-004)
- Boundary values: score=0.0 and score=1.0 are valid
- Edge cases: expected_value=None and prompt_hash=None are valid
- Error cases: empty/whitespace-only field_name and evaluator_method raise ValueError
- Error cases: score outside [0.0, 1.0] range raises ValueError
- Data type flexibility for expected_value and obtained_value (Any type)
- Metadata mutability after instantiation

All tests confirmed to fail (red) - FieldEvaluation class not yet implemented.

## Implementation Notes

- Added the `FieldEvaluation` dataclass to `assayer/models.py` following the existing pattern from `TokenUsage`.
- Used Google-style docstrings with comprehensive parameter descriptions, return types, and exception documentation.
- Added full type hints using `Union[str, None]` for `prompt_hash` to match the existing code style in the module.
- Implemented `__post_init__` validation that:
  - Checks both empty strings and whitespace-only strings using `not string or not string.strip()`
  - Validates score range [0.0, 1.0] with inclusive bounds
  - Provides clear error messages matching the test expectations
- Used `field(default_factory=dict)` for metadata to provide mutable default while avoiding shared mutable defaults
- The dataclass is not frozen (default `frozen=False`) to allow incremental population as required by the spec
- Added required imports: `field` from dataclasses and `Any` from typing



## Commit

Hash:

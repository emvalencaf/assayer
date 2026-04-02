---
id: TASK-001
spec: ner-evaluator
status: done
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement EntitySpan dataclass

## What to do
Create `assayer/evaluators/ner.py` and implement the `EntitySpan` frozen dataclass as specified in `design.md`. Validate `text`, `entity_type`, `start >= 0`, and `end > start` in `__post_init__`.

## Acceptance Criteria
- [x] `EntitySpan` is hashable (frozen=True)
- [x] Raises `ValueError` for empty text, empty entity_type, negative start, or end <= start
- [x] Two spans with identical fields compare equal and hash equally
- [x] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_ner.py`
- Comprehensive test coverage for `EntitySpan` dataclass
- Tests for hashability, immutability (frozen=True), equality, and validation
- Edge case coverage for empty/whitespace inputs, boundary values, unicode text
- All 18 test cases currently fail with `ModuleNotFoundError` (expected - no implementation yet)

## Implementation Notes

Implemented `EntitySpan` as a frozen dataclass in `/home/emvalenca/personal_projects/assayer/assayer/evaluators/ner.py`:

- Used `@dataclass(frozen=True)` for immutability and hashability
- Implemented validation in `__post_init__()` method to check:
  - Text and entity_type are not empty or whitespace-only (using `.strip()`)
  - Start position is >= 0
  - End position is > start position
- Added comprehensive Google-style docstring with examples
- All validation error messages match the exact strings expected by tests
- Supports Unicode text and large index values as required by test cases

All 18 test cases pass, confirming the implementation meets all acceptance criteria.

## Commit
Hash: b1f2575

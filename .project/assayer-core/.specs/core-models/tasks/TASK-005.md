---
id: TASK-005
spec: core-models
status: done
depends-on: [TASK-004]
created: 2026-03-30
---

# TASK-005: Verify module isolation and add __all__ exports

## What to do

Add an `__all__` list to `assayer/models.py` exporting exactly: `TokenUsage`, `FieldEvaluation`, `RunResult`, `ExperimentResult`.

Write a dedicated test that:
1. Verifies `assayer/models.py` contains no imports from any `assayer.*` submodule (parse the file's import statements).
2. Verifies `__all__` contains exactly the four expected symbols.
3. Verifies each symbol in `__all__` is importable from `assayer.models`.

This task ensures the module remains a leaf dependency with no coupling to the rest of the codebase.

## Acceptance Criteria

- AC-SPEC-008: `assayer/models.py` does not import from any other `assayer.*` module.
- `__all__` exports exactly `TokenUsage`, `FieldEvaluation`, `RunResult`, `ExperimentResult`.
- All four classes are importable via `from assayer.models import <ClassName>`.

## Dependencies

- TASK-004 (all models must exist).

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_models_exports.py`

Tests verify:
1. Module isolation - no imports from other assayer modules (AC-SPEC-008)
2. __all__ list contains exactly the four expected symbols
3. All four classes (TokenUsage, FieldEvaluation, RunResult, ExperimentResult) are importable
4. Individual and bulk imports work properly

## Implementation Notes

The implementation was already complete from TASK-004. The `assayer/models.py` module already contained:

1. **Proper `__all__` list**: Line 10 exports exactly the four required symbols: `["TokenUsage", "FieldEvaluation", "RunResult", "ExperimentResult"]`

2. **Module isolation (AC-SPEC-008)**: The module only imports from standard library modules (`dataclasses` from line 7, `typing` from line 8). No imports from any `assayer.*` submodules.

3. **All classes implemented**: All four required classes (`TokenUsage`, `FieldEvaluation`, `RunResult`, `ExperimentResult`) are properly defined as dataclasses with full validation and docstrings.

The tests confirm all acceptance criteria are met:
- Module isolation verification passes
- `__all__` contains exactly the expected symbols
- All four classes are importable individually and collectively
- No regressions in the full test suite (55/55 tests pass)


## Commit

Hash:

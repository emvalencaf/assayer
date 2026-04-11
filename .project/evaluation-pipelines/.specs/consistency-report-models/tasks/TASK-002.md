---
id: SPEC-001-TASK-002
spec: consistency-report-models
spec-id: SPEC-001
status: done
depends-on: ["SPEC-001-TASK-001"]
created: 2026-04-09
---

# SPEC-001-TASK-002: Define ConsistencyReport dataclass and export both models

## What to do

Create `assayer/models/consistency_report.py` containing the
`ConsistencyReport` dataclass.

Fields:
- `experiment_name: str` -- human-readable experiment name
- `k: int` -- number of repetitions per input
- `per_field: dict[str, ConsistencySummary]` -- one summary per declared
  field, keyed by field name
- `runs: list[ConsistencyRunResult]` -- one entry per dataset input

`__post_init__` validation:
- Raise `ValueError` if `experiment_name` is empty or whitespace-only
- Raise `ValueError` if `k < 1`

The class must have a Google-style docstring (description, Args, Raises)
and full type hints.

After creating the file, update `assayer/models/__init__.py`:
- Import `ConsistencyRunResult` from `assayer.models.consistency_run_result`
- Import `ConsistencyReport` from `assayer.models.consistency_report`
- Add both to `__all__`

## Acceptance Criteria

- [ ] `ConsistencyReport` is a `@dataclass` in
  `assayer/models/consistency_report.py`
- [ ] It has fields `experiment_name: str`, `k: int`,
  `per_field: dict[str, ConsistencySummary]`,
  `runs: list[ConsistencyRunResult]`
- [ ] `__post_init__` raises `ValueError` for empty/whitespace
  `experiment_name`
- [ ] `__post_init__` raises `ValueError` for `k < 1`
- [ ] Google-style docstring with description, Args, and Raises sections
- [ ] Both `ConsistencyRunResult` and `ConsistencyReport` are importable
  from `assayer.models`
- [ ] Both are listed in `assayer.models.__all__`

## Dependencies

- SPEC-001-TASK-001 (ConsistencyRunResult must exist first)

## Tests

Test file: `tests/models/test_consistency_report.py`

40 tests across 5 test classes:
- `TestConsistencyReportIsDataclass` — verifies the module is importable and the class is a proper `@dataclass`
- `TestConsistencyReportFields` — verifies presence and type hints of all four fields (`experiment_name`, `k`, `per_field`, `runs`), including generic type parameters for `dict` and `list`
- `TestConsistencyReportInstantiation` — verifies correct instantiation with valid inputs, including boundary value `k=1` and multiple entries in `per_field` and `runs`
- `TestConsistencyReportValidation` — verifies `__post_init__` raises `ValueError` for empty/whitespace `experiment_name` (including tabs, newlines) and for `k < 1` (zero and negative); also verifies a name with embedded spaces is accepted
- `TestConsistencyReportDocstring` — verifies presence of Google-style docstring with description, `Args:`, and `Raises:` sections mentioning all four fields
- `TestConsistencyReportPublicExports` — verifies both `ConsistencyRunResult` and `ConsistencyReport` are importable from `assayer.models` and listed in `__all__`

## Implementation Notes

- Created `assayer/models/consistency_report.py` with `ConsistencyReport` as a `@dataclass`.
- Fields: `experiment_name: str`, `k: int`, `per_field: dict[str, ConsistencySummary]`, `runs: list[ConsistencyRunResult]`.
- `__post_init__` raises `ValueError` if `experiment_name.strip()` is falsy (empty or whitespace-only).
- `__post_init__` raises `ValueError` if `k < 1`.
- Google-style docstring includes description, `Args:`, and `Raises:` sections documenting all four fields.
- `assayer/models/__init__.py` was updated to import and export both `ConsistencyRunResult` and `ConsistencyReport` in `__all__`.
- `tests/test_models_exports.py` was updated to include `ConsistencyRunResult` and `ConsistencyReport` in `expected_symbols`, resolving the previous blocking conflict.
- All 46 tests across both test files pass.

## Commit

Hash:

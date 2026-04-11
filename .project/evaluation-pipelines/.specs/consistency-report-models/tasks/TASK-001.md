---
id: SPEC-001-TASK-001
spec: consistency-report-models
spec-id: SPEC-001
status: done
depends-on: []
created: 2026-04-09
---

# SPEC-001-TASK-001: Define ConsistencyRunResult dataclass

## What to do

Create `assayer/models/consistency_run_result.py` containing the
`ConsistencyRunResult` dataclass.

Fields:
- `input: Any` -- the dataset input that was evaluated
- `per_field_evaluations: dict[str, ConsistencyFieldEvaluation]` -- keyed
  by field name

The class must have a Google-style docstring describing its purpose, all
fields (Args section), and full type hints. No `__post_init__` validation
is needed for this dataclass.

## Acceptance Criteria

- [ ] `ConsistencyRunResult` is a `@dataclass` in
  `assayer/models/consistency_run_result.py`
- [ ] It has fields `input: Any` and
  `per_field_evaluations: dict[str, ConsistencyFieldEvaluation]`
- [ ] It has a Google-style docstring with description and Args section
- [ ] All fields have type hints

## Dependencies

- none

## Tests

Test file: `tests/models/test_consistency_run_result.py`

21 tests across four classes:
- `TestConsistencyRunResultIsDataclass` — confirms the module is importable, the class exists, and is decorated with `@dataclass`
- `TestConsistencyRunResultFields` — verifies the `input: Any` and `per_field_evaluations: dict[str, ConsistencyFieldEvaluation]` fields and their type hints, and that no extra fields are present
- `TestConsistencyRunResultInstantiation` — exercises construction with a variety of `input` types (str, dict, None, int, list, arbitrary object) and with single/multiple `per_field_evaluations` entries
- `TestConsistencyRunResultDocstring` — asserts a non-empty docstring exists, that it contains an `Args:` section (Google style), and that both fields are documented with a description before `Args:`

## Implementation Notes

Created `assayer/models/consistency_run_result.py` with the `ConsistencyRunResult` dataclass.
- Imported `ConsistencyFieldEvaluation` from `assayer.models.consistency_field_evaluation` (its canonical module path).
- Used `typing.Any` for the `input` field annotation so that `get_type_hints()` resolves to the `Any` sentinel, which the tests verify with `hints["input"] is Any`.
- No `__post_init__` or default values were added — the dataclass is a plain value container as specified.

## Commit

Hash:

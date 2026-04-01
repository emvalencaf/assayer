---
id: TASK-003
spec: runner
status: pending
depends-on: []
created: 2026-03-30
---

# TASK-003: Implement FieldRouter

## What to do
Create `assayer/runner/field_router.py` and implement `FieldRouter` as specified in `design.md`.

- Eagerly validates all evaluator names against the registry at construction time (raises `KeyError` before any execution)
- `route(output, expected_output) -> list[FieldEvaluation]` handles both scalar and dict-structured outputs

## Acceptance Criteria
- [ ] Constructor raises `KeyError` if any evaluator name is not in the registry
- [ ] `route()` returns one `FieldEvaluation` per (field, evaluator) pair
- [ ] Handles scalar output (non-dict) by using the full value as the field value
- [ ] Handles dict-structured output by extracting the field by key
- [ ] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

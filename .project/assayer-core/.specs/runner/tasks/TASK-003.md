---
id: TASK-003
spec: runner
status: done
depends-on: []
created: 2026-03-30
---

# TASK-003: Implement FieldRouter

## What to do
Create `assayer/runner/field_router.py` and implement `FieldRouter` as specified in `design.md`.

- Eagerly validates all evaluator names against the registry at construction time (raises `KeyError` before any execution)
- `route(output, expected_output) -> list[FieldEvaluation]` handles both scalar and dict-structured outputs

## Acceptance Criteria
- [x] Constructor raises `KeyError` if any evaluator name is not in the registry
- [x] `route()` returns one `FieldEvaluation` per (field, evaluator) pair
- [x] Handles scalar output (non-dict) by using the full value as the field value
- [x] Handles dict-structured output by extracting the field by key
- [x] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/runner/test_field_router.py`

Comprehensive test suite covering:
- Constructor validation of evaluator names against registry
- Proper instantiation of evaluators with field_name parameter
- Route method handling of dict-structured outputs (field extraction)
- Route method handling of scalar outputs (full value usage)
- Multiple evaluators per field
- Mixed output types (dict/scalar combinations)
- Edge cases (None values, missing fields, empty configurations)
- One FieldEvaluation per (field, evaluator) pair requirement

## Implementation Notes

Implemented FieldRouter class following the design specification:

1. **Constructor validation**: Eagerly validates all evaluator names against the registry at construction time using a list comprehension that calls `evaluator_registry.get(n)` for each name, which raises `KeyError` if the evaluator is not registered.

2. **Evaluator instantiation**: Creates evaluator instances with both the evaluator name (as required by BaseEvaluator) and the field_name as a keyword argument: `evaluator_registry.get(n)(n, field_name=field)`.

3. **Route method**: Handles both scalar and dict-structured outputs by checking `isinstance(output, dict)` and extracting field values accordingly. Returns a flat list of FieldEvaluation objects.

4. **Error handling**: Missing fields in dict-structured inputs naturally raise `KeyError` when accessing `output[field]`.

Key design decisions:
- Used dictionary comprehension for clean, readable route mapping
- Relied on Python's natural `KeyError` behavior for missing dict keys
- Followed the exact evaluator instantiation pattern from the design spec

## Commit
Hash: 5003f30

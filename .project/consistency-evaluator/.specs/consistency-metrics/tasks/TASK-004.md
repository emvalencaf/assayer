---
id: TASK-004
spec: consistency-metrics
status: done
depends-on: [TASK-003]
created: 2026-04-07
---

# TASK-004: Implement compute_recall_at_k

## What to do

In `assayer/evaluators/consistency_metrics.py`, implement:

**`compute_recall_at_k(results: list[FieldEvaluation], reference: Any) -> float`**

Multi-label path (when any `obtained_value` is a `list` or `set`):
- `ref_set = set(reference)`
- `union_predicted = set().union(*[set(r.obtained_value) for r in results])`
- Return `len(union_predicted & ref_set) / len(ref_set)`
- Return `0.0` (not raise) when `ref_set` is empty

Single-label path (when all `obtained_value` are `str`):
- `ref_set = {str(reference)}`
- `union_predicted = {str(r.obtained_value) for r in results}`
- Return `1.0` if `ref_set & union_predicted` else `0.0` (equivalent to `pass_at_k`)

Return `0.0` for empty `results` list.

Add to `__all__`.

## Acceptance Criteria

- [x] `compute_recall_at_k` returns `1.0` when the union of all predicted label sets covers all reference labels.
- [x] `compute_recall_at_k` returns `0.0` when no predicted label appears in the reference set.
- [x] `compute_recall_at_k` returns `0.0` when `reference` is an empty list, without raising.
- [x] For single-label inputs, returns `1.0` if `pass_at_k` is `True` and `0.0` otherwise.
- [x] Returns `0.0` for empty `results` list without raising.
- [x] Function carries Google-style docstring and full type hints.

## Dependencies

- TASK-003

## Tests

Test file: `tests/evaluators/test_consistency_metrics.py` - Added `TestComputeRecallAtK` class with 18 comprehensive tests covering all acceptance criteria: multi-label full/partial coverage, empty reference handling, single-label equivalence to pass@k, empty results, mixed types, edge cases with sets/lists, string conversion, and mode detection.

## Implementation Notes

Implemented `compute_recall_at_k` in `assayer/evaluators/consistency_metrics.py` following the specification:

1. **Type Detection**: Automatically detects multi-label mode if any `obtained_value` in results is a `list` or `set`, otherwise uses single-label mode.

2. **Multi-label Path**: 
   - Converts reference to a set and checks if empty (returns 0.0 if so)
   - Creates union of all predicted sets using `set().union(*[set(r.obtained_value) for r in results])`
   - Returns `len(intersection) / len(reference_set)` as recall fraction
   - Handles non-iterable obtained_values gracefully by skipping them

3. **Single-label Path**: 
   - Converts reference to `{str(reference)}` and all obtained_values to strings
   - Returns 1.0 if reference string appears in union of predicted strings, 0.0 otherwise
   - This is equivalent to `pass_at_k` behavior for single-label scenarios

4. **Edge Cases**: 
   - Empty results list returns 0.0
   - Empty reference (multi-label) returns 0.0 without raising ZeroDivisionError
   - Non-iterable references/values handled with try/except blocks

5. **Added to `__all__` exports and includes comprehensive Google-style docstring with examples for both single-label and multi-label modes.

All 18 test cases pass, covering full coverage, partial coverage, empty references, single vs multi-label modes, mixed types, and edge cases.

## Commit

Hash:

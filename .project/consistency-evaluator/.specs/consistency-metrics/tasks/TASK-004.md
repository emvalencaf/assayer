---
id: TASK-004
spec: consistency-metrics
status: pending
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

- [ ] `compute_recall_at_k` returns `1.0` when the union of all predicted label sets covers all reference labels.
- [ ] `compute_recall_at_k` returns `0.0` when no predicted label appears in the reference set.
- [ ] `compute_recall_at_k` returns `0.0` when `reference` is an empty list, without raising.
- [ ] For single-label inputs, returns `1.0` if `pass_at_k` is `True` and `0.0` otherwise.
- [ ] Returns `0.0` for empty `results` list without raising.
- [ ] Function carries Google-style docstring and full type hints.

## Dependencies

- TASK-003

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

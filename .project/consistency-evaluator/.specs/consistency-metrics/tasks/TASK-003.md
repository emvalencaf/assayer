---
id: TASK-003
spec: consistency-metrics
status: pending
depends-on: [TASK-001]
created: 2026-04-07
---

# TASK-003: Implement compute_correct_rate and compute_pass_at_k

## What to do

In `assayer/evaluators/consistency_metrics.py`, implement:

**`compute_correct_rate(results: list[FieldEvaluation], reference: Any) -> float`**
- If any `r.obtained_value` is a `list` or `set` → multi-label path: compare `set(r.obtained_value) == set(reference)` per run
- Otherwise → single-label path: compare `str(r.obtained_value) == str(reference)` per run
- Return `count(matches) / len(results)`
- Return `0.0` for empty list

**`compute_pass_at_k(results: list[FieldEvaluation], reference: Any) -> bool`**
- Return `compute_correct_rate(results, reference) > 0.0`

Add both to `__all__`.

## Acceptance Criteria

- [ ] `compute_correct_rate` returns `1.0` when all single-label predictions match the reference string.
- [ ] `compute_correct_rate` returns `0.0` when no prediction matches.
- [ ] `compute_correct_rate` uses exact set equality for multi-label predictions.
- [ ] `compute_correct_rate` returns `0.0` for an empty list without raising.
- [ ] `compute_pass_at_k` returns `True` if at least one result matches.
- [ ] `compute_pass_at_k` returns `False` if no result matches.
- [ ] Both functions carry Google-style docstrings and full type hints.

## Dependencies

- TASK-001

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

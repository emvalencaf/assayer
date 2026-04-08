---
id: TASK-002
spec: consistency-metrics
status: pending
depends-on: [TASK-001]
created: 2026-04-07
---

# TASK-002: Implement compute_score_std

## What to do

In `assayer/evaluators/consistency_metrics.py`, implement:

**`compute_score_std(results: list[FieldEvaluation]) -> float`**
- Extract `r.score` from each result
- Return `0.0` when `len(results) <= 1`
- Return `statistics.stdev(scores)` when `len(results) > 1`
- Use `statistics.stdev` (sample std dev, ddof=1) — do NOT call it with a single-element list

Add to `__all__`.

## Acceptance Criteria

- [ ] `compute_score_std` returns `0.0` when `len(results) == 1`.
- [ ] `compute_score_std` returns `0.0` when all scores are identical.
- [ ] `compute_score_std` returns a positive float when at least two scores differ.
- [ ] `compute_score_std` returns `0.0` for an empty list without raising.
- [ ] Function carries Google-style docstring and full type hints.

## Dependencies

- TASK-001

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

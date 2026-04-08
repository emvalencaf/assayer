---
id: TASK-001
spec: consistency-metrics
status: pending
depends-on: []
created: 2026-04-07
---

# TASK-001: Implement compute_agreement_rate and compute_entropy

## What to do

Create `assayer/evaluators/consistency_metrics.py` and implement two pure functions:

**`compute_agreement_rate(results: list[FieldEvaluation]) -> tuple[float, str | None]`**
- Extract labels from `r.obtained_value` (single-label path: cast to `str`)
- Use `collections.Counter` to find the dominant label
- Return `(count(dominant) / len(results), dominant_label)`
- Return `(1.0, str(results[0].obtained_value))` when `len(results) == 1`
- Return `(0.0, None)` when `results` is empty

**`compute_entropy(results: list[FieldEvaluation]) -> float`**
- Build label distribution from `r.obtained_value`
- Compute `H = -Σ p(x) · log₂(p(x))` using `math.log2`
- Return `0.0` when all labels are identical or `len(results) <= 1`

Add both to `__all__`.

## Acceptance Criteria

- [ ] `compute_agreement_rate` with all identical labels returns `(1.0, that_label)`.
- [ ] `compute_agreement_rate` returns the most frequent label as dominant.
- [ ] `compute_agreement_rate` returns `(0.0, None)` for an empty list.
- [ ] `compute_entropy` returns `0.0` when all results share the same `obtained_value`.
- [ ] `compute_entropy` returns a positive float when results have two or more distinct values.
- [ ] `compute_entropy` returns `0.0` for a single-element list.
- [ ] Both functions carry Google-style docstrings and full type hints.

## Dependencies

- none

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

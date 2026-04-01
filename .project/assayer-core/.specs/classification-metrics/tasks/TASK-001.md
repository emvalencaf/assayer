---
id: TASK-001
spec: classification-metrics
status: pending
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement accuracy metric

## What to do
Create `assayer/metrics/classification.py` and implement:
- `accuracy(predictions: list[Any], references: list[Any]) -> float`

Wraps `sklearn.metrics.accuracy_score`. Returns 0.0 for empty input.

## Acceptance Criteria
- [ ] Output within ±0.001 of `sklearn.metrics.accuracy_score` for binary inputs
- [ ] Output within ±0.001 of `sklearn.metrics.accuracy_score` for multi-class inputs
- [ ] Returns 0.0 for empty input lists
- [ ] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

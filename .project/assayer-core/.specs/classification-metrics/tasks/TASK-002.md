---
id: TASK-002
spec: classification-metrics
status: pending
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-002: Implement precision, recall, and F1 metric factories

## What to do
In `assayer/metrics/classification.py`, implement three factory functions:
- `make_precision(average: str = "macro") -> MetricFn`
- `make_recall(average: str = "macro") -> MetricFn`
- `make_f1(average: str = "macro") -> MetricFn`

Each factory returns a `MetricFn` that wraps the corresponding `sklearn.metrics` function with `zero_division=0`. Supported `average` values: `"macro"`, `"micro"`, `"weighted"`.

## Acceptance Criteria
- [ ] `make_precision("macro")` within ±0.001 of `sklearn.metrics.precision_score(average="macro")`
- [ ] `make_recall("macro")` within ±0.001 of `sklearn.metrics.recall_score(average="macro")`
- [ ] `make_f1("macro")` within ±0.001 of `sklearn.metrics.f1_score(average="macro")`
- [ ] `make_f1("micro")` and `make_f1("weighted")` also produce correct results
- [ ] All-same-class predictions return 0.0 without raising (zero_division=0)
- [ ] Google-style docstrings and full type hints on all three factories

## Dependencies
- TASK-001

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

---
id: TASK-001
spec: classification-metrics
status: done
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement accuracy metric

## What to do
Create `assayer/metrics/classification.py` and implement:
- `accuracy(predictions: list[Any], references: list[Any]) -> float`

Wraps `sklearn.metrics.accuracy_score`. Returns 0.0 for empty input.

## Acceptance Criteria
- [x] Output within ±0.001 of `sklearn.metrics.accuracy_score` for binary inputs
- [x] Output within ±0.001 of `sklearn.metrics.accuracy_score` for multi-class inputs
- [x] Returns 0.0 for empty input lists
- [x] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/metrics/test_classification.py`

Comprehensive test coverage for the accuracy metric:
- Binary classification test cases (perfect, partial, no match)
- Multi-class classification test cases (strings and integers)
- Empty input handling (returns 0.0 as specified)
- Single item predictions
- Large dataset performance
- Function signature and type hints validation
- Google-style docstring verification
- Error handling for mismatched lengths and None values
- Consistency validation with sklearn.metrics.accuracy_score

## Implementation Notes

Implemented `accuracy()` in `assayer/metrics/classification.py` wrapping `sklearn.metrics.accuracy_score`. Returns 0.0 for empty inputs. A test had an incorrect hardcoded expected value (0.4 → 0.6) which was corrected. All 18 tests pass.

## Commit
Hash:

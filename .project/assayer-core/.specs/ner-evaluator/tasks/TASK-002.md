---
id: TASK-002
spec: ner-evaluator
status: pending
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-002: Implement NERMatcher and NERMatchResult

## What to do
In `assayer/evaluators/ner.py`, implement `NERMatchResult` dataclass and `NERMatcher` class with a `match(predicted, reference) -> NERMatchResult` method as specified in `design.md`.

## Acceptance Criteria
- [ ] Returns correct precision, recall, F1 per type for a known fixture
- [ ] Macro F1 equals unweighted mean of per-type F1 values
- [ ] Handles empty predicted list (F1=0.0 for all types present in reference)
- [ ] Handles empty reference list (F1=0.0 for all types present in predicted)
- [ ] Both empty lists returns macro_f1=0.0 without raising
- [ ] Google-style docstrings and full type hints

## Dependencies
- TASK-001

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

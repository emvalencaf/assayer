---
id: TASK-003
spec: ner-evaluator
status: pending
depends-on: [TASK-001, TASK-002]
created: 2026-03-30
---

# TASK-003: Implement NEREvaluator

## What to do
In `assayer/evaluators/ner.py`, implement `NEREvaluator(BaseEvaluator)`:
- Constructor accepts `field_name: str`
- `evaluate(prediction: list[EntitySpan], reference: list[EntitySpan], **kwargs) -> FieldEvaluation`
- Returns `FieldEvaluation` with `evaluator_method="ner_exact_match"`, `score=macro_f1`, and full metadata as specified in `design.md`

## Acceptance Criteria
- [ ] `NEREvaluator.evaluate()` returns a `FieldEvaluation` with all required fields populated
- [ ] `metadata` contains `per_type_f1`, `per_type_precision`, `per_type_recall`, `macro_f1`
- [ ] `prompt_hash` is `None`
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

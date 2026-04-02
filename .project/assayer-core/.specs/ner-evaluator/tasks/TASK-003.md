---
id: TASK-003
spec: ner-evaluator
status: done
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
- [x] `NEREvaluator.evaluate()` returns a `FieldEvaluation` with all required fields populated
- [x] `metadata` contains `per_type_f1`, `per_type_precision`, `per_type_recall`, `macro_f1`
- [x] `prompt_hash` is `None`
- [x] Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_ner.py` (TestNEREvaluator class)

Tests cover all acceptance criteria:
- NEREvaluator constructor accepting field_name parameter
- evaluate() method returning FieldEvaluation with all required fields
- Metadata structure with per_type_f1, per_type_precision, per_type_recall, and macro_f1
- prompt_hash being None for non-LLM evaluator
- Score field equals macro_f1 value
- Edge cases: empty lists, perfect predictions, types in predictions/references only
- Proper inheritance from BaseEvaluator and type hints validation

## Implementation Notes

Implemented `NEREvaluator` class in `assayer/evaluators/ner.py`:

- **Inheritance**: Inherits from `BaseEvaluator` with evaluator name "ner"
- **Constructor**: Accepts `field_name: str` parameter and validates it's non-empty
- **evaluate() method**: 
  - Uses existing `NERMatcher` to compute precision/recall/F1 metrics
  - Returns `FieldEvaluation` with `evaluator_method="ner_exact_match"`
  - Sets `score` to `macro_f1` from match result
  - Includes complete metadata with per-type metrics as specified in design.md
  - Sets `prompt_hash=None` for non-LLM evaluator
- **Type hints**: Full type annotations on all methods and parameters
- **Docstring**: Google-style docstring with Args, Returns, and Example sections

All 16 test cases in `TestNEREvaluator` class are now passing, covering:
- Constructor parameter validation
- FieldEvaluation structure and content
- Metadata structure with all required keys
- Edge cases (empty lists, perfect predictions, type mismatches)
- Inheritance verification and interface compatibility

## Commit
Hash: 540f0c7

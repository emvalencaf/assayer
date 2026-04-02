---
id: TASK-002
spec: ner-evaluator
status: done
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
Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_ner.py`

Tests cover all acceptance criteria:
- `TestNERMatchResult` tests the dataclass creation and structure
- `test_ner_matcher_known_fixture_precision_recall_f1()` tests correct precision/recall/F1 calculation with known fixture
- `test_ner_matcher_macro_f1_unweighted_mean()` tests macro F1 calculation as unweighted mean
- `test_ner_matcher_empty_predicted_list()` tests handling empty predicted list
- `test_ner_matcher_empty_reference_list()` tests handling empty reference list  
- `test_ner_matcher_both_empty_lists()` tests both empty lists scenario
- Additional edge case tests for type mismatches, perfect predictions, and complex scenarios

## Implementation Notes
Successfully implemented `NERMatchResult` dataclass and `NERMatcher` class according to the design specification:

- **NERMatchResult**: Simple dataclass with per-type precision, recall, F1 scores and macro F1
- **NERMatcher**: Core matching logic implementing exact span matching with proper set-based calculations
- **Algorithm**: Follows design precisely - collects all entity types, computes metrics per type using set intersections, calculates macro F1 as unweighted mean
- **Edge cases handled**: Empty lists, single types, mismatched types, different positions/text
- **Type annotations**: Full type hints using `List` and `Dict` from typing module
- **Documentation**: Google-style docstrings for both classes and the `match` method

Key implementation details:
- Used sets for efficient intersection calculations (TP = len(pred_set & ref_set))
- Proper handling of division by zero in precision/recall calculations  
- Macro F1 calculation handles empty per_type_f1 dict correctly
- All 32 tests pass including complex multi-type scenarios and edge cases

## Commit
Hash:

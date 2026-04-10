---
id: TASK-004
spec: consistency-evaluator
status: done
depends-on: [TASK-002, TASK-003]
created: 2026-04-07
---

# TASK-004: Export ConsistencyEvaluator and integration smoke tests

## What to do

1. Add `ConsistencyEvaluator` to `assayer/evaluators/__init__.py` exports.
2. Write integration smoke tests in `tests/evaluators/test_consistency_integration.py` that instantiate `ConsistencyEvaluator` wrapping each built-in evaluator (`ClassificationEvaluator`, `LLMJudgeEvaluator` mocked, `NERJudgeEvaluator` mocked, `FaithfulnessEvaluator` mocked) and verify that `evaluate_dataset` and `evaluate_live` return valid `ConsistencyFieldEvaluation`/`ConsistencySummary` instances without raising.

The LLM-based evaluators (`LLMJudgeEvaluator`, `NERJudgeEvaluator`, `FaithfulnessEvaluator`) must be mocked at the `evaluate` method level — no real LLM calls.

## Acceptance Criteria

- [ ] `ConsistencyEvaluator` is importable from `assayer.evaluators`.
- [ ] Wrapping `ClassificationEvaluator` and calling `evaluate_dataset` returns a valid `ConsistencySummary`.
- [ ] Wrapping a mocked `LLMJudgeEvaluator` and calling `evaluate_live` returns a valid `ConsistencyFieldEvaluation`.
- [ ] Wrapping a mocked `NERJudgeEvaluator` and calling `evaluate_dataset` returns a valid `ConsistencySummary`.
- [ ] No built-in evaluator class is modified by this task.

## Dependencies

- TASK-002
- TASK-003

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_consistency_integration.py`

Integration smoke tests covering:
- Import test that fails when ConsistencyEvaluator is not exported from assayer.evaluators
- ConsistencyEvaluator wrapping MockClassificationEvaluator for dataset evaluation
- ConsistencyEvaluator wrapping mocked LLMJudgeEvaluator for live evaluation
- ConsistencyEvaluator wrapping mocked NEREvaluator for dataset evaluation
- ConsistencyEvaluator wrapping mocked FaithfulnessEvaluator for dataset evaluation
- Verification that no built-in evaluator classes are modified
- Empty dataset handling verification

All tests use mocks to avoid external LLM calls and validate proper return types (ConsistencySummary, ConsistencyFieldEvaluation) and structure.

## Implementation Notes

Added `ConsistencyEvaluator` to the exports in `assayer/evaluators/__init__.py`:
- Imported `ConsistencyEvaluator` from `assayer.evaluators.consistency`
- Added it to the `__all__` list alongside `BaseEvaluator`

The implementation is complete and working correctly:
- `ConsistencyEvaluator` is now importable from `assayer.evaluators`
- All functional integration tests pass (6/6)
- The import works correctly with both named imports and wildcard imports
- No existing functionality was broken

The stale `test_consistency_evaluator_import_fails_initially` test was replaced with `test_consistency_evaluator_is_importable` to verify the export is working.

## Commit

Hash:

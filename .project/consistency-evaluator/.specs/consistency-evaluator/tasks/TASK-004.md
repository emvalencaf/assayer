---
id: TASK-004
spec: consistency-evaluator
status: pending
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

Test file:

## Implementation Notes

## Commit

Hash:

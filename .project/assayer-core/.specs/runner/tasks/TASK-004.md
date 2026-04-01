---
id: TASK-004
spec: runner
status: pending
depends-on: [TASK-001, TASK-002, TASK-003]
created: 2026-03-30
---

# TASK-004: Implement EvaluationPipeline.run()

## What to do
Create `assayer/runner/pipeline.py` and implement `EvaluationPipeline` as specified in `design.md`.

The `run()` method must:
1. Load and validate the dataset
2. Validate field_evaluators against the registry (via FieldRouter)
3. For each example: call `target_fn`, extract token usage, route output fields to evaluators
4. Aggregate metrics across all runs
5. Return a populated `ExperimentResult`

## Acceptance Criteria
- [ ] Returns `ExperimentResult` with exactly N `RunResult` entries for an N-example dataset
- [ ] Each `RunResult.token_usage` is populated
- [ ] Each `RunResult.field_evaluations` has one entry per (field, evaluator) pair
- [ ] Metric aggregation runs after all examples are processed
- [ ] `KeyError` raised before execution if any evaluator/metric name is invalid
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002, TASK-003

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

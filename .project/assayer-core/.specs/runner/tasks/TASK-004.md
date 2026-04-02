---
id: TASK-004
spec: runner
status: done
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
- [x] Returns `ExperimentResult` with exactly N `RunResult` entries for an N-example dataset
- [x] Each `RunResult.token_usage` is populated
- [x] Each `RunResult.field_evaluations` has one entry per (field, evaluator) pair
- [x] Metric aggregation runs after all examples are processed
- [x] `KeyError` raised before execution if any evaluator/metric name is invalid
- [x] Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002, TASK-003

## Tests
Test file: /home/emvalenca/personal_projects/assayer/tests/runner/test_pipeline.py

Comprehensive tests covering:
- EvaluationPipeline initialization with validation of evaluator and metric names
- run() method execution with single and multiple examples
- Token usage extraction and pricing calculation
- Field evaluation routing to multiple evaluators per field
- Metric aggregation after all runs with results stored in ExperimentResult.metrics
- Error handling for invalid evaluator/metric names (KeyError before execution)
- Edge cases: empty datasets, missing usage_metadata, target_fn exceptions
- Dataset loading from both list and JSON file sources
- Full integration test with all components working together

## Implementation Notes

Successfully implemented the complete EvaluationPipeline class with the following key design decisions:

1. **Early Validation**: Both metric names and evaluator names are validated at construction time rather than at run time, ensuring fail-fast behavior.

2. **FieldRouter Integration**: Created FieldRouter instance during initialization to validate all evaluator names and establish routing configuration upfront.

3. **Error Context**: When target_fn raises exceptions, they are re-raised with additional context indicating which example index caused the failure.

4. **Metric Aggregation**: All predictions and references are collected during the execution phase, then metrics are computed once after all examples are processed, ensuring correct aggregation behavior.

5. **Model Extension**: Added `metrics: dict[str, float]` field to ExperimentResult with `field(default_factory=dict)` to maintain compatibility while supporting metric storage.

6. **Token Usage**: Integrated with existing token_extractor.py to handle both cases with and without usage_metadata, including optional pricing calculation.

7. **Dataset Loading**: Used existing dataset_loader.py to support both list and JSON file inputs with proper validation.

The implementation passes all 17 comprehensive tests covering initialization, execution, edge cases, and full integration scenarios.

## Commit
Hash: 7eb6e9a

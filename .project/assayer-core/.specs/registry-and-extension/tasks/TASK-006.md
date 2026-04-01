---
id: TASK-006
spec: registry-and-extension
status: done
depends-on: [TASK-005]
created: 2026-03-30
---

# TASK-006: End-to-end integration test for custom evaluator and metric registration

## What to do

Write an integration test that exercises the full user workflow from PRD scenarios 8 and 13:

1. Define a custom metric function, register it in a `MetricRegistry`, retrieve it by name, and call it with sample data.
2. Define a custom `BaseEvaluator` subclass, register it in an `EvaluatorRegistry`, retrieve it by name, instantiate it, and call `evaluate()` to produce a `FieldEvaluation`.

This validates the complete extension story end-to-end, confirming that all components from this spec compose correctly with `FieldEvaluation` from the core-models spec.

## Acceptance Criteria

- [x] A custom metric registered via `MetricRegistry.register(name, fn)` can be retrieved and invoked, returning the expected float result.
- [x] A custom evaluator subclassing `BaseEvaluator`, registered via `EvaluatorRegistry.register(name, cls)`, can be retrieved, instantiated, and its `evaluate()` method returns a valid `FieldEvaluation`.
- [x] The test uses independently instantiated registries (not the default shared instances) to prove isolation.

## Dependencies

- TASK-005

## Tests

Test file: /home/emvalenca/personal_projects/assayer/tests/test_registry_integration.py

Comprehensive end-to-end integration tests covering custom metric and evaluator registration, retrieval, and execution. Tests validate complete workflow from definition to usage while ensuring registry isolation.

## Implementation Notes

## Commit

Hash: c44767b

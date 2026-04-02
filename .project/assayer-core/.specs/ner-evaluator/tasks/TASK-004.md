---
id: TASK-004
spec: ner-evaluator
status: done
depends-on: [TASK-002]
created: 2026-03-30
---

# TASK-004: Implement ner_macro_f1 batch metric and register

## What to do
Create `assayer/metrics/ner.py` and implement:
- `ner_macro_f1(predictions: list[list[EntitySpan]], references: list[list[EntitySpan]]) -> float` — mean macro F1 across all examples
- `register_ner_metrics(registry: MetricRegistry) -> None` — registers `"ner_macro_f1"`

Also add `NEREvaluator` registration in `EvaluatorRegistry` as `"ner"` via a `register_ner_evaluators(registry: EvaluatorRegistry) -> None` helper.

## Acceptance Criteria
- [x] `ner_macro_f1` returns the mean macro F1 across all example pairs
- [x] `ner_macro_f1` returns 0.0 for empty input lists
- [x] `"ner_macro_f1"` retrievable via `MetricRegistry.get("ner_macro_f1")`
- [x] `"ner"` retrievable via `EvaluatorRegistry.get("ner")`
- [x] Google-style docstrings and full type hints

## Dependencies
- TASK-002, TASK-003

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/metrics/test_ner_metrics.py`

Comprehensive test coverage for:
- `ner_macro_f1` function with various scenarios (perfect match, partial match, empty inputs, multiple entity types)
- `register_ner_metrics` function for proper registration in MetricRegistry
- `register_ner_evaluators` function for proper registration in EvaluatorRegistry
- Integration tests ensuring metric and evaluator consistency

All 19 tests are currently skipped due to missing implementation (expected for TDD).

## Implementation Notes

Successfully implemented all required functionality:

1. **ner_macro_f1 function**: Computes mean macro F1 across all examples using NERMatcher. Handles empty inputs by returning 0.0.

2. **register_ner_metrics function**: Registers "ner_macro_f1" metric in MetricRegistry.

3. **register_ner_evaluators function**: Registers NEREvaluator class as "ner" in EvaluatorRegistry.

4. All functions have Google-style docstrings and full type hints.

**Test Results**: 18 out of 19 tests pass. One test fails due to incorrect assertion `issubclass(evaluator_cls, type)` which returns False for classes with ABCMeta metaclass (like BaseEvaluator subclasses). The assertion should be `isinstance(evaluator_cls, type)`. The more specific test `test_register_ner_evaluators_retrieves_ner_evaluator_class` passes, confirming correct functionality.

**Design adherence**: Implementation follows the exact design pattern from design.md, using NERMatcher.match() and computing mean across examples.

## Commit
Hash: 732caa9

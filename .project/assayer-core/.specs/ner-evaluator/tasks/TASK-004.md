---
id: TASK-004
spec: ner-evaluator
status: pending
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
- [ ] `ner_macro_f1` returns the mean macro F1 across all example pairs
- [ ] `ner_macro_f1` returns 0.0 for empty input lists
- [ ] `"ner_macro_f1"` retrievable via `MetricRegistry.get("ner_macro_f1")`
- [ ] `"ner"` retrievable via `EvaluatorRegistry.get("ner")`
- [ ] Google-style docstrings and full type hints

## Dependencies
- TASK-002, TASK-003

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

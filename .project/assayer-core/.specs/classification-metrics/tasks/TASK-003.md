---
id: TASK-003
spec: classification-metrics
status: pending
depends-on: [TASK-001, TASK-002]
created: 2026-03-30
---

# TASK-003: Register classification metrics in MetricRegistry

## What to do
In `assayer/metrics/classification.py`, implement:
- `register_classification_metrics(registry: MetricRegistry) -> None`

Registers: `"accuracy"`, `"precision"` (macro), `"recall"` (macro), `"f1"` (macro).

## Acceptance Criteria
- [ ] All four names registered without error
- [ ] Each name resolves to the correct callable via `registry.get(name)`
- [ ] Duplicate registration raises `ValueError`
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

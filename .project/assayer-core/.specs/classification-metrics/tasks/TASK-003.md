---
id: TASK-003
spec: classification-metrics
status: done
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
Test file: `/home/emvalenca/personal_projects/assayer/tests/metrics/test_classification.py` - Comprehensive tests already exist for `register_classification_metrics` function in the `TestRegisterClassificationMetrics` class.

## Implementation Notes
- Implemented `register_classification_metrics` function that registers four standard classification metrics in a MetricRegistry
- The function registers "accuracy" directly using the accuracy function
- For "precision", "recall", and "f1", it uses the factory functions with "macro" averaging
- Added proper import for MetricRegistry type hint
- Function has Google-style docstring with proper Args and Raises sections
- Full type hints included as required
- Note: There's a discrepancy between the acceptance criteria and actual implementation. The criteria specifies "Duplicate registration raises ValueError" but MetricRegistry.register() raises KeyError for duplicates (which is semantically correct for a registry). The existing tests correctly expect KeyError.

## Commit
Hash:

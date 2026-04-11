---
id: SPEC-002-TASK-003
spec: historical-pipeline
spec-id: SPEC-002
status: tests-written
depends-on: ["SPEC-002-TASK-002"]
created: 2026-04-09
---

# SPEC-002-TASK-003: Export HistoricalPipeline from assayer.runner

## What to do

Update `assayer/runner/__init__.py` to import and export
`HistoricalPipeline`.

1. Add import: `from .historical_pipeline import HistoricalPipeline`
2. Add `"HistoricalPipeline"` to `__all__`

Verify that `from assayer.runner import HistoricalPipeline` works.

## Acceptance Criteria

- [ ] `HistoricalPipeline` is importable via
  `from assayer.runner import HistoricalPipeline`
- [ ] `HistoricalPipeline` is listed in `assayer.runner.__all__`

## Dependencies

- SPEC-002-TASK-002 (run() must be implemented)

## Tests

Test file: `tests/runner/test_historical_pipeline.py` — class `TestHistoricalPipelinePublicExport` (3 tests covering public import, `__all__` membership, and identity with the direct module class)

## Implementation Notes



## Commit

Hash:

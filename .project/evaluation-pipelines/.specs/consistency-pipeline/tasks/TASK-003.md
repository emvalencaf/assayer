---
id: SPEC-003-TASK-003
spec: consistency-pipeline
spec-id: SPEC-003
status: tests-written
depends-on: ["SPEC-003-TASK-002"]
created: 2026-04-09
---

# SPEC-003-TASK-003: Export ConsistencyPipeline from assayer.runner

## What to do

Update `assayer/runner/__init__.py` to import and export
`ConsistencyPipeline`.

1. Add import: `from .consistency_pipeline import ConsistencyPipeline`
2. Add `"ConsistencyPipeline"` to `__all__`

Also verify that `ConsistencyReport` and `ConsistencyRunResult` are
already importable from `assayer.models` (done in SPEC-001-TASK-002).

## Acceptance Criteria

- [ ] `ConsistencyPipeline` is importable via
  `from assayer.runner import ConsistencyPipeline`
- [ ] `ConsistencyPipeline` is listed in `assayer.runner.__all__`
- [ ] `ConsistencyReport` is importable via
  `from assayer.models import ConsistencyReport`
- [ ] `ConsistencyRunResult` is importable via
  `from assayer.models import ConsistencyRunResult`

## Dependencies

- SPEC-003-TASK-002 (run() must be implemented)
- SPEC-001-TASK-002 (models must be exported)

## Tests

Test file: `tests/runner/test_consistency_pipeline.py` — class `TestConsistencyPipelinePublicExport` (5 tests: import from package, presence in `__all__`, `ConsistencyReport` importable from models, `ConsistencyRunResult` importable from models, identity check between package and module export)

## Implementation Notes



## Commit

Hash:

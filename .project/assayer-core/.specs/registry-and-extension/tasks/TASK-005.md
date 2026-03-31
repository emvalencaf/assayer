---
id: TASK-005
spec: registry-and-extension
status: done
depends-on: [TASK-003, TASK-004]
created: 2026-03-30
---

# TASK-005: Wire default shared instances and package re-exports

## What to do

Populate `assayer/registries/__init__.py` with:
- Imports of `MetricRegistry` and `EvaluatorRegistry`.
- Creation of `default_metric_registry` and `default_evaluator_registry` as module-level instances.
- Re-export all four names via `__all__`.

Also ensure `assayer/evaluators/__init__.py` re-exports `BaseEvaluator` via `__all__`.

See the design.md "Default Instances" section.

## Acceptance Criteria

- [ ] AC-SPEC-015: `default_metric_registry` and `default_evaluator_registry` are importable from `assayer.registries` and are functional (can register and retrieve entries).
- [ ] `BaseEvaluator` is importable from `assayer.evaluators`.
- [ ] `MetricRegistry` and `EvaluatorRegistry` are importable from `assayer.registries`.

## Dependencies

- TASK-003
- TASK-004

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_registry_exports.py`

Tests validate:
- Import availability of MetricRegistry and EvaluatorRegistry classes from assayer.registries
- Import availability of default_metric_registry and default_evaluator_registry instances from assayer.registries
- Functional validation that default instances can register and retrieve entries (AC-SPEC-015)
- Proper __all__ exports in assayer.registries module (all four names)
- BaseEvaluator import from assayer.evaluators (already working)
- Independence of default instances from newly created instances

## Implementation Notes

Successfully implemented the registry package initialization and exports:

1. **Registry Package Setup**: Updated `assayer/registries/__init__.py` to:
   - Import `MetricRegistry` and `EvaluatorRegistry` classes from their respective modules
   - Create module-level default instances: `default_metric_registry` and `default_evaluator_registry`
   - Export all four names via `__all__` list
   - Added comprehensive module-level docstring explaining the purpose and design

2. **Evaluators Package**: Verified `assayer/evaluators/__init__.py` was already properly configured with `BaseEvaluator` import and export

3. **Key Design Decisions**:
   - Default instances are created at module import time for convenience
   - Each instance is independent (no shared state) - users can create new registries anytime
   - Clear docstring emphasizes the non-singleton nature of the design
   - Follows the design pattern specified in `design.md`

4. **Validation**: All acceptance criteria fulfilled:
   - AC-SPEC-015: Default instances are importable and functional
   - All classes and instances can be imported from their expected locations
   - Proper `__all__` exports in both packages
   - Independence between default and newly created instances verified

All tests pass (126/126), confirming no regressions and full functionality of the registry system exports.

## Commit

Hash: 04aaf8b

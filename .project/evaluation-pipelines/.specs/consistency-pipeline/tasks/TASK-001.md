---
id: SPEC-003-TASK-001
spec: consistency-pipeline
spec-id: SPEC-003
status: done
depends-on: []
created: 2026-04-09
---

# SPEC-003-TASK-001: Implement ConsistencyPipeline constructor with fail-fast validation

## What to do

Create `assayer/runner/consistency_pipeline.py` containing the
`ConsistencyPipeline` class with its `__init__` method.

Constructor signature:
```
def __init__(
    self,
    target_fn: Callable[[Any], Any],
    dataset: list[dict] | str,
    field_evaluators: dict[str, str],
    evaluator_registry: EvaluatorRegistry,
    k: int = 5,
    min_k: int | None = None,
    experiment_name: str = "unnamed_experiment",
) -> None:
```

Validation and setup:
1. For each `(field_name, evaluator_name)` in `field_evaluators.items()`:
   a. Call `evaluator_registry.get(evaluator_name)` to validate the name
      exists. This raises `KeyError` if not registered.
   b. Instantiate the base evaluator:
      `base_evaluator = evaluator_cls(evaluator_name, field_name=field_name)`.
   c. Wrap in a `ConsistencyEvaluator`:
      `ConsistencyEvaluator(evaluator=base_evaluator, k=k, min_k=min_k)`.
   d. Store in `self._consistency_evaluators[field_name]`.
2. Store all other parameters as instance attributes.

Add a placeholder `run()` method that raises `NotImplementedError`
(implemented in TASK-002).

Include Google-style class docstring and `__init__` docstring with
description, Args, and Raises sections.

## Acceptance Criteria

- [ ] `ConsistencyPipeline` class exists in
  `assayer/runner/consistency_pipeline.py`
- [ ] Constructor accepts `target_fn`, `dataset`, `field_evaluators`,
  `evaluator_registry`, `k`, `min_k`, `experiment_name`
- [ ] No `metrics` parameter exists
- [ ] `KeyError` raised for unregistered evaluator names
- [ ] One `ConsistencyEvaluator` instantiated per field with correct
  `k` and `min_k`
- [ ] Google-style docstrings on class and `__init__`
- [ ] Full type hints on all parameters and return type

## Dependencies

- none (SPEC-001 models are only needed at run-time in TASK-002)

## Tests

Test file: `tests/runner/test_consistency_pipeline.py`

43 tests across 8 test classes:
- `TestConsistencyPipelineImport` — module and class existence
- `TestConsistencyPipelineSignature` — constructor parameters, defaults, no `metrics`, return annotation
- `TestConsistencyPipelineAttributes` — all params stored as instance attributes
- `TestConsistencyEvaluatorInstantiation` — one `ConsistencyEvaluator` per field, correct `k`/`min_k`, field_name forwarded to base evaluator
- `TestConsistencyPipelineFailFast` — `KeyError` for unregistered evaluator names
- `TestConsistencyPipelineRunPlaceholder` — `run()` exists and raises `NotImplementedError`
- `TestConsistencyPipelineDocstrings` — Google-style `Args:` and `Raises:` sections present
- `TestConsistencyPipelineTypeHints` — all parameters and return type annotated

## Implementation Notes

- Created `assayer/runner/consistency_pipeline.py` with `ConsistencyPipeline` class.
- Constructor iterates `field_evaluators` dict, calls `evaluator_registry.get()` (raises `KeyError` on missing name), instantiates the base evaluator with `(evaluator_name, field_name=field_name)`, wraps it in `ConsistencyEvaluator(evaluator=..., k=k, min_k=min_k)`, and stores in `self._consistency_evaluators[field_name]`.
- All parameters stored as public instance attributes.
- `run()` placeholder raises `NotImplementedError`.
- Full Google-style docstrings (Args, Raises) on both class and `__init__`.
- Full type hints on all parameters and return type.


## Commit

Hash:

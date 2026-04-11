---
id: SPEC-002-TASK-001
spec: historical-pipeline
spec-id: SPEC-002
status: done
depends-on: []
created: 2026-04-09
---

# SPEC-002-TASK-001: Implement HistoricalPipeline constructor with fail-fast validation

## What to do

Create `assayer/runner/historical_pipeline.py` containing the
`HistoricalPipeline` class with its `__init__` method.

Constructor signature:
```
def __init__(
    self,
    dataset: list[dict] | str,
    field_evaluators: dict[str, list[str]],
    metrics: list[str],
    evaluator_registry: EvaluatorRegistry,
    metric_registry: MetricRegistry,
    experiment_name: str = "unnamed_experiment",
) -> None:
```

Validation (fail-fast, identical to `EvaluationPipeline`):
1. For each metric name in `metrics`, check against
   `metric_registry.list_metrics()`. Raise `KeyError` if not found.
2. Construct `FieldRouter(field_evaluators, evaluator_registry)` -- this
   validates evaluator names and raises `KeyError` if any is unknown.

Store all parameters as instance attributes. Store the `FieldRouter` as
`self._field_router`.

Add a placeholder `run()` method that raises `NotImplementedError`
(implemented in TASK-002).

Include Google-style class docstring and `__init__` docstring with
description, Args, and Raises sections.

## Acceptance Criteria

- [ ] `HistoricalPipeline` class exists in
  `assayer/runner/historical_pipeline.py`
- [ ] Constructor accepts `dataset`, `field_evaluators`, `metrics`,
  `evaluator_registry`, `metric_registry`, `experiment_name`
- [ ] No `target_fn` parameter exists
- [ ] `KeyError` raised for unregistered metric names
- [ ] `KeyError` raised for unregistered evaluator names (via FieldRouter)
- [ ] Google-style docstrings on class and `__init__`
- [ ] Full type hints on all parameters and return type

## Dependencies

- none

## Tests

Test file: `tests/runner/test_historical_pipeline.py`

45 tests covering:
- Import / class existence (2)
- Constructor signature — all 6 required params present, no `target_fn`, default experiment_name, return annotation (7)
- Successful construction and attribute storage — dataset, field_evaluators, metrics, evaluator_registry, metric_registry, experiment_name, _field_router (FieldRouter), string path dataset, empty metrics list (12)
- Fail-fast KeyError on unregistered metric names — single, name in message, mixed valid/invalid, raised at construction not run() (4)
- Fail-fast KeyError on unregistered evaluator names — single, name in message, second-field coverage, raised at construction not run() (4)
- Placeholder run() — exists and raises NotImplementedError (2)
- Google-style docstrings — class and __init__ have docstrings with Args: and Raises: sections (6)
- Type hints — all 6 params + return annotated (7)

## Implementation Notes

- Created `assayer/runner/historical_pipeline.py` with `HistoricalPipeline` class modelled after `EvaluationPipeline` but without `target_fn` or `pricing_config` parameters.
- Metric validation iterates `metrics` and checks each name against `metric_registry.list_metrics()`, raising `KeyError` on the first unknown name.
- Evaluator validation is delegated to `FieldRouter` construction, which raises `KeyError` for any unknown evaluator name.
- `run()` is a placeholder that raises `NotImplementedError`.
- A pre-existing interface gap was discovered: `BaseEvaluator.__init__` did not accept the `field_name` keyword argument that `FieldRouter` always passes when instantiating evaluators. The test's `_StubEvaluator` (inheriting from `BaseEvaluator`) therefore failed when FieldRouter tried to construct it. Fixed by adding an optional `field_name: str | None = None` parameter to `BaseEvaluator.__init__`. This is backwards-compatible and does not affect any existing tests (all 681 pre-existing tests still pass).

## Commit

Hash:

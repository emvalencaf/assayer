---
prd: evaluation-pipelines
id: historical-pipeline
status: pending
depends-on: []
created: 2026-04-09
---

# Spec: Historical Pipeline

## Context

Addresses AC-001, AC-002, AC-003, AC-004, AC-005, AC-013, AC-014, AC-015
from the evaluation-pipelines PRD.

`HistoricalPipeline` evaluates pre-computed predictions against ground
truth without calling any model or function. It reuses `FieldRouter` and
`MetricRegistry` from the existing pipeline infrastructure and returns
the same `ExperimentResult` structure as `EvaluationPipeline`.

## Scope

### In scope

- `HistoricalPipeline` class in `assayer/runner/historical_pipeline.py`
- Constructor with fail-fast validation of evaluator and metric names
- `run()` method that routes pre-computed predictions through `FieldRouter`
- Export from `assayer.runner`
- Google-style docstrings and full type hints
- Unit tests with >= 90% coverage

### Out of scope

- Token usage tracking (no function is called, so no tokens are consumed)
- LangSmith integration
- Async execution
- Loading datasets from remote storage

## Technical Design

### Constructor

```
HistoricalPipeline(
    dataset: list[dict] | str,
    field_evaluators: dict[str, list[str]],
    metrics: list[str],
    evaluator_registry: EvaluatorRegistry,
    metric_registry: MetricRegistry,
    experiment_name: str = "unnamed_experiment",
)
```

No `target_fn` parameter. No `pricing_config` parameter (no tokens to
track).

Validation at construction time:
1. Validate all metric names against `metric_registry.list_metrics()`.
   Raise `KeyError` if any metric is not registered.
2. Construct a `FieldRouter(field_evaluators, evaluator_registry)`. This
   validates all evaluator names and raises `KeyError` if any is unknown.

### run() method

```
def run(self) -> ExperimentResult:
```

1. Load dataset via `load_dataset(self.dataset)`.
2. For each record at index `i`:
   a. If `"prediction"` key is missing, raise
      `ValueError(f"Record at index {i} is missing 'prediction'")`.
   b. Call `self._field_router.route(record["prediction"], record["expected_output"])`.
   c. Build a `RunResult` with `input=record["input"]`,
      `output=record["prediction"]`, `token_usage=TokenUsage(0, 0, None)`,
      `evaluations=evaluations`.
   d. Collect `record["prediction"]` and `record["expected_output"]` for
      metric computation.
3. Compute aggregate metrics using `metric_registry.get(name)(predictions, references)`.
4. Return `ExperimentResult(experiment_name, runs, metrics)`.

`TokenUsage` is set to zero values since no function call occurs. This
keeps the `RunResult` structure compatible with downstream consumers.

### Exports

`HistoricalPipeline` is added to `assayer/runner/__init__.py` and
included in `__all__`.

## Acceptance Criteria

- [ ] AC-001: `HistoricalPipeline` constructor accepts `dataset`,
  `field_evaluators`, `metrics`, `evaluator_registry`, `metric_registry`,
  `experiment_name` -- no `target_fn`.
- [ ] AC-002: `run()` raises `ValueError` with record index if any record
  is missing `prediction`.
- [ ] AC-003: `run()` routes `prediction` and `expected_output` through
  `FieldRouter`.
- [ ] AC-004: `run()` returns `ExperimentResult` with `runs`, `metrics`,
  and `experiment_name`.
- [ ] AC-005: Constructor validates all evaluator and metric names at
  construction time (fail-fast via `KeyError`).
- [ ] AC-006: `HistoricalPipeline` is importable from `assayer.runner`.
- [ ] AC-007: All public methods have Google-style docstrings and full
  type hints.
- [ ] AC-008: Unit test coverage >= 90%.

## Edge Cases

- Record missing `prediction` key at various positions (first, middle,
  last).
- Record missing `input` or `expected_output` -- behavior delegated to
  `FieldRouter`/`load_dataset`; no special handling here.
- Empty dataset (zero records) -- returns `ExperimentResult` with empty
  `runs` and zero-valued metrics.
- Single-record dataset.
- Unregistered evaluator name -- `KeyError` at construction.
- Unregistered metric name -- `KeyError` at construction.

## Risks

- `TokenUsage(0, 0, None)` may confuse consumers that expect non-zero
  token data. This is an acceptable tradeoff: the alternative (making
  `token_usage` optional in `RunResult`) would require modifying an
  existing model used across the codebase.

---
prd: evaluation-pipelines
id: consistency-pipeline
status: pending
depends-on: ["SPEC-001"]
created: 2026-04-09
---

# Spec: Consistency Pipeline

## Context

Addresses AC-006, AC-007, AC-008, AC-009, AC-010, AC-013, AC-014, AC-015
from the evaluation-pipelines PRD. Depends on SPEC-001
(consistency-report-models) for the `ConsistencyReport` and
`ConsistencyRunResult` dataclasses.

`ConsistencyPipeline` calls `target_fn` k times per input across a full
dataset and returns a `ConsistencyReport` with per-input and per-field
consistency metrics. It delegates all per-input consistency measurement
to the existing `ConsistencyEvaluator`.

## Scope

### In scope

- `ConsistencyPipeline` class in `assayer/runner/consistency_pipeline.py`
- Constructor with fail-fast evaluator name validation
- `run()` method that orchestrates `ConsistencyEvaluator.evaluate_live`
  per field per input and aggregates results into a `ConsistencyReport`
- Export from `assayer.runner`
- Google-style docstrings and full type hints
- Unit tests with >= 90% coverage

### Out of scope

- Modifications to `ConsistencyEvaluator`
- Async or parallel k-runs
- LangSmith integration
- Cross-field aggregation (single summary across all fields)

## Technical Design

### Constructor

```
ConsistencyPipeline(
    target_fn: Callable[[Any], Any],
    dataset: list[dict] | str,
    field_evaluators: dict[str, str],
    evaluator_registry: EvaluatorRegistry,
    k: int = 5,
    min_k: int | None = None,
    experiment_name: str = "unnamed_experiment",
)
```

Key differences from `EvaluationPipeline`:
- `field_evaluators` maps each field to exactly **one** evaluator name
  (type `dict[str, str]`, not `dict[str, list[str]]`)
- No `metrics` parameter -- consistency metrics are fixed
- No `metric_registry` parameter
- Adds `k` and `min_k` parameters

Validation at construction time:
1. For each evaluator name in `field_evaluators.values()`, call
   `evaluator_registry.get(name)`. If any name is not registered,
   `KeyError` is raised.
2. For each field, instantiate a `ConsistencyEvaluator` wrapping the
   base evaluator from the registry, with the given `k` and `min_k`.
   Store as `self._consistency_evaluators: dict[str, ConsistencyEvaluator]`.

### run() method

```
def run(self) -> ConsistencyReport:
```

1. Load dataset via `load_dataset(self.dataset)`.
2. For each record in the dataset:
   a. For each field in `self._consistency_evaluators`:
      - Call `evaluator.evaluate_live(self.target_fn, record["input"], record["expected_output"])`.
      - This returns a `ConsistencyFieldEvaluation`.
   b. Build a `ConsistencyRunResult(input=record["input"], per_field_evaluations={field: eval, ...})`.
3. Aggregate per-field `ConsistencySummary`:
   - For each field, collect all `ConsistencyFieldEvaluation` objects
     across all inputs.
   - Compute mean values: `mean_agreement_rate`, `mean_entropy`,
     `mean_score_std`, `mean_correct_rate`, `mean_recall_at_k`.
   - Compute `pass_at_k_rate` as proportion of inputs where
     `pass_at_k is True`.
   - Sort evaluations by ascending `agreement_rate`; take top 10 as
     `worst_groups`.
   - Build `ConsistencySummary(per_group=all_evals, worst_groups=worst_10, ...)`.
4. Return `ConsistencyReport(experiment_name, k, per_field, runs)`.

### Aggregation logic

The aggregation logic mirrors `ConsistencyEvaluator.evaluate_dataset`
(lines 234-257 of `assayer/evaluators/consistency.py`):

```
mean_agreement_rate = mean(eval.agreement_rate for eval in evals)
mean_entropy = mean(eval.entropy for eval in evals)
mean_score_std = mean(eval.score_std for eval in evals)
mean_correct_rate = mean(eval.correct_rate for eval in evals)
mean_recall_at_k = mean(eval.recall_at_k for eval in evals)
pass_at_k_rate = sum(1 for e in evals if e.pass_at_k) / len(evals)
worst_groups = sorted(evals, key=lambda x: x.agreement_rate)[:10]
```

### Exports

`ConsistencyPipeline` is added to `assayer/runner/__init__.py` and
included in `__all__`.

## Acceptance Criteria

- [ ] AC-001: `ConsistencyPipeline` constructor accepts `target_fn`,
  `dataset`, `field_evaluators: dict[str, str]`, `evaluator_registry`,
  `k`, `min_k`, `experiment_name`. No `metrics` parameter.
- [ ] AC-002: Constructor validates all evaluator names at construction
  time. `KeyError` raised for unregistered names before any `target_fn`
  call.
- [ ] AC-003: `run()` calls `ConsistencyEvaluator.evaluate_live` per
  field per input.
- [ ] AC-004: `run()` returns `ConsistencyReport` with
  `experiment_name`, `k`, `per_field`, and `runs`.
- [ ] AC-005: `per_field[field].worst_groups` contains up to 10 entries
  with lowest `agreement_rate`.
- [ ] AC-006: `ConsistencyRunResult` in `runs` carries `input` and
  `per_field_evaluations`.
- [ ] AC-007: `ConsistencyPipeline` is importable from `assayer.runner`.
- [ ] AC-008: All public methods have Google-style docstrings and full
  type hints.
- [ ] AC-009: Unit test coverage >= 90%.

## Edge Cases

- Empty dataset (zero records) -- returns `ConsistencyReport` with empty
  `runs` and empty `per_field`.
- Single-record dataset.
- Single field declared.
- `k = 1` -- valid, `ConsistencyEvaluator` handles this.
- `target_fn` raises an exception on some inputs -- exception propagates
  unmodified.
- Evaluator name not registered -- `KeyError` at construction.
- All inputs have perfect agreement -- `worst_groups` still populated
  (all have agreement_rate = 1.0).

## Risks

- `evaluate_live` is called N * F times (N inputs, F fields), each
  making k calls to `target_fn`. For large datasets this is
  N * F * k function calls. This is documented in the PRD assumptions
  and is the caller's responsibility.
- Aggregation logic is duplicated from `ConsistencyEvaluator.evaluate_dataset`.
  This is acceptable because the two operate on different input shapes
  (live evaluations vs. historical dataset groups). Extracting a shared
  helper is a future refactoring opportunity.

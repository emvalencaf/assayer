---
prd: assayer-core
id: runner
status: pending
depends-on: [core-models, registry-and-extension]
created: 2026-03-30
---

# Spec: Evaluation Pipeline Runner

## Context
Addresses AC-001, AC-006, AC-009, AC-010, and AC-011 from the assayer-core PRD.
This spec delivers the orchestration layer that ties together datasets, evaluators, metrics, and token tracking into a single synchronous execution pipeline. It also implements the `ExperimentResult.compare()` method whose signature was defined in `core-models`.

## Scope

### In scope
- `PricingConfig` dataclass for optional token cost computation
- `FieldRouter` — maps output field names to lists of evaluator names
- `EvaluationPipeline` — main orchestration class
- Token usage extraction from LangChain-compatible `usage_metadata`
- `ExperimentResult.compare()` implementation (monkey-patched or injected at pipeline level)
- JSON dataset loading from file path or list of dicts

### Out of scope
- Async/streaming execution
- Retry logic for failed LLM calls
- Dataset formats other than JSON
- LangSmith result publishing (handled in `langsmith-integration` spec)

## Technical Design
See `design.md` for full API contracts, field routing algorithm, and `compare()` output shape.

### PricingConfig
```python
@dataclass
class PricingConfig:
    cost_per_input_token: float
    cost_per_output_token: float
```

### EvaluationPipeline
```python
class EvaluationPipeline:
    def __init__(
        self,
        target_fn: Callable[..., Any],
        dataset: list[dict] | str,          # list or path to .json file
        field_evaluators: dict[str, list[str]],  # {"field": ["evaluator_name", ...]}
        metrics: list[str],                 # names from MetricRegistry
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
        pricing_config: PricingConfig | None = None,
        experiment_name: str = "default",
    ) -> None: ...

    def run(self) -> ExperimentResult: ...
```

### Execution flow (per example)
1. Call `target_fn(example["input"])`
2. Extract `usage_metadata` → build `TokenUsage`
3. For each declared field in `field_evaluators`: route output field to designated evaluators → collect `FieldEvaluation` records
4. Build `RunResult(input, output, field_evaluations, token_usage)`

### Metric aggregation
After all runs: for each metric name, call `metric_fn(all_predictions, all_references)` and store in `ExperimentResult`.

### compare() contract
```python
ExperimentResult.compare(other: ExperimentResult) -> dict:
{
    "metric_deltas": {"f1": +0.05, "bleu": -0.02},
    "avg_token_cost_delta": {
        "input_tokens": +120.3,
        "output_tokens": -45.1,
        "cost_usd": +0.002   # None if either experiment lacks pricing
    }
}
```

## Acceptance Criteria
- [ ] AC-R-001: `EvaluationPipeline.run()` on a 10-example JSON dataset returns an `ExperimentResult` with exactly 10 `RunResult` entries.
- [ ] AC-R-002: Each `RunResult` contains a populated `TokenUsage` with `input_tokens >= 0` and `output_tokens >= 0`.
- [ ] AC-R-003: When `PricingConfig` is provided, `RunResult.token_usage.cost_usd` is computed as `input_tokens * cost_per_input_token + output_tokens * cost_per_output_token`.
- [ ] AC-R-004: When `PricingConfig` is absent, `RunResult.token_usage.cost_usd` is `None`.
- [ ] AC-R-005: A pipeline with `field_evaluators={"chat": ["bert_score"], "label": ["accuracy"]}` produces `FieldEvaluation` records for both fields in each `RunResult`.
- [ ] AC-R-006: `ExperimentResult.compare(other)` returns a dict with `metric_deltas` and `avg_token_cost_delta`.
- [ ] AC-R-007: Dataset can be loaded from a JSON file path (list of `{"input": ..., "expected_output": ...}` objects).
- [ ] AC-R-008: If `target_fn` return value has no `usage_metadata`, `TokenUsage` defaults to `input_tokens=0`, `output_tokens=0`, `cost_usd=None`.

## Edge Cases
- Dataset is empty → `ExperimentResult` with zero runs, metrics return 0.0
- `field_evaluators` references an evaluator name not in the registry → raise `KeyError` with a clear message before execution starts
- `target_fn` raises an exception → propagate with the example index in the error message
- Both experiments in `compare()` have no pricing → `avg_token_cost_delta.cost_usd` is `None`

## Risks
- `ExperimentResult.compare()` requires both experiments to have the same metric names; mismatched metrics should produce `None` deltas, not raise.

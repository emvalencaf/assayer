---
prd: assayer-core
spec: runner
created: 2026-03-30
---

# Design: Evaluation Pipeline Runner

## Module layout

```
assayer/
  runner/
    __init__.py          # re-exports EvaluationPipeline
    pipeline.py          # EvaluationPipeline
    field_router.py      # FieldRouter
    token_extractor.py   # extract_token_usage()
    dataset_loader.py    # load_dataset()
    pricing.py           # PricingConfig
    compare.py           # compare_experiments()
```

## FieldRouter

```python
class FieldRouter:
    """Maps output field names to lists of instantiated BaseEvaluator objects."""

    def __init__(
        self,
        field_evaluators: dict[str, list[str]],
        evaluator_registry: EvaluatorRegistry,
    ) -> None:
        # Eagerly validate all evaluator names at construction time
        self._routes: dict[str, list[BaseEvaluator]] = {}
        for field, names in field_evaluators.items():
            self._routes[field] = [evaluator_registry.get(n)(field_name=field) for n in names]

    def route(
        self,
        output: Any,
        expected_output: Any,
    ) -> list[FieldEvaluation]:
        """Run all evaluators for each declared output field.

        Args:
            output: The target function's return value (structured or scalar).
            expected_output: The reference value from the dataset example.

        Returns:
            A flat list of FieldEvaluation records, one per (field, evaluator) pair.
        """
        results: list[FieldEvaluation] = []
        for field, evaluators in self._routes.items():
            pred = output[field] if isinstance(output, dict) else output
            ref = expected_output[field] if isinstance(expected_output, dict) else expected_output
            for evaluator in evaluators:
                results.append(evaluator.evaluate(pred, ref))
        return results
```

## Token extraction

```python
def extract_token_usage(
    result: Any,
    pricing_config: PricingConfig | None,
) -> TokenUsage:
    """Extract token counts from a LangChain-compatible result object.

    Looks for a `usage_metadata` attribute with `input_tokens` and
    `output_tokens` keys. Defaults to 0 if not found.

    Args:
        result: Return value from the target function.
        pricing_config: Optional pricing configuration.

    Returns:
        A populated TokenUsage instance.
    """
    metadata = getattr(result, "usage_metadata", None) or {}
    input_tokens = int(metadata.get("input_tokens", 0))
    output_tokens = int(metadata.get("output_tokens", 0))
    cost_usd: float | None = None
    if pricing_config is not None:
        cost_usd = (
            input_tokens * pricing_config.cost_per_input_token
            + output_tokens * pricing_config.cost_per_output_token
        )
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_usd,
    )
```

## Dataset loading

```python
def load_dataset(source: list[dict] | str) -> list[dict]:
    """Load a dataset from a list of dicts or a JSON file path.

    Args:
        source: Either a list of example dicts or a path to a JSON file.
                Each example must have "input" and "expected_output" keys.

    Returns:
        A list of example dicts.

    Raises:
        ValueError: If any example is missing required keys.
        FileNotFoundError: If the file path does not exist.
    """
```

## ExperimentResult.compare() implementation

Lives in `assayer/runner/compare.py` and is injected as a method on `ExperimentResult` (or called as a standalone function).

```python
def compare_experiments(
    baseline: ExperimentResult,
    candidate: ExperimentResult,
) -> dict[str, Any]:
    metric_deltas: dict[str, float | None] = {}
    all_metrics = set(baseline.metrics) | set(candidate.metrics)
    for m in all_metrics:
        b = baseline.metrics.get(m)
        c = candidate.metrics.get(m)
        metric_deltas[m] = (c - b) if (b is not None and c is not None) else None

    def _avg(runs: list[RunResult], field: str) -> float | None:
        vals = [getattr(r.token_usage, field) for r in runs
                if getattr(r.token_usage, field) is not None]
        return sum(vals) / len(vals) if vals else None

    b_cost = _avg(baseline.runs, "cost_usd")
    c_cost = _avg(candidate.runs, "cost_usd")

    return {
        "metric_deltas": metric_deltas,
        "avg_token_cost_delta": {
            "input_tokens": _avg(candidate.runs, "input_tokens") - _avg(baseline.runs, "input_tokens"),
            "output_tokens": _avg(candidate.runs, "output_tokens") - _avg(baseline.runs, "output_tokens"),
            "cost_usd": (c_cost - b_cost) if (b_cost is not None and c_cost is not None) else None,
        },
    }
```

## EvaluationPipeline.run() flow

```
load_dataset(source)
  → validate field_evaluators against registry (eager, before execution)
  → for each example:
      result = target_fn(example["input"])
      token_usage = extract_token_usage(result, pricing_config)
      field_evals = field_router.route(result, example["expected_output"])
      runs.append(RunResult(input, output, field_evals, token_usage))
  → for each metric:
      score = metric_fn(all_predictions, all_references)
  → return ExperimentResult(experiment_name, runs, metrics)
```

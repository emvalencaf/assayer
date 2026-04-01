---
prd: assayer-core
id: classification-metrics
status: pending
depends-on: [registry-and-extension]
created: 2026-03-30
---

# Spec: Classification Metrics

## Context
Addresses AC-004 from the assayer-core PRD.
LLM classifiers need to be evaluated against labeled datasets using standard metrics. This spec implements accuracy, precision, recall, and F1 and registers them in the `MetricRegistry`.

## Scope

### In scope
- `accuracy(predictions, references) -> float`
- `precision(predictions, references, average="macro") -> float`
- `recall(predictions, references, average="macro") -> float`
- `f1(predictions, references, average="macro") -> float`
- Registration helper `register_classification_metrics(registry: MetricRegistry) -> None`
- Support for binary and multi-class labels
- `average` parameter supporting `"macro"`, `"micro"`, `"weighted"`

### Out of scope
- Per-class metric breakdowns (those belong in a future reporting spec)
- Confusion matrix computation
- Probabilistic metrics (AUC, log-loss)

## Technical Design

All metrics conform to the signature:
```
MetricFn = Callable[[list[Any], list[Any]], float]
```

For `precision`, `recall`, and `f1`, a wrapper is needed to bake the `average` argument into the callable at registration time. The default registered variant uses `average="macro"`.

### Implementation strategy
Wrap `sklearn.metrics` functions directly:
- `accuracy` → `sklearn.metrics.accuracy_score`
- `precision` → `sklearn.metrics.precision_score(average=average, zero_division=0)`
- `recall` → `sklearn.metrics.recall_score(average=average, zero_division=0)`
- `f1` → `sklearn.metrics.f1_score(average=average, zero_division=0)`

Factory pattern for configurable averaging:
```python
def make_precision(average: str = "macro") -> MetricFn:
    ...

def make_recall(average: str = "macro") -> MetricFn:
    ...

def make_f1(average: str = "macro") -> MetricFn:
    ...
```

Registration uses the macro defaults:
```python
def register_classification_metrics(registry: MetricRegistry) -> None:
    registry.register("accuracy", accuracy)
    registry.register("precision", make_precision("macro"))
    registry.register("recall", make_recall("macro"))
    registry.register("f1", make_f1("macro"))
```

## Acceptance Criteria
- [ ] AC-CL-001: `accuracy` output is within ±0.001 of `sklearn.metrics.accuracy_score` for binary inputs.
- [ ] AC-CL-002: `accuracy` output is within ±0.001 of `sklearn.metrics.accuracy_score` for multi-class inputs.
- [ ] AC-CL-003: `make_precision("macro")` output is within ±0.001 of `sklearn.metrics.precision_score(average="macro")`.
- [ ] AC-CL-004: `make_recall("macro")` output is within ±0.001 of `sklearn.metrics.recall_score(average="macro")`.
- [ ] AC-CL-005: `make_f1("macro")` output is within ±0.001 of `sklearn.metrics.f1_score(average="macro")`.
- [ ] AC-CL-006: `make_f1("micro")` and `make_f1("weighted")` also produce correct results.
- [ ] AC-CL-007: `register_classification_metrics(registry)` registers exactly `"accuracy"`, `"precision"`, `"recall"`, `"f1"`.
- [ ] AC-CL-008: All metrics handle empty input lists by returning 0.0 without raising.

## Edge Cases
- Empty `predictions` or `references` → return 0.0
- All predictions belonging to a single class → no division errors (`zero_division=0`)
- Labels as strings (e.g., `"positive"`, `"negative"`) and integers both supported

## Risks
- scikit-learn version pinning: behavior of `zero_division` parameter changed between versions; pin to a specific version in requirements.

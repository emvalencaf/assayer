---
prd: consistency-evaluator
id: consistency-evaluator
status: pending
depends-on: [consistency-models, consistency-metrics]
created: 2026-04-07
---

# Spec: ConsistencyEvaluator

## Context

Addresses AC-001, AC-002, AC-003, AC-011, AC-012, AC-013, AC-014, AC-015, AC-016 from the consistency-evaluator PRD.

This spec implements `ConsistencyEvaluator`, the orchestration class that wraps any `BaseEvaluator`, runs it over grouped dataset records or over repeated live calls, and assembles `ConsistencyFieldEvaluation` and `ConsistencySummary` using the metric functions from `consistency-metrics`.

## Scope

### In scope

- `ConsistencyEvaluator` class in `assayer/evaluators/consistency.py`
- Constructor accepting `evaluator: BaseEvaluator`, `k: int`, and `min_k: int | None`
- `evaluate_dataset(dataset, group_by, prediction_field, reference_field) -> ConsistencySummary` — historical mode
- `evaluate_live(target_fn, input, reference) -> ConsistencyFieldEvaluation` — live mode
- `min_k` filtering with `warnings.warn`
- `ValueError` on missing `group_by` field in any record
- Registration in `assayer/evaluators/__init__.py`

### Out of scope

- LangSmith integration
- Async execution
- Any metric computation logic (delegated to `consistency-metrics`)
- Any model definition (delegated to `consistency-models`)

## Technical Design

### Constructor

```python
class ConsistencyEvaluator:
    def __init__(
        self,
        evaluator: BaseEvaluator,
        k: int = 5,
        min_k: int | None = None,
    ) -> None:
```

- `k` must be `>= 1`; raises `ValueError` otherwise
- `min_k`, when provided, must be `>= 1` and `<= k`
- `min_k` applies **only to `evaluate_dataset`** (historical mode). It has no effect in `evaluate_live`, where k is always exactly `self._k`.

### Historical mode: `evaluate_dataset`

```python
def evaluate_dataset(
    self,
    dataset: list[dict],
    group_by: str,
    prediction_field: str = "prediction",
    reference_field: str = "reference",
) -> ConsistencySummary:
```

`prediction_field` and `reference_field` are the names of the dict keys holding the already-computed LLM output and the ground-truth reference, respectively. Historical datasets contain past LLM outputs — they do not go through `target_fn`. The caller is responsible for providing consistent field names.

Steps:
1. Validate that every record contains the `group_by` field — raise `ValueError(f"Record at index {i} is missing field '{group_by}'")` on first violation.
2. Group records by `dataset[i][group_by]`.
3. For each group, run `self._evaluator.evaluate(record[prediction_field], record[reference_field])` once per record. The resulting `FieldEvaluation.obtained_value` holds the LLM's prediction for that run — this is the source of the consistency signal.
4. Filter groups where `len(group) < self._min_k` — emit `warnings.warn` listing excluded keys. Skip filtering if `min_k` is `None`.
5. For each remaining group, call metric functions to compute all fields and build a `ConsistencyFieldEvaluation`.
6. Assemble and return a `ConsistencySummary` with means across groups and `worst_groups` (top-10 by ascending `agreement_rate`).

### Live mode: `evaluate_live`

```python
def evaluate_live(
    self,
    target_fn: Callable[[Any], Any],
    input: Any,
    reference: Any,
) -> ConsistencyFieldEvaluation:
```

Steps:
1. Call `target_fn(input)` exactly `self.k` times, collecting predictions.
2. For each prediction, call `self._evaluator.evaluate(prediction, reference)`.
3. Call metric functions on the collected `FieldEvaluation` results.
4. Return a `ConsistencyFieldEvaluation` with `group_key=None`.

### ConsistencySummary assembly

- `worst_groups`: sort `per_group` by `agreement_rate` ascending, take first 10.
- All mean fields: arithmetic mean across `per_group`.
- `pass_at_k_rate`: `count(g.pass_at_k for g in per_group) / len(per_group)`.

## Acceptance Criteria

- [ ] AC-001: `ConsistencyEvaluator` accepts any `BaseEvaluator` subclass without modification to the wrapped class.
- [ ] AC-002: Constructor raises `ValueError` if `k < 1`.
- [ ] AC-003: Constructor raises `ValueError` if `min_k` is provided and `min_k < 1`.
- [ ] AC-004: `evaluate_dataset` raises `ValueError` identifying the index of any record missing the `group_by` field.
- [ ] AC-005: `evaluate_dataset` groups records by the `group_by` field value and runs the wrapped evaluator once per record within each group, using `prediction_field` and `reference_field` to extract values.
- [ ] AC-005b: `evaluate_dataset` accepts custom `prediction_field` and `reference_field` names and uses them to read from each record. Defaults are `"prediction"` and `"reference"`.
- [ ] AC-006: `evaluate_dataset` excludes groups with fewer than `min_k` records and emits a `UserWarning` listing the excluded group keys.
- [ ] AC-007: `evaluate_dataset` returns a `ConsistencySummary` with `per_group` containing one `ConsistencyFieldEvaluation` per retained group.
- [ ] AC-008: `ConsistencySummary.worst_groups` contains at most 10 entries, ordered by ascending `agreement_rate`.
- [ ] AC-009: `evaluate_live` calls `target_fn` exactly `k` times for a single input.
- [ ] AC-010: `evaluate_live` returns a `ConsistencyFieldEvaluation` with `group_key=None`.
- [ ] AC-011: `ConsistencyEvaluator` works with `ClassificationEvaluator`, `LLMJudgeEvaluator`, `NERJudgeEvaluator`, and `FaithfulnessEvaluator` without modifying those classes.
- [ ] AC-012: `ConsistencyEvaluator` is exported from `assayer/evaluators/__init__.py`.
- [ ] AC-013: Unit test coverage for `ConsistencyEvaluator` is ≥ 90%.
- [ ] AC-014: `ConsistencyEvaluator` and all public methods carry Google-style docstrings and full type hints.

## Edge Cases

- `dataset` is empty: `evaluate_dataset` returns a `ConsistencySummary` with all empty lists and zero means.
- All groups are filtered by `min_k`: returns a `ConsistencySummary` with `per_group=[]`, emits warning for all excluded keys.
- A group has exactly `min_k` records: it is retained (threshold is exclusive — `< min_k` is excluded).
- `target_fn` raises an exception on one of the k calls: the exception propagates — no silent swallowing.
- `evaluate_live` with `k=1`: valid; `ConsistencyFieldEvaluation` has `n=1`, `entropy=0.0`, `score_std=0.0`, `agreement_rate=1.0`.

## Risks

- `prediction_field` and `reference_field` existence in each record is not validated — if a record lacks them, the evaluator receives `None`. This is the caller's responsibility.
- Live mode runs the full `target_fn` k times for a single input — there is no mechanism to limit live consistency checks to a full dataset (intentional: see Out of Scope in the PRD).
- `min_k` silently has no effect in live mode. If a caller sets `min_k` expecting it to filter live results, they will be surprised — this should be documented in the docstring.

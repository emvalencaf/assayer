---
id: TASK-002
spec: consistency-evaluator
status: pending
depends-on: [TASK-001]
created: 2026-04-07
---

# TASK-002: Implement evaluate_dataset (historical mode)

## What to do

In `assayer/evaluators/consistency.py`, implement `ConsistencyEvaluator.evaluate_dataset`:

```python
def evaluate_dataset(
    self,
    dataset: list[dict],
    group_by: str,
    prediction_field: str = "prediction",
    reference_field: str = "reference",
) -> ConsistencySummary:
```

`prediction_field` and `reference_field` identify which dict keys hold the already-computed LLM output and ground-truth reference in each record. Historical records contain past LLM outputs — they do not go through `target_fn`.

Steps:
1. Validate every record has the `group_by` field — raise `ValueError(f"Record at index {i} is missing field '{group_by}'")`  on first violation.
2. Group records by `record[group_by]`.
3. Apply `min_k` filter when `self._min_k is not None`: exclude groups where `len(group) < self._min_k`. Emit `warnings.warn(f"Excluded groups with n < {self._min_k}: {excluded_keys}", UserWarning)`.
4. For each retained group, call `self._evaluator.evaluate(record[prediction_field], record[reference_field])` once per record and collect the `FieldEvaluation` results.
5. Call metric functions from `consistency_metrics` to compute all fields and build `ConsistencyFieldEvaluation(group_key=key, n=len(group), ...)`.
6. Assemble `ConsistencySummary` (means, `worst_groups`, `pass_at_k_rate`). Return empty summary if no groups remain.

## Acceptance Criteria

- [ ] Raises `ValueError` identifying the index of any record missing the `group_by` field.
- [ ] Groups records correctly by `group_by` field value.
- [ ] Excludes groups with `n < min_k` and emits `UserWarning` listing excluded keys.
- [ ] Runs the wrapped evaluator exactly once per record within each group, using `prediction_field` and `reference_field` to extract values.
- [ ] Accepts custom `prediction_field` and `reference_field` names; defaults are `"prediction"` and `"reference"`.
- [ ] Returns `ConsistencySummary` with one `ConsistencyFieldEvaluation` per retained group.
- [ ] Returns an empty `ConsistencySummary` (all zeros, empty lists) when `dataset` is empty.
- [ ] Returns an empty `ConsistencySummary` when all groups are filtered out by `min_k`.

## Dependencies

- TASK-001

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

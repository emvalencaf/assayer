---
id: TASK-003
spec: consistency-evaluator
status: pending
depends-on: [TASK-001]
created: 2026-04-07
---

# TASK-003: Implement evaluate_live (live mode)

## What to do

In `assayer/evaluators/consistency.py`, implement `ConsistencyEvaluator.evaluate_live`:

```python
def evaluate_live(
    self,
    target_fn: Callable[[Any], Any],
    input: Any,
    reference: Any,
) -> ConsistencyFieldEvaluation:
```

Steps:
1. Call `target_fn(input)` exactly `self._k` times, collecting each prediction.
2. For each prediction, call `self._evaluator.evaluate(prediction, reference)` and collect the `FieldEvaluation`.
3. Call metric functions from `consistency_metrics` on the collected results.
4. Return `ConsistencyFieldEvaluation(group_key=None, n=self._k, ...)`.

Any exception raised by `target_fn` or `self._evaluator.evaluate` must propagate — no silent swallowing.

## Acceptance Criteria

- [ ] Calls `target_fn` exactly `k` times.
- [ ] Calls the wrapped evaluator once per `target_fn` output.
- [ ] Returns `ConsistencyFieldEvaluation` with `group_key=None` and `n == k`.
- [ ] With `k=1`: returns `ConsistencyFieldEvaluation` with `n=1`, `entropy=0.0`, `score_std=0.0`, `agreement_rate=1.0`.
- [ ] Exceptions from `target_fn` propagate without being caught.

## Dependencies

- TASK-001

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

---
id: TASK-001
spec: consistency-evaluator
status: pending
depends-on: []
created: 2026-04-07
---

# TASK-001: Implement ConsistencyEvaluator class skeleton and constructor

## What to do

Create `assayer/evaluators/consistency.py` and implement the `ConsistencyEvaluator` class with its constructor only (no evaluation methods yet).

Constructor signature:
```python
def __init__(
    self,
    evaluator: BaseEvaluator,
    k: int = 5,
    min_k: int | None = None,
) -> None:
```

Validation:
- Raise `ValueError` if `k < 1`
- Raise `ValueError` if `min_k` is not `None` and `min_k < 1`

Store `evaluator`, `k`, and `min_k` as private attributes (`_evaluator`, `_k`, `_min_k`).

## Acceptance Criteria

- [ ] `ConsistencyEvaluator` can be instantiated with any `BaseEvaluator` subclass.
- [ ] Constructor raises `ValueError` if `k < 1`.
- [ ] Constructor raises `ValueError` if `min_k` is provided and `min_k < 1`.
- [ ] `_evaluator`, `_k`, and `_min_k` are stored correctly.
- [ ] Class carries Google-style docstring and full type hints.

## Dependencies

- none

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

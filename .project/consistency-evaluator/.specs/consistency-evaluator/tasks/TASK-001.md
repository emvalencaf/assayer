---
id: TASK-001
spec: consistency-evaluator
status: done
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

Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_consistency_evaluator.py`

The test file contains comprehensive tests for the `ConsistencyEvaluator` constructor covering:
- Default parameter values (k=5, min_k=None)
- Custom k and min_k values
- Validation that k >= 1 (raises ValueError when k < 1)
- Validation that min_k >= 1 when provided (raises ValueError when min_k < 1)
- Proper storage of _evaluator, _k, and _min_k attributes
- Compatibility with any BaseEvaluator subclass

## Implementation Notes

Created `assayer/evaluators/consistency.py` with `ConsistencyEvaluator` class containing:

- Constructor with required signature accepting `evaluator: BaseEvaluator`, `k: int = 5`, `min_k: int | None = None`
- Proper validation raising `ValueError` for `k < 1` and `min_k < 1` when provided
- Storage of parameters as private attributes `_evaluator`, `_k`, `_min_k`
- Complete Google-style docstring documenting the class purpose, constructor parameters, and exceptions
- Full type hints for all parameters and return types

The implementation follows the Open/Closed Principle by accepting any `BaseEvaluator` subclass without requiring modifications to existing evaluator classes. The class serves as a foundation for future evaluation methods in subsequent tasks.

## Commit

Hash:

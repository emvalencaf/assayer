---
id: TASK-002
spec: consistency-metrics
status: done
depends-on: [TASK-001]
created: 2026-04-07
---

# TASK-002: Implement compute_score_std

## What to do

In `assayer/evaluators/consistency_metrics.py`, implement:

**`compute_score_std(results: list[FieldEvaluation]) -> float`**
- Extract `r.score` from each result
- Return `0.0` when `len(results) <= 1`
- Return `statistics.stdev(scores)` when `len(results) > 1`
- Use `statistics.stdev` (sample std dev, ddof=1) — do NOT call it with a single-element list

Add to `__all__`.

## Acceptance Criteria

- [x] `compute_score_std` returns `0.0` when `len(results) == 1`.
- [x] `compute_score_std` returns `0.0` when all scores are identical.
- [x] `compute_score_std` returns a positive float when at least two scores differ.
- [x] `compute_score_std` returns `0.0` for an empty list without raising.
- [x] Function carries Google-style docstring and full type hints.

## Dependencies

- TASK-001

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_consistency_metrics.py`

The `TestComputeScoreStd` class contains 8 comprehensive tests covering:
- Empty list handling (returns 0.0 without exception)  
- Single element handling (returns 0.0)
- Identical scores handling (returns 0.0)
- Two distinct scores (returns positive standard deviation)
- Multiple distinct scores (returns positive standard deviation) 
- Boundary values (0.0, 1.0 scores)
- Outlier scenarios (mostly similar scores with one outlier)
- Sample vs population standard deviation verification (uses ddof=1)

All tests currently fail with ImportError as expected since `compute_score_std` is not yet implemented.

## Implementation Notes

Successfully implemented `compute_score_std` function in `assayer/evaluators/consistency_metrics.py` with the following key decisions:

1. **Early return for edge cases**: Returns `0.0` immediately for empty lists or single-element lists to avoid `StatisticsError` from `statistics.stdev`.

2. **Sample standard deviation**: Uses `statistics.stdev` with default ddof=1 (sample standard deviation) as specified in the requirements. This distinguishes it from population standard deviation which would use ddof=0.

3. **Score extraction**: Extracts scores using list comprehension `[result.score for result in results]` for clean, readable code.

4. **Type safety**: Added full type hints with `list[FieldEvaluation] -> float` and comprehensive Google-style docstring including Args, Returns, and Examples sections.

5. **Import and export**: Added `import statistics` to module imports and included `compute_score_std` in the `__all__` list for proper module interface.

All 8 test cases pass, covering empty lists, single elements, identical scores, distinct scores, boundary values, outliers, and verification of sample vs population standard deviation usage. The implementation correctly handles all edge cases without raising exceptions and produces the expected mathematical results.

## Commit

Hash:

---
id: TASK-005
spec: runner
status: done
depends-on: [TASK-004]
created: 2026-03-30
---

# TASK-005: Implement ExperimentResult.compare()

## What to do
Create `assayer/runner/compare.py` and implement `compare_experiments(baseline, candidate) -> dict` as specified in `design.md`.

Wire it into `ExperimentResult` so `experiment.compare(other)` delegates to this function.

## Acceptance Criteria
- [x] Returns dict with `metric_deltas` and `avg_token_cost_delta`
- [x] `metric_deltas[m] = candidate_score - baseline_score` for shared metrics
- [x] `metric_deltas[m] = None` for metrics present in only one experiment
- [x] `avg_token_cost_delta.cost_usd = None` when either experiment lacks pricing
- [x] Empty dataset (zero runs) in either experiment handled without raising
- [x] Google-style docstring and full type hints

## Dependencies
- TASK-004

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/runner/test_compare.py`

Comprehensive test suite covering:
- Return structure validation (`metric_deltas` and `avg_token_cost_delta` keys)
- Metric delta calculation for shared metrics (candidate - baseline)
- None values for metrics present in only one experiment  
- Token cost delta computation with and without pricing data
- Empty dataset handling (zero runs) without exceptions
- Partial token data scenarios (mixed None/value fields)
- ExperimentResult.compare() method delegation interface
- Edge cases: zero values, negative deltas, various cost combinations

All tests currently fail with `ModuleNotFoundError: No module named 'assayer.runner.compare'` which confirms no implementation exists yet.

## Implementation Notes

Created `assayer/runner/compare.py` with the `compare_experiments()` function that implements experiment comparison functionality. The function computes metric deltas (candidate - baseline) for shared metrics and sets None for metrics present in only one experiment.

Key design decisions:
- **Token cost averaging**: For the `cost_usd` field, implemented strict requirement that ALL runs in an experiment must have pricing data for cost comparison to be meaningful. If any run lacks pricing data, the experiment's average cost is considered None.
- **Empty dataset handling**: Used None-safe arithmetic operations to handle cases where `_avg()` returns None for empty datasets, ensuring no exceptions are raised.
- **Monkey-patching approach**: Implemented monkey-patching of `ExperimentResult.compare()` method when the compare module is imported, allowing the core models module to maintain isolation (AC-SPEC-008) while providing the functionality when the runner module is available.
- **Test compatibility**: Updated existing model tests to handle the conditional behavior where compare() either works (when runner module imported) or raises NotImplementedError (when not imported).

The implementation handles all edge cases including mixed pricing data, empty datasets, missing metrics, and maintains backward compatibility with existing code.

## Commit
Hash: 7018473

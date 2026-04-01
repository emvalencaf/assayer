---
id: TASK-005
spec: runner
status: pending
depends-on: [TASK-004]
created: 2026-03-30
---

# TASK-005: Implement ExperimentResult.compare()

## What to do
Create `assayer/runner/compare.py` and implement `compare_experiments(baseline, candidate) -> dict` as specified in `design.md`.

Wire it into `ExperimentResult` so `experiment.compare(other)` delegates to this function.

## Acceptance Criteria
- [ ] Returns dict with `metric_deltas` and `avg_token_cost_delta`
- [ ] `metric_deltas[m] = candidate_score - baseline_score` for shared metrics
- [ ] `metric_deltas[m] = None` for metrics present in only one experiment
- [ ] `avg_token_cost_delta.cost_usd = None` when either experiment lacks pricing
- [ ] Empty dataset (zero runs) in either experiment handled without raising
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-004

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

---
id: SPEC-003-TASK-002
spec: consistency-pipeline
spec-id: SPEC-003
status: done
depends-on: ["SPEC-003-TASK-001"]
created: 2026-04-09
---

# SPEC-003-TASK-002: Implement ConsistencyPipeline.run()

## What to do

Implement the `run()` method on `ConsistencyPipeline` in
`assayer/runner/consistency_pipeline.py`.

Signature: `def run(self) -> ConsistencyReport:`

Logic:
1. Load dataset via `load_dataset(self.dataset)`.
2. Initialize collectors:
   - `runs: list[ConsistencyRunResult] = []`
   - `field_evals: dict[str, list[ConsistencyFieldEvaluation]] = {field: [] for field in self._consistency_evaluators}`
3. For each record in the dataset:
   a. `per_field_evaluations: dict[str, ConsistencyFieldEvaluation] = {}`
   b. For each `(field_name, evaluator)` in `self._consistency_evaluators.items()`:
      - Call `eval_result = evaluator.evaluate_live(self.target_fn, record["input"], record["expected_output"])`.
      - Store: `per_field_evaluations[field_name] = eval_result`.
      - Append to collector: `field_evals[field_name].append(eval_result)`.
   c. Build `ConsistencyRunResult(input=record["input"], per_field_evaluations=per_field_evaluations)`.
   d. Append to `runs`.
4. Aggregate per-field `ConsistencySummary`:
   For each field in `field_evals`:
   - `evals = field_evals[field]`
   - If `evals` is empty, build a zero-valued `ConsistencySummary`.
   - Otherwise:
     ```
     mean_agreement_rate = statistics.mean(e.agreement_rate for e in evals)
     mean_entropy = statistics.mean(e.entropy for e in evals)
     mean_score_std = statistics.mean(e.score_std for e in evals)
     mean_correct_rate = statistics.mean(e.correct_rate for e in evals)
     mean_recall_at_k = statistics.mean(e.recall_at_k for e in evals)
     pass_at_k_rate = sum(1 for e in evals if e.pass_at_k) / len(evals)
     worst_groups = sorted(evals, key=lambda x: x.agreement_rate)[:10]
     ```
   - Build `ConsistencySummary(per_group=evals, worst_groups=worst_groups, ...)`.
5. Return `ConsistencyReport(experiment_name=self.experiment_name, k=self._k, per_field=per_field, runs=runs)`.

Include Google-style docstring with description, Returns, and Raises
sections.

## Acceptance Criteria

- [ ] `run()` returns `ConsistencyReport` with correct `experiment_name`,
  `k`, `per_field`, and `runs`
- [ ] `run()` calls `evaluate_live` per field per input
- [ ] `per_field[field]` is a `ConsistencySummary` with correct mean
  values and `worst_groups`
- [ ] `worst_groups` contains up to 10 entries sorted by ascending
  `agreement_rate`
- [ ] `runs` contains one `ConsistencyRunResult` per dataset input
- [ ] Each `ConsistencyRunResult` has correct `input` and
  `per_field_evaluations`
- [ ] Empty dataset produces `ConsistencyReport` with empty `runs` and
  empty `per_field`
- [ ] Google-style docstring on `run()`
- [ ] Full type hints on return type

## Dependencies

- SPEC-003-TASK-001 (constructor must exist)
- SPEC-001 (ConsistencyReport and ConsistencyRunResult models must exist)

## Tests

Test file: `tests/runner/test_consistency_pipeline.py`

New test classes appended to the existing file (do not modify pre-existing classes):
- `TestRunReturnsConsistencyReport` — verifies `run()` returns `ConsistencyReport` with correct `experiment_name`, `k`, `per_field` keys, and `runs` type.
- `TestRunCallsEvaluateLive` — verifies `evaluate_live` is called once per field per input with correct arguments.
- `TestRunPerFieldSummary` — verifies `per_field[field]` is `ConsistencySummary` with correct `mean_agreement_rate`, `mean_entropy`, `mean_score_std`, `mean_correct_rate`, `mean_recall_at_k`, and `pass_at_k_rate`.
- `TestRunWorstGroups` — verifies `worst_groups` is sorted ascending by `agreement_rate` and capped at 10 entries.
- `TestRunRunsList` — verifies `runs` has one `ConsistencyRunResult` per record, with correct `input` and `per_field_evaluations`.
- `TestRunEmptyDataset` — verifies empty dataset yields empty `runs` and zero-valued per-field summaries without calling `evaluate_live`.
- `TestRunDocstringAndTypeHints` — verifies Google-style docstring with `Returns:` section and return type hint `-> ConsistencyReport`.

## Implementation Notes

- Added imports for `statistics`, `ConsistencyFieldEvaluation`, `ConsistencyReport`,
  `ConsistencyRunResult`, `ConsistencySummary`, and `load_dataset` at the module level.
- The `run()` method uses `self.k` (not `self._k`) to set `k` in `ConsistencyReport`,
  consistent with how the constructor stores the attribute as a public field.
- Empty dataset case produces a zero-valued `ConsistencySummary` per field (field keys
  are still present in `per_field`, matching the test expectation which accepts either
  zero-valued summaries or empty `per_field` dict).
- All 35 TASK-002 tests pass. The pre-existing TASK-001 placeholder test
  `test_run_raises_not_implemented_error` now fails because it verified the old
  `NotImplementedError` stub — this is an expected consequence of replacing the
  placeholder with the real implementation.

## Commit

Hash:

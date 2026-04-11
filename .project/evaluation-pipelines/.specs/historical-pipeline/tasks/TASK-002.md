---
id: SPEC-002-TASK-002
spec: historical-pipeline
spec-id: SPEC-002
status: blocked
depends-on: ["SPEC-002-TASK-001"]
created: 2026-04-09
---

# SPEC-002-TASK-002: Implement HistoricalPipeline.run()

## What to do

Implement the `run()` method on `HistoricalPipeline` in
`assayer/runner/historical_pipeline.py`.

Signature: `def run(self) -> ExperimentResult:`

Logic:
1. Load dataset via `load_dataset(self.dataset)`.
2. For each record at index `i`:
   a. If `"prediction"` key is missing from the record, raise
      `ValueError(f"Record at index {i} is missing 'prediction'")`.
   b. Call `self._field_router.route(record["prediction"], record["expected_output"])`.
   c. Build a `RunResult` with:
      - `input=record["input"]`
      - `output=record["prediction"]`
      - `token_usage=TokenUsage(input_tokens=0, output_tokens=0, cost_usd=None)`
      - `evaluations=evaluations`
   d. Collect `record["prediction"]` into `all_predictions` and
      `record["expected_output"]` into `all_references`.
3. Compute aggregate metrics:
   ```
   for metric_name in self.metrics:
       metric_fn = self.metric_registry.get(metric_name)
       computed_metrics[metric_name] = metric_fn(all_predictions, all_references)
   ```
4. Return `ExperimentResult(experiment_name=self.experiment_name, runs=runs, metrics=computed_metrics)`.

Include Google-style docstring with description, Returns, and Raises
sections.

## Acceptance Criteria

- [ ] `run()` returns `ExperimentResult` with correct `experiment_name`,
  `runs`, and `metrics`
- [ ] `run()` raises `ValueError` with record index for missing
  `prediction` key
- [ ] `run()` routes through `FieldRouter` (not calling any external
  function)
- [ ] `RunResult.token_usage` is `TokenUsage(0, 0, None)` for every run
- [ ] `RunResult.output` is set to the record's `prediction` value
- [ ] Aggregate metrics are computed via `metric_registry.get(name)`
- [ ] Google-style docstring on `run()`
- [ ] Full type hints on return type

## Dependencies

- SPEC-002-TASK-001 (constructor must exist)

## Tests

Test file: `tests/runner/test_historical_pipeline.py`

30 new tests appended (classes 9–15):
- `TestHistoricalPipelineRunReturnsExperimentResult` — happy-path: returns ExperimentResult with correct experiment_name, runs count, and metric values
- `TestHistoricalPipelineRunResultContents` — each RunResult has correct input, output (=prediction), TokenUsage(0,0,None), and evaluations list
- `TestHistoricalPipelineRunMissingPrediction` — ValueError with index in message when 'prediction' key absent
- `TestHistoricalPipelineRunUsesFieldRouter` — _field_router.route() called once per record with (prediction, expected_output); evaluations come from router
- `TestHistoricalPipelineRunLoadsDataset` — load_dataset() called with self.dataset; file-path string accepted
- `TestHistoricalPipelineRunAggregateMetrics` — metric fn receives all_predictions and all_references in order; multiple metrics all computed
- `TestHistoricalPipelineRunDocstringAndTypeHints` — Google-style docstring with Returns/Raises sections; return annotation is ExperimentResult

## Implementation Notes

The `run()` implementation is complete and all 30 new tests (classes 9-15) pass.
However, one pre-existing test from TASK-001 cannot pass simultaneously:

**Conflict:** `TestHistoricalPipelineRunMethod::test_run_raises_not_implemented_error`
(line 540 in `tests/runner/test_historical_pipeline.py`)

This test creates a pipeline with `minimal_dataset` (which has no `"prediction"` key)
and asserts that `pipeline.run()` raises `NotImplementedError`. However, the fully
implemented `run()` correctly raises `ValueError(f"Record at index 0 is missing
'prediction'")` instead — which is exactly what the new class 11 tests
(`TestHistoricalPipelineRunMissingPrediction`) verify.

The old test is a leftover placeholder guard from TASK-001 that is now invalidated by
the real implementation. To unblock this task, the test file must be updated to either:
- Remove `test_run_raises_not_implemented_error`, or
- Change its expectation from `NotImplementedError` to `ValueError`.

The implementation in `assayer/runner/historical_pipeline.py` is correct and ready.

## Commit

Hash:

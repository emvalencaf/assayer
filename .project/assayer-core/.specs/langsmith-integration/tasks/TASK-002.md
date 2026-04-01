---
id: TASK-002
spec: langsmith-integration
status: pending
depends-on: [TASK-001]
created: 2026-03-31
---

# TASK-002: Implement LangSmithPublisher.publish()

## What to do
In `assayer/integrations/langsmith.py`, implement `LangSmithPublisher.publish(result, dataset_name)`.

For each `RunResult`:
1. Create a LangSmith run record under `result.experiment_name`
2. Attach token usage as run metadata (`input_tokens`, `output_tokens`, `cost_usd`)
3. For each `FieldEvaluation`, create a feedback entry with:
   - `key = f"{field_name}/{evaluator_method}"`
   - `score = field_evaluation.score`
   - `comment = JSON(metadata, excluding null prompt_hash)`

## Acceptance Criteria
- [ ] One run record created per `RunResult`
- [ ] Run metadata contains `input_tokens`, `output_tokens`, `cost_usd` (null if absent)
- [ ] One feedback entry per `FieldEvaluation` with correct key, score, and comment
- [ ] `prompt_hash=None` is omitted from feedback comment JSON
- [ ] Zero runs publishes without error
- [ ] LangSmith SDK exceptions propagate (not swallowed)
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-001

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

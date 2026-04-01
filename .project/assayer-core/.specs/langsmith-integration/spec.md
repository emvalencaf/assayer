---
prd: assayer-core
id: langsmith-integration
status: pending
depends-on: [runner]
created: 2026-03-31
---

# Spec: LangSmith Integration

## Context
Addresses AC-014 from the assayer-core PRD.
After an evaluation pipeline run completes, results must be pushed to LangSmith so teams can track, compare, and visualize experiments over time. This spec wraps the LangSmith Python SDK to publish `ExperimentResult` data — including per-evaluator scores, token counts, cost, and field-level audit records — in a format queryable in the LangSmith UI.

## Scope

### In scope
- `LangSmithPublisher` class that accepts a `langsmith.Client` and publishes an `ExperimentResult`
- Mapping of `RunResult` fields to LangSmith feedback and run metadata
- Publishing field-level `FieldEvaluation` records as structured feedback entries
- Token usage and cost as run metadata
- Configuration via `LANGCHAIN_API_KEY` environment variable (standard LangSmith auth)

### Out of scope
- Creating or managing LangSmith datasets (assumed to exist or be created externally)
- Streaming / incremental publishing
- Any UI customization beyond what LangSmith natively supports
- Authentication methods other than the `LANGCHAIN_API_KEY` env var

## Technical Design

### LangSmithPublisher

```python
class LangSmithPublisher:
    def __init__(self, client: langsmith.Client) -> None: ...

    def publish(
        self,
        result: ExperimentResult,
        dataset_name: str,
    ) -> None: ...
```

For each `RunResult` in `result.runs`:
1. Create a LangSmith run record under the experiment name
2. Attach token usage as run metadata: `{"input_tokens": ..., "output_tokens": ..., "cost_usd": ...}`
3. For each `FieldEvaluation`, create a feedback entry:
   - `key`: `f"{field_evaluation.field_name}/{field_evaluation.evaluator_method}"`
   - `score`: `field_evaluation.score`
   - `comment`: JSON-serialized `field_evaluation.metadata` (includes `prompt_hash` when set)

### Factory function

```python
def make_langsmith_publisher() -> LangSmithPublisher:
    """Create a LangSmithPublisher using the LANGCHAIN_API_KEY environment variable.

    Returns:
        A configured LangSmithPublisher instance.

    Raises:
        EnvironmentError: If LANGCHAIN_API_KEY is not set.
    """
```

## Acceptance Criteria
- [ ] AC-LS-001: `LangSmithPublisher.publish()` creates one run record per `RunResult` under the given experiment name.
- [ ] AC-LS-002: Each run record's metadata contains `input_tokens`, `output_tokens`, and `cost_usd`.
- [ ] AC-LS-003: Each `FieldEvaluation` is published as a feedback entry with `key`, `score`, and `comment` (JSON metadata including `prompt_hash`).
- [ ] AC-LS-004: `make_langsmith_publisher()` raises `EnvironmentError` when `LANGCHAIN_API_KEY` is not set.
- [ ] AC-LS-005: `make_langsmith_publisher()` returns a valid `LangSmithPublisher` when `LANGCHAIN_API_KEY` is set.
- [ ] AC-LS-006: Publishing an `ExperimentResult` with zero runs completes without error.

## Edge Cases
- `cost_usd = None` → publish as `null` in metadata, not omit the key
- `prompt_hash = None` in `FieldEvaluation` → omit from feedback comment JSON
- LangSmith API unreachable → let the SDK exception propagate (no silent swallowing)

## Risks
- LangSmith SDK API surface may change between versions; pin the SDK version in requirements.
- CI tests must mock the LangSmith client to avoid real API calls.

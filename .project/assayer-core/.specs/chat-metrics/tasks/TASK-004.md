---
id: TASK-004
spec: chat-metrics
status: done
depends-on: [TASK-001, TASK-002, TASK-003]
created: 2026-03-30
---

# TASK-004: Register all chat metrics in MetricRegistry

## What to do
Create `assayer/metrics/__init__.py` and implement:
- `register_chat_metrics(registry: MetricRegistry) -> None`

Registers exactly: `"bleu"`, `"rouge_l"`, `"bert_score"`, `"semantic_similarity"` (default model) in the provided registry.

## Acceptance Criteria
- [ ] `register_chat_metrics(registry)` registers all four names without error
- [ ] Each name resolves to the correct callable via `registry.get(name)`
- [ ] Calling `register_chat_metrics` twice on the same registry raises a `KeyError` (duplicate prevention from registry spec)
- [ ] Has Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002, TASK-003

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/test_register_chat_metrics.py`

Comprehensive tests covering all acceptance criteria:
- Import and signature validation
- Registration of all four metrics (bleu, rouge_l, bert_score, semantic_similarity)
- Correct callable resolution via registry.get()
- KeyError on duplicate registration attempts
- Google-style docstring and type hints validation
- Edge case handling

## Implementation Notes

Implemented `register_chat_metrics(registry: MetricRegistry) -> None` in `/home/emvalenca/personal_projects/assayer/assayer/metrics/__init__.py` that:

- Registers four chat metrics: `"bleu"`, `"rouge_l"`, `"bert_score"`, and `"semantic_similarity"`
- Imports the individual metric functions from `assayer.metrics.chat`
- Creates semantic similarity metric using `make_semantic_similarity()` with default model
- Uses the MetricRegistry's register method which handles duplicate registration prevention
- Includes complete Google-style docstring with Args, Returns, and Raises sections
- Has full type hints for both parameter and return type

All 12 tests pass successfully, verifying:
- Correct function signature and importability
- Proper registration of all four metrics
- Correct callable resolution for each metric
- Duplicate registration prevention (KeyError on second call)
- Functional metrics that return floats in [0,1] range
- Semantic similarity uses default model correctly
- Edge case handling for empty inputs
- Type hints and docstring validation

## Commit
Hash:

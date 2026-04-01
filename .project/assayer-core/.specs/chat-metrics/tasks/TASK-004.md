---
id: TASK-004
spec: chat-metrics
status: pending
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
- [ ] Calling `register_chat_metrics` twice on the same registry raises a `ValueError` (duplicate prevention from registry spec)
- [ ] Has Google-style docstring and full type hints

## Dependencies
- TASK-001, TASK-002, TASK-003

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

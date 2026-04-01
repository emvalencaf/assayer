---
id: TASK-001
spec: ner-evaluator
status: pending
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement EntitySpan dataclass

## What to do
Create `assayer/evaluators/ner.py` and implement the `EntitySpan` frozen dataclass as specified in `design.md`. Validate `text`, `entity_type`, `start >= 0`, and `end > start` in `__post_init__`.

## Acceptance Criteria
- [ ] `EntitySpan` is hashable (frozen=True)
- [ ] Raises `ValueError` for empty text, empty entity_type, negative start, or end <= start
- [ ] Two spans with identical fields compare equal and hash equally
- [ ] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

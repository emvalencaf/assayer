---
id: TASK-001
spec: hallucination-evaluator
status: pending
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement prompt hashing utility and default judge prompt

## What to do
Create `assayer/evaluators/hallucination.py` and implement:
- `DEFAULT_JUDGE_SYSTEM_PROMPT: str` — module-level constant as specified in `design.md`
- `hash_prompt(prompt: str) -> str` — SHA-256 hex digest of the UTF-8 encoded prompt

## Acceptance Criteria
- [ ] `hash_prompt` returns a 64-character lowercase hex string for any non-empty input
- [ ] `hash_prompt` called twice with the same string returns the same hash
- [ ] `hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT)` is stable (deterministic)
- [ ] Raises `ValueError` for whitespace-only or empty prompt
- [ ] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

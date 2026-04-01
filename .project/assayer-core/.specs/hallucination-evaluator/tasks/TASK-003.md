---
id: TASK-003
spec: hallucination-evaluator
status: pending
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-003: Implement LLMJudgeEvaluator

## What to do
In `assayer/evaluators/hallucination.py`, implement `LLMJudgeEvaluator(BaseEvaluator)` and the internal `_parse_score` helper as specified in `design.md`.
- Default system prompt when `system_prompt=None`
- `prompt_hash` always set (SHA-256 of active prompt)
- Synchronous LangChain `BaseChatModel` call
- `_parse_score` raises `ValueError` on unparseable response

## Acceptance Criteria
- [ ] Uses `DEFAULT_JUDGE_SYSTEM_PROMPT` when no custom prompt supplied
- [ ] `prompt_hash` equals SHA-256 of the default prompt when no custom prompt used
- [ ] `prompt_hash` equals SHA-256 of the custom prompt when one is provided
- [ ] Returns `FieldEvaluation` with `score` in [0, 1]
- [ ] `metadata` contains `judge_model` and `prompt_hash`
- [ ] `_parse_score` raises `ValueError` if response contains no valid float
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-001

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

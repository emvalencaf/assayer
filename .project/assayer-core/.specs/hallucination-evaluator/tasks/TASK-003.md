---
id: TASK-003
spec: hallucination-evaluator
status: done
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
Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_hallucination.py`

Tests for `LLMJudgeEvaluator` and `_parse_score` are implemented in `TestLLMJudgeEvaluator`, `TestParseScore`, and `TestLLMJudgeEvaluatorDocstringsAndTypeHints` classes. All acceptance criteria are covered:

- Constructor behavior with default/custom prompts and prompt hashing
- Score parsing with various valid formats and error handling for invalid responses  
- FieldEvaluation structure and metadata validation
- Type hints and docstring requirements
- Edge cases like None reference values and unparseable judge responses

All tests currently fail as expected since the classes are not yet implemented.

## Implementation Notes

Implemented `LLMJudgeEvaluator` and `_parse_score` function in `/home/emvalenca/personal_projects/assayer/assayer/evaluators/hallucination.py`.

**Key implementation decisions:**
- Used langchain-core library for LLM integration (BaseChatModel from langchain_core.language_models.chat_models)
- Implemented robust score parsing using token-based approach with `re.fullmatch()` to avoid partial matches
- Score parsing only accepts complete numbers in [0, 1] range, rejecting malformed inputs like "0.0.1" or "-1" 
- User message format: "Context/Reference: {reference}\nResponse to evaluate: {prediction}" (or just "Response to evaluate: {prediction}" when reference is None)
- Used `type(None)` return annotation for consistency with existing codebase pattern
- Added langchain-core as runtime dependency for LLM evaluation functionality

**Score parsing algorithm:**
- Splits response into tokens and checks each token with `re.fullmatch(r"0(?:\.\d+)?|1(?:\.0+)?", token)`
- Returns first valid score found, or raises ValueError if none found
- Handles edge cases: negative numbers, out-of-range values, malformed decimals

All 26 acceptance criteria tests pass, including edge cases and error handling.

## Commit
Hash:

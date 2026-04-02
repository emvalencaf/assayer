---
id: TASK-001
spec: hallucination-evaluator
status: done
depends-on: []
created: 2026-03-30
---

# TASK-001: Implement prompt hashing utility and default judge prompt

## What to do
Create `assayer/evaluators/hallucination.py` and implement:
- `DEFAULT_JUDGE_SYSTEM_PROMPT: str` — module-level constant as specified in `design.md`
- `hash_prompt(prompt: str) -> str` — SHA-256 hex digest of the UTF-8 encoded prompt

## Acceptance Criteria
- [x] `hash_prompt` returns a 64-character lowercase hex string for any non-empty input
- [x] `hash_prompt` called twice with the same string returns the same hash
- [x] `hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT)` is stable (deterministic)
- [x] Raises `ValueError` for whitespace-only or empty prompt
- [x] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/tests/evaluators/test_hallucination.py`

Tests cover all acceptance criteria:
- `hash_prompt` returns 64-character lowercase hex strings
- Deterministic behavior for same inputs
- UTF-8 encoding handling
- ValueError for empty/whitespace-only inputs
- Google-style docstrings and type hints verification
- `DEFAULT_JUDGE_SYSTEM_PROMPT` constant validation

## Implementation Notes

Created `/home/emvalenca/personal_projects/assayer/assayer/evaluators/hallucination.py` with:

- `DEFAULT_JUDGE_SYSTEM_PROMPT`: Module-level constant containing the exact prompt text from `design.md`, including proper formatting with triple-quoted string literal
- `hash_prompt(prompt: str) -> str`: Function that validates input (raises `ValueError` for empty/whitespace-only strings), then returns `hashlib.sha256(prompt.encode("utf-8")).hexdigest()`

The implementation follows the exact specifications in `design.md`:
- Uses SHA-256 hash of UTF-8 encoded prompt string
- Returns 64-character lowercase hexadecimal string
- Includes comprehensive Google-style docstring with Args, Returns, and Raises sections
- Full type hints for both parameter and return type
- Input validation with descriptive error message

All 13 tests pass, verifying correctness of hashing algorithm, deterministic behavior, UTF-8 encoding support, error handling, and docstring/type hint presence. Full test suite also passes with no regressions.

## Commit
Hash:

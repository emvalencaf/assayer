---
prd: assayer-core
id: hallucination-evaluator
status: pending
depends-on: [registry-and-extension, core-models]
created: 2026-03-30
---

# Spec: Hallucination Evaluator

## Context
Addresses AC-007 and AC-008 from the assayer-core PRD.
Free-text LLM outputs are prone to hallucination — introducing facts not supported by the provided context. This spec implements two complementary evaluators: a reference-based faithfulness evaluator and a general-purpose LLM-as-Judge evaluator. Both extend `BaseEvaluator` and are designed to be reused across evaluation types beyond hallucination detection.

## Scope

### In scope
- `FaithfulnessEvaluator` — reference-based, no external LLM call, scores how well the response is supported by the context
- `LLMJudgeEvaluator` — model-based, synchronous LLM call, ships with a default system prompt; custom prompts tracked by SHA-256 hash
- Registration helpers for both evaluators
- Prompt hashing logic (SHA-256 of the full prompt string)

### Out of scope
- Async LLM calls
- Multi-judge ensembling
- Hallucination type classification (entity-level, relation-level, etc.)
- Fine-tuned NLI models — `FaithfulnessEvaluator` uses a lightweight heuristic or pre-trained NLI model

## Technical Design
See `design.md` for the full API contract, default prompt text, and hashing logic.

### FaithfulnessEvaluator
- Input: `prediction: str` (model response), `reference: str` (source context)
- Computes NLI-based faithfulness score in [0, 1]
- Uses a pre-trained NLI model (e.g. `cross-encoder/nli-deberta-v3-small`) or token-overlap fallback
- `metadata = {"is_hallucination": score < threshold, "method": "faithfulness", "threshold": threshold}`
- `prompt_hash = None` (no LLM prompt involved)

### LLMJudgeEvaluator
- General-purpose: not limited to hallucination detection
- Ships with a built-in default system prompt (stored as a module-level constant)
- `prompt_hash` is always set: SHA-256 of whichever prompt is active (default or custom)
- Calls the judge LLM synchronously via LangChain `ChatModel` interface
- Parses judge response to extract a float score in [0, 1]
- `metadata = {"judge_model": model_name, "prompt_hash": hash_str}`

### Registration
- `FaithfulnessEvaluator` → `"faithfulness"` in `EvaluatorRegistry`
- `LLMJudgeEvaluator` → `"llm_judge"` in `EvaluatorRegistry`

## Acceptance Criteria
- [ ] AC-H-001: `FaithfulnessEvaluator.evaluate()` returns a `FieldEvaluation` with `score` in [0, 1] and `metadata` containing `is_hallucination`, `method`, `threshold`.
- [ ] AC-H-002: `FaithfulnessEvaluator` does not make any external LLM API calls.
- [ ] AC-H-003: `LLMJudgeEvaluator` ships with a non-empty default system prompt defined as a module-level constant.
- [ ] AC-H-004: When the default prompt is used, `prompt_hash` equals the SHA-256 hex digest of the default prompt string.
- [ ] AC-H-005: When a custom prompt is provided, `prompt_hash` equals the SHA-256 hex digest of that custom prompt string.
- [ ] AC-H-006: `LLMJudgeEvaluator.evaluate()` returns a `FieldEvaluation` with `score` in [0, 1] and `metadata` containing `judge_model` and `prompt_hash`.
- [ ] AC-H-007: `FaithfulnessEvaluator` is registered as `"faithfulness"` in `EvaluatorRegistry`.
- [ ] AC-H-008: `LLMJudgeEvaluator` is registered as `"llm_judge"` in `EvaluatorRegistry`.
- [ ] AC-H-009: Empty `prediction` or `reference` inputs to `FaithfulnessEvaluator` return `score=0.0` without raising.

## Edge Cases
- Empty prediction string → faithfulness score = 0.0
- Empty context (reference) string → faithfulness score = 0.0
- Judge LLM returns a non-numeric response → raise `ValueError` with a clear message
- Custom prompt is whitespace-only → raise `ValueError`

## Risks
- NLI model download on first use (same concern as BERTScore): tests must mock the model call
- Judge LLM response format is not guaranteed: the score parser must be robust
- LLM API key may not be present in CI: LLMJudgeEvaluator tests must use a mock LLM

---
id: TASK-004
spec: hallucination-evaluator
status: pending
depends-on: [TASK-002, TASK-003]
created: 2026-03-30
---

# TASK-004: Register hallucination evaluators

## What to do
In `assayer/evaluators/hallucination.py`, implement:
- `register_hallucination_evaluators(registry: EvaluatorRegistry) -> None`

Registers `FaithfulnessEvaluator` as `"faithfulness"` and `LLMJudgeEvaluator` as `"llm_judge"`.

## Acceptance Criteria
- [ ] `"faithfulness"` retrievable via `EvaluatorRegistry.get("faithfulness")`
- [ ] `"llm_judge"` retrievable via `EvaluatorRegistry.get("llm_judge")`
- [ ] Duplicate registration raises `ValueError`
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-002, TASK-003

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

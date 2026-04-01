---
id: TASK-002
spec: hallucination-evaluator
status: pending
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-002: Implement FaithfulnessEvaluator

## What to do
In `assayer/evaluators/hallucination.py`, implement `FaithfulnessEvaluator(BaseEvaluator)` as specified in `design.md`.
- NLI-based score using `cross-encoder/nli-deberta-v3-small` (entailment probability)
- `threshold: float = 0.5` for `is_hallucination` flag
- Returns `FieldEvaluation` with `prompt_hash=None`
- Empty prediction or reference → score=0.0 without raising

## Acceptance Criteria
- [ ] Returns `FieldEvaluation` with `score` in [0, 1]
- [ ] `metadata` contains `is_hallucination`, `method="faithfulness"`, `threshold`
- [ ] `prompt_hash` is `None`
- [ ] Makes no external LLM API calls
- [ ] Empty prediction or reference returns score=0.0 without raising
- [ ] Google-style docstring and full type hints

## Dependencies
- TASK-001

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

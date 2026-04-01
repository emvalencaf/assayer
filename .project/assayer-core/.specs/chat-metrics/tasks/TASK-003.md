---
id: TASK-003
spec: chat-metrics
status: tests-written
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-003: Implement semantic_similarity metric factory

## What to do
In `assayer/metrics/chat.py`, implement:
- `make_semantic_similarity(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> MetricFn`

The returned callable:
1. Encodes all predictions and references with the given sentence-transformer model
2. Computes per-pair cosine similarity
3. Returns the mean cosine similarity as a float in [0, 1]

Must return 0.0 for empty input without raising.

## Acceptance Criteria
- [ ] Default model is `"sentence-transformers/all-MiniLM-L6-v2"`
- [ ] Returned metric function returns cosine similarity in [0, 1] for any non-empty string inputs
- [ ] Custom `model_name` is used instead of the default when provided
- [ ] Returns 0.0 for empty input lists
- [ ] Has Google-style docstring and full type hints

## Dependencies
- TASK-001 (module already created)

## Tests
Test file: `/home/emvalenca/personal_projects/assayer/test_semantic_similarity.py`
- Covers all acceptance criteria: default model, custom model usage, similarity range [0,1], empty input handling, and proper function signature/docstring
- Tests edge cases: identical strings, orthogonal vectors, single words, mismatched list lengths, error handling
- Tests mean computation across multiple prediction-reference pairs

## Implementation Notes

## Commit
Hash:

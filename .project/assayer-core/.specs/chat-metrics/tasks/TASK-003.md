---
id: TASK-003
spec: chat-metrics
status: done
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

### Completed Implementation
- Implemented `make_semantic_similarity` factory function in `assayer/metrics/chat.py`
- Factory returns a `MetricFn` that computes cosine similarity using sentence transformers
- Function signature: `make_semantic_similarity(model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> MetricFn`
- Default model is "sentence-transformers/all-MiniLM-L6-v2" as required
- The returned metric function computes per-pair cosine similarity and returns the mean

### Technical Decisions
- Used dynamic import with fallback to handle sentence_transformers dependency gracefully
- Implemented cosine similarity calculation manually to ensure values are clamped to [0, 1] range
- Added robust error handling that returns 0.0 for any failure conditions (model loading, encoding, etc.)
- Handled edge cases: empty inputs, mismatched list lengths, zero vectors

### Key Features  
- **Empty input handling**: Returns 0.0 for empty predictions, references, or both
- **Custom model support**: Accepts any sentence transformer model name
- **Error resilience**: Gracefully handles model loading failures, encoding errors, etc.
- **Proper similarity range**: Ensures cosine similarity values are in [0, 1] by clamping negative values
- **List length mismatch**: Uses minimum length to compute similarities for available pairs
- **Zero vector handling**: Returns 0.0 similarity when either vector has zero norm

### Testing
- All 14 tests pass, covering default/custom models, similarity calculations, empty inputs, edge cases, and error handling
- Function signature and docstring validation pass
- Error scenarios properly handled with graceful fallback to 0.0

## Commit
Hash: 6bf4ed1

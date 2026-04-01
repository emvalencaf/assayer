---
prd: assayer-core
id: chat-metrics
status: pending
depends-on: [registry-and-extension]
created: 2026-03-30
---

# Spec: Chat Quality Metrics

## Context
Addresses AC-002 and AC-003 from the assayer-core PRD.
Developers evaluating chat/conversational LLM outputs need built-in, reference-quality metrics to measure generation quality against ground-truth responses. This spec implements the four built-in chat metrics and registers them in the `MetricRegistry`.

## Scope

### In scope
- Implement `bleu` metric using NLTK's BLEU implementation
- Implement `rouge_l` metric using the `rouge-score` library
- Implement `bert_score` metric using the `bert-score` library
- Implement `semantic_similarity` metric using sentence-transformers with a configurable default model
- Register all four under their canonical names in a `MetricRegistry` instance
- Factory function for `semantic_similarity` that accepts an optional `embedding_model` parameter

### Out of scope
- ROUGE-1 / ROUGE-2 variants (only ROUGE-L is required)
- BERTScore with custom model selection beyond the default
- Batch-level aggregation beyond computing the mean across all example-level scores
- Any chat-specific evaluators (those belong to the `runner` spec)

## Technical Design

All four metrics conform to the signature established in `registry-and-extension`:

```
MetricFn = Callable[[list[str], list[str]], float]
```

where the first argument is `predictions` and the second is `references`.
Each function returns a single `float` in [0, 1].

### bleu
Wraps `nltk.translate.bleu_score.corpus_bleu`. Uses uniform 4-gram weights `(0.25, 0.25, 0.25, 0.25)`. Input strings are tokenized by splitting on whitespace. Returns corpus-level BLEU.

### rouge_l
Wraps `rouge_score.rouge_scorer.RougeScorer(["rougeL"])`. Returns the mean `fmeasure` across all prediction/reference pairs.

### bert_score
Wraps `bert_score.score()`. Uses `lang="en"` and `rescale_with_baseline=True`. Returns the mean F1 across all pairs as a float.

### semantic_similarity
Factory function:
```
def make_semantic_similarity(
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
) -> MetricFn:
    ...
```
Returns a `MetricFn` that:
1. Encodes all predictions and references using the given sentence-transformer model
2. Computes per-pair cosine similarity
3. Returns the mean cosine similarity as a float in [0, 1]

### Registration helper
```
def register_chat_metrics(registry: MetricRegistry) -> None:
    registry.register("bleu", bleu)
    registry.register("rouge_l", rouge_l)
    registry.register("bert_score", bert_score)
    registry.register("semantic_similarity", make_semantic_similarity())
```

Users who want a custom embedding model call `make_semantic_similarity(model_name=...)` and register the result manually.

## Acceptance Criteria
- [ ] AC-CM-001: `bleu(predictions, references)` returns a float within ±0.01 of `nltk.translate.bleu_score.corpus_bleu` for the same tokenized inputs.
- [ ] AC-CM-002: `rouge_l(predictions, references)` returns a float within ±0.01 of the `rouge-score` library's mean ROUGE-L F1 for the same inputs.
- [ ] AC-CM-003: `bert_score(predictions, references)` returns a float within ±0.01 of the `bert-score` library's mean F1 for the same inputs.
- [ ] AC-CM-004: `make_semantic_similarity()` with the default model returns cosine similarity in [0, 1] for any non-empty string inputs.
- [ ] AC-CM-005: `make_semantic_similarity(model_name="custom-model")` uses the specified model, not the default.
- [ ] AC-CM-006: `register_chat_metrics(registry)` registers exactly the names `"bleu"`, `"rouge_l"`, `"bert_score"`, `"semantic_similarity"` in the provided registry.
- [ ] AC-CM-007: All four metrics handle empty prediction/reference lists by returning 0.0 without raising.

## Edge Cases
- Empty `predictions` or `references` list → return 0.0
- Single-word strings (no tokenization boundary) → handled gracefully
- Predictions longer or shorter than references → no errors
- `bert_score` on very short strings (< 3 tokens) → must not raise

## Risks
- `bert_score` downloads a model on first use; tests must either mock the download or use a lightweight model
- `sentence-transformers` model download at test time → same concern; use a fixture that patches the encoder

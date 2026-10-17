---
type: Metric
title: Semantic similarity
description: Chat metric returning the mean cosine similarity between prediction and reference embeddings, clamped to [0, 1].
resource: assayer/metrics/chat.py
tags: [metrics, chat]
status: stable
generated: { by: claude-code/pre-commit, at: 2026-10-16T00:00:00Z }
sources:
  - id: chat-metrics
    resource: assayer/metrics/chat.py
    title: make_semantic_similarity factory
  - id: similarity-tests
    resource: tests/metrics/test_semantic_similarity.py
    title: Semantic similarity tests
---

# Overview

`make_semantic_similarity` in `assayer/metrics/chat.py` returns a metric function
`(predictions, references) -> float`, following the pure-metric convention in
[package organization](/architecture/package-organization.md). Each pair is
encoded with a `SentenceTransformer` model and scored by cosine similarity; the
metric returns the mean over all pairs.[^chat-metrics]

# Range

The documented range is [0, 1]. Each pair's similarity is clamped on both ends:

* Negative cosine values become `0.0`.
* Float overshoot above `1.0` becomes `1.0`. With float32 embeddings, identical
  texts can yield a raw cosine slightly above 1 (for example `1.0000001`), so
  identical inputs always score exactly `1.0`.[^similarity-tests]

[^chat-metrics]: make_semantic_similarity factory
[^similarity-tests]: Semantic similarity tests

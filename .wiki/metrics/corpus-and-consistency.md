---
type: Reference
title: Corpus and consistency metrics
description: The Experiment-level metrics that score a whole corpus of outputs (BLEU, accuracy, NER...) or the stability of a target across repetitions of a Case.
resource: assayer/metrics/
tags: [metrics, experiment, corpus, consistency]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-18T01:00:00Z }
sources:
  - id: corpus
    resource: assayer/metrics/corpus.py
    title: Corpus metrics
  - id: consistency
    resource: assayer/metrics/consistency.py
    title: Consistency metrics
  - id: corpus-tests
    resource: tests/metrics/test_corpus.py
    title: Corpus metric tests
  - id: consistency-tests
    resource: tests/metrics/test_consistency.py
    title: Consistency metric tests
---

# Overview

Both families are `experiment`-level [`Metric`s](metric-contract.md) (#30): each
emits one Score for the whole Experiment (`target_id` `None`). They score the
same as the corpus functions (`bleu`, `accuracy`, `ner_macro_f1`, ...), which remain as
plain functions; the legacy registries and consistency functions were removed (#39).[^corpus-tests]

# Corpus metrics

`register_corpus_metrics(registry)` registers `bleu`, `rouge_l`, `bert_score`,
`semantic_similarity`, `accuracy`, `precision`, `recall`, `f1` (the last three
macro-averaged) and `ner_macro_f1`. `corpus_metric(name, fn)` lifts any
`(predictions, references) -> float` function.[^corpus]

* Each Trajectory is one prediction (its `final_output`) paired with the `expected_output` of its Case, so a Case run k times counts k times (the corpus is pooled, not averaged per Case).
* The metric `requires` `expected_output`: a Case without it gives an `EvaluationFailure` and no Score.[^corpus-tests]

# Consistency metrics

`register_consistency_metrics(registry)` registers `agreement_rate`, `entropy`,
`correct_rate`, `pass_at_k`, `recall_at_k` and `score_std`, for a Runner with
`repetitions=k`. Each is measured per Case, over that Case's k Trajectories; the
Score is the mean over Cases.[^consistency]

| Metric | Per Case |
|---|---|
| `agreement_rate` | Share of repetitions giving the most frequent answer. |
| `entropy` | Shannon entropy in bits divided by `log2(k)`, so within [0, 1]. The one deliberate departure from the removed legacy value, as a Score must fit [0, 1]. |
| `correct_rate` | Share of repetitions equal to the reference (as sets for multi-label outputs). |
| `pass_at_k` | 1 if any repetition equals the reference, else 0. |
| `recall_at_k` | Share of the reference labels covered by the union of the repetitions. |
| `score_std` | Sample standard deviation of the Scores of another trajectory-level metric over the repetitions. |

* `correct_rate`, `pass_at_k` and `recall_at_k` `require` `expected_output`.
* `make_score_std(of="metric")` names the metric to measure. Without `of`, the only trajectory-level metric that scored the output is used; with none or several, it fails with an `EvaluationFailure`. That metric must run before `score_std`.[^consistency-tests]
* A single repetition has no disagreement: `agreement_rate` 1.0, `entropy` 0.0.
* With nothing to measure (an Experiment with no Trajectories) a consistency metric gives an `EvaluationFailure`, never a 0.[^consistency-tests]

# Per Field

Both families work in `field_metrics`, where they see that Field's values only;
see [Per-Field measurement](../architecture/field-measurement.md).

[^corpus]: Corpus metrics
[^corpus-tests]: Corpus metric tests
[^consistency]: Consistency metrics
[^consistency-tests]: Consistency metric tests

---
type: Reference
title: Retrieval and pass^k metrics
description: Goal success, faithfulness, context precision and recall over retrieval Steps, and the Experiment-level pass^k.
resource: assayer/metrics/judge.py
tags: [metrics, judge, retrieval, rag]
status: stable
generated: { by: claude-code, at: 2026-10-17T22:00:00Z }
sources:
  - id: judge
    resource: assayer/metrics/judge.py
    title: make_goal_success and make_faithfulness
  - id: retrieval
    resource: assayer/metrics/retrieval.py
    title: make_context_precision and make_context_recall
  - id: retrieved
    resource: assayer/metrics/retrieved.py
    title: retrieved_items
  - id: consistency
    resource: assayer/metrics/consistency.py
    title: make_pass_hat_k
---

# Overview

Four trajectory-level metrics and one Experiment-level aggregate, all built on
the [Judge metrics](judge-metrics.md) and the [Metric contract](metric-contract.md).
A missing reference is an `EvaluationFailure`, never a 0.

# Goal success

`make_goal_success(judge, name="goal_success")` asks the Judge for 0 or 1 on the
Case input and `final_output`. With `Case.expected_outcome` the Judge compares the
answer to it; without, it decides from the request alone. `metadata["reference"]`
records which.[^judge]

# Faithfulness

`make_faithfulness(judge)` makes two Judge calls: one lists the claims of
`final_output`, one says per claim whether the retrieved context supports it. The
Score is supported over total claims, with the counts and each verdict in
`metadata`. The context is the items of the `retrieval` Steps. No context or no
claims is an `EvaluationFailure`. Each reply is retried once if it does not
parse.[^judge]

# Context precision and recall

A `retrieval` Step's `output` is the ranked list of its items, each a string or a
mapping with `id` and `text` (or `content`); all the retrieval Steps of a
Trajectory read as one ranking. `make_context_precision(match)` is the average
precision of that ranking, `make_context_recall(match)` the share of reference
contexts retrieved.

| `match` | Compares | Against |
|---|---|---|
| `"id"` | item `id` | `Case.reference_context_ids` |
| `"string"` | item text, ignoring case and whitespace; it holds the reference, or is a snippet of it of at least 20 characters | `Case.reference_contexts` |

They are deterministic. A missing or empty reference, a Trajectory without a
retrieval Step or an item without an `id` (id variant) is an `EvaluationFailure`.
`register_retrieval_metrics` registers the four as `context_precision_id`,
`context_precision_string`, `context_recall_id` and `context_recall_string`.[^retrieval]

# pass^k

`make_pass_hat_k(of=None, threshold=0.5)` is the share of Cases whose k repetitions
all score at least `threshold` for the trajectory-level metric `of` (the only one,
if omitted), which must run first. The default 0.5 splits a binary metric and is
the midpoint of a normalised one. A repetition without a Score makes it an
`EvaluationFailure` instead of a miss. It is stricter than `pass_at_k`.[^consistency]

[^judge]: make_goal_success and make_faithfulness
[^retrieval]: make_context_precision and make_context_recall
[^consistency]: make_pass_hat_k

---
type: Reference
title: Comparison of Experiments
description: compare(a, b) returns a Comparison with the per-(metric, Field) Score deltas and the mean token and cost deltas per Case between two Experiments.
resource: assayer/runner/compare.py
tags: [runner, experiment, comparison]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T23:00:00Z }
sources:
  - id: compare
    resource: assayer/runner/compare.py
    title: compare
  - id: model
    resource: assayer/models/comparison.py
    title: Comparison model
  - id: tests
    resource: tests/runner/test_compare_experiments.py
    title: compare tests
---

# Overview

`compare(experiment_a, experiment_b, pricing=None)` in `assayer.runner` reports how
the second Experiment differs from the first, always **b minus a** (#27).[^compare]
It sits beside the legacy `compare_experiments`, which is unchanged.

# Comparison

`Comparison` (`assayer.models`) is a dataclass with:[^model]

| Field | Meaning |
|---|---|
| `metric_deltas` | `dict[(metric name, Field), float \| None]`: difference of the mean Score per key. `None` when the key is scored on one side only. |
| `input_tokens_delta` | Difference of the mean input tokens per Case. |
| `output_tokens_delta` | Difference of the mean output tokens per Case. |
| `cost_usd_delta` | Difference of the mean cost per Case. `None` without `pricing`. |

# Rules

* Scores are averaged per `(score.name, score.field)`; the same metric on another
  Field is a separate key, and `None` Field is its own key. Keys are sorted.
* Usage is averaged per `case_id`: repetitions of a Case are averaged inside it
  first, then the Cases are averaged, so a Case with more repetitions weighs the same.
* The three token and cost deltas are `None` when either Experiment has no
  Trajectories.[^tests]

[^compare]: compare
[^model]: Comparison model
[^tests]: compare tests

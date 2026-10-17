---
type: Reference
title: Comparison of Experiments
description: compare(a, b) returns a Comparison with the per-(metric, Field) Score deltas and the mean token and cost deltas per shared Case between two Experiments, plus the Cases only one side has.
resource: assayer/runner/compare.py
tags: [runner, experiment, comparison]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T23:30:00Z }
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

`compare(experiment_a, experiment_b)` in `assayer.runner` reports how
the second Experiment differs from the first, always **b minus a** (#27).[^compare]
It replaced the legacy `compare_experiments` and `ExperimentResult.compare` (#39). It takes no
`pricing` argument: the cost uses the `Experiment.pricing` each side carries, so the
two sides may use different models.

# Comparison

`Comparison` (`assayer.models`) is a dataclass with:[^model]

| Field | Meaning |
|---|---|
| `metric_deltas` | `dict[(metric name, Field), float \| None]`: difference of the mean Score per key. `None` when the key is scored on one side only. |
| `input_tokens_delta` | Difference of the mean input tokens per Case. `None` when either side has no recorded usage. |
| `output_tokens_delta` | Difference of the mean output tokens per Case. `None` when either side has no recorded usage. |
| `cost_usd_delta` | Difference of the mean cost per Case. `None` when either side has no recorded usage or no pricing. |
| `only_in_a` | Ids of the Cases that only the first Experiment has (sorted). |
| `only_in_b` | Ids of the Cases that only the second Experiment has (sorted). |

# Rules

* Scores are averaged per `(score.name, score.field)`; the same metric on another
  Field is a separate key, and `None` Field is its own key. Keys are sorted.
* Usage is averaged per `case_id`: repetitions of a Case are averaged inside it
  first, then the Cases are averaged, so a Case with more repetitions weighs the same.
* The usage deltas cover only the Cases both Experiments have, so they compare like
  with like; the others are listed in `only_in_a` and `only_in_b`. The metric deltas
  are not restricted this way: they use every Score of each side.
* "No recorded usage" means no Step of any Trajectory of the shared Cases carries `usage` (no Trajectories,
  or outputs scored after the fact). That is unknown, not zero, so the deltas are
  `None` rather than `0`.
* Cost is priced with each Experiment's own `pricing`; if either side has none, the
  cost delta is `None` while the token deltas still apply.
* The Judge's usage (`judge_usage`) is never part of the token or cost deltas.[^tests]

[^compare]: compare
[^model]: Comparison model
[^tests]: compare tests

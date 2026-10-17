---
type: Reference
title: Vendor-neutral domain models
description: The Trajectory, Step, Score, Experiment, EvaluationFailure, Dataset and Case dataclasses in assayer.models, and the rules each one validates.
resource: assayer/models/__init__.py
tags: [architecture, models, domain]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T23:00:00Z }
sources:
  - id: models-init
    resource: assayer/models/__init__.py
    title: Public API of the models subpackage
  - id: trajectory
    resource: assayer/models/trajectory.py
    title: Trajectory model
  - id: experiment
    resource: assayer/models/experiment.py
    title: Experiment model
  - id: glossary
    resource: GLOSSARY.md
    title: Domain language
---

# Overview

`assayer.models` now holds vendor-neutral dataclasses beside the legacy result
models (`RunResult`, `ExperimentResult`, `Consistency*`). They follow the domain
terms in `GLOSSARY.md` (#24).[^glossary]

| Model | Role |
|---|---|
| `Trajectory` | Ordered record of what an agent did for one input: `steps`, `session_id`, `final_output`, `final_state`, `case_id`, `repetition` (default 0). May be empty. |
| `Step` | One unit of work in a Trajectory, with `kind` (`model`, `tool`, `retrieval` or `other`), `id`, `parent_id`, `name`, `model`, `input`, `output`, `error`, `usage`. |
| `Score` | One named result in [0, 1] of a metric, with optional `field`, `label`, `comment`, `metadata`, `target` (`ScoreTarget`) and `target_id`. |
| `Experiment` | Trajectories, Scores and failures from running one target over a Dataset, plus `judge_usage` and `pricing` (the target's `PricingConfig`, optional). |
| `EvaluationFailure` | A metric that could not be computed, kept as data (`metric`, `error`, `target_id`) instead of raised. |
| `Dataset` | A named list of Cases. |
| `Case` | One input with optional references (`expected_output`, `expected_tool_calls`, `expected_steps`, `expected_outcome`, `expected_state`, `reference_contexts`, `reference_context_ids`). |
| `Comparison` | The difference between two Experiments (second minus first): `metric_deltas`, `input_tokens_delta`, `output_tokens_delta`, `cost_usd_delta`. Returned by `compare`; see [Comparison](comparison.md). |
| `PricingConfig` | Per-token input and output prices, with `cost(input_tokens, output_tokens)` to price a token count. Moved here from `assayer.runner.pricing`, which re-exports it. |

# Validation rules

* `Step` raises `ValueError` for an unknown `kind`, or for `usage` on a non-model Step. A Step `error` is data and never invalidates the Trajectory.
* `Step.kind` is typed as `StepKind`, a `Literal` of the four kinds.
* `Score` raises `ValueError` for a non-numeric `value` (for example `None` or a string), converts numbers with `float()` (so booleans become 0.0 or 1.0), and raises `ValueError` outside [0, 1].
* `Score` only accepts `target` of `step`, `trajectory` or `experiment` (default `trajectory`), typed as `ScoreTarget`. A `step` target requires `target_id`, otherwise `ValueError`.
* `Experiment` raises `ValueError` for an empty or whitespace-only `name`.

# Usage and cost

* `Trajectory.total_usage(pricing=None)` sums the usage of its model Steps only. `cost_usd` is None unless a `PricingConfig` is given, then it is derived from the token counts with `PricingConfig.cost`.[^trajectory]
* `Experiment.total_usage(pricing=None)` sums the Trajectory totals and excludes `judge_usage`, which is kept apart from the target's totals. `pricing` defaults to `Experiment.pricing`; with neither, `cost_usd` is None.[^experiment]
* `Experiment.pricing` is never applied to `judge_usage`, whose model is another one: price it with `total_judge_usage(pricing)`.[^experiment]
* `Experiment.total_judge_usage(pricing=None)` prices the Judge bucket: it returns None when `judge_usage` is None, otherwise a `TokenUsage` with the same tokens and a `cost_usd` computed from the Judge model's `PricingConfig` (None without it).[^experiment]
* `TokenUsage` supports `+`: tokens are summed, and `cost_usd` is None unless both operands have a known cost. `Experiment.total_usage` folds the Trajectory totals with it.

[^glossary]: Domain language
[^trajectory]: Trajectory model
[^experiment]: Experiment model

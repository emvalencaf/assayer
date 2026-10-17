---
type: Reference
title: Runner
description: Runs a target over a Dataset of Cases and returns an Experiment with Scores and evaluation failures.
resource: assayer/runner/runner.py
tags: [runner, experiment, dataset]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T23:00:00Z }
sources:
  - id: runner
    resource: assayer/runner/runner.py
    title: Runner
  - id: loader
    resource: assayer/runner/case_loader.py
    title: load_cases
  - id: tests
    resource: tests/runner/test_runner.py
    title: Runner tests
---

# Overview

`Runner(target, metrics, repetitions=1, pricing=None).run(dataset)` calls the target with each
`Case.input` and returns an `Experiment` (#26).[^runner] `target` is optional:
`run` raises `ValueError` without one, and only `score` works without it.

* A target returning a plain value gets it wrapped in one `model` Step; one
  returning a `Trajectory` is kept as is. An exception becomes the `error` of a
  model Step, formatted as `ExceptionType: message` (e.g. `RuntimeError: boom`).
* Every Trajectory gets `case_id` (the Case id, else its position) and
  `repetition`; Steps without an id get one so Step Scores can point at them.
* Metrics run at their own level; Scores and `EvaluationFailure`s go on the Experiment.
* `pricing` (a `PricingConfig` for the target's model) is stored on `Experiment.pricing`,
  by both `run` and `score`, so `Experiment.total_usage()` and
  [compare](comparison.md) can price the target. It is never applied to the Judge.

# Scoring collected outputs

`Runner(metrics=...).score(dataset, outputs)` scores outputs gathered beforehand
without calling the target (#27).[^runner]

* `outputs` has one entry per Case, in order; a different length raises `ValueError`.
* Each entry is a `Trajectory` or a plain value wrapped in one `model` Step, and
  becomes the Case's only repetition (`repetition` 0). It is tagged like a run
  result (`case_id`, Step ids) on a copy; the caller's object is untouched.
* Metrics, Scores and `EvaluationFailure`s behave as in `run`. Two Experiments can
  then be diffed with [Comparison](comparison.md).

# Loading

`dataset` may be a `Dataset`, a list of dicts or a JSON path. `load_cases`
requires `input` plus only the Case fields that the chosen metrics list in
`requires`, and rejects unknown keys.[^loader]

[^runner]: assayer/runner/runner.py
[^loader]: assayer/runner/case_loader.py

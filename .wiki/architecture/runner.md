---
type: Reference
title: Runner
description: Runs a target over a Dataset of Cases and returns an Experiment with Scores and evaluation failures.
resource: assayer/runner/runner.py
tags: [runner, experiment, dataset]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T21:00:00Z }
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

`Runner(target, metrics, repetitions=1).run(dataset)` calls the target with each
`Case.input` and returns an `Experiment` (#26).[^runner]

* A target returning a plain value gets it wrapped in one `model` Step; one
  returning a `Trajectory` is kept as is. An exception becomes the `error` of a
  model Step.
* Every Trajectory gets `case_id` (the Case id, else its position) and
  `repetition`; Steps without an id get one so Step Scores can point at them.
* Metrics run at their own level; Scores and `EvaluationFailure`s go on the Experiment.

# Loading

`dataset` may be a `Dataset`, a list of dicts or a JSON path. `load_cases`
requires `input` plus only the Case fields that the chosen metrics list in
`requires`, and rejects unknown keys.[^loader]

[^runner]: assayer/runner/runner.py
[^loader]: assayer/runner/case_loader.py

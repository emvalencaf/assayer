---
type: Reference
title: Metric contract and Registry
description: The public Metric dataclass, its MetricOutcome result and the Registry that holds built-in and custom metrics alike.
resource: assayer/metrics/metric.py
tags: [metrics, contract, registry]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T23:30:00Z }
sources:
  - id: metric
    resource: assayer/metrics/metric.py
    title: Metric and MetricOutcome
  - id: registry
    resource: assayer/registries/registry.py
    title: Registry
  - id: contract-tests
    resource: tests/metrics/test_metric.py
    title: Metric contract tests
  - id: registry-tests
    resource: tests/registries/test_registry.py
    title: Registry tests
  - id: glossary
    resource: GLOSSARY.md
    title: Domain language
---

# Overview

A `Metric` is a named way of computing Scores for a Step, a Trajectory or an
Experiment. Built-in and custom metrics share this one shape, so they run, skip
and fail the same way (#25).[^metric] It sits beside the legacy `MetricRegistry`
and `EvaluatorRegistry`, which stay until the clean break.[^glossary]

# Metric fields

| Field | Description |
|---|---|
| `name` | Name of the metric; becomes the name of its Scores. |
| `level` | What it scores: `step`, `trajectory` or `experiment`. |
| `fn` | Called as `fn(subject, case)`, plus keyword parameters given for a Field; returns a number in [0, 1] or a boolean. |
| `requires` | Names of Case, Trajectory or Step fields the metric needs (for example `expected_output`, `final_state`). Default empty. |
| `kind` | `deterministic` (default), or `judge` when a Judge scores the output. |

`Metric` raises `ValueError` for a blank `name`, an unknown `level` or `kind`, or
a `requires` entry that names a field of no Case, Trajectory or Step. It raises
`TypeError` when `fn` is not callable.[^metric]

# Evaluating

`Metric.evaluate(subject, case=None, field=None, params=None)` applies the metric once and returns a
`MetricOutcome` (`scores`, `failures`). It never raises.[^metric]

* `field` is the dotted path of the output Field the subject and case were cut down to; it is recorded on the Score or `EvaluationFailure`. `params` are passed to `fn` as keyword arguments. See [Per-Field measurement](../architecture/field-measurement.md).

* Each `requires` name is looked up on the Case first, then on the subject. If any is `None`, no Score is emitted and one `EvaluationFailure` ("missing required input: ...") is returned. A missing input is never scored as 0.
* A missing answer is different: the metric itself scores it 0 (an empty `final_output` against an expected one).
* If `fn` raises, the exception message becomes an `EvaluationFailure`.
* Resolving the `target_id` and checking `requires` run inside the same guard as `fn`, so a wrong subject (for example `None` for a `step` metric) becomes an `EvaluationFailure` instead of an exception.[^contract-tests]
* The Score's `target_id` is the Step `id` for `step` metrics, the Trajectory `case_id` for `trajectory` metrics, and `None` for `experiment` metrics.[^contract-tests]

# Registry

`Registry` (`assayer.registries.Registry`) stores `Metric` objects by name. Each
instance keeps its own metrics, with no shared state.[^registry] It imports
`Metric` from `assayer.metrics.metric` directly: `assayer.metrics` imports the
legacy registries, so going through its `__init__` would be circular.

* `register(metric)` raises `TypeError` for a non-Metric and `KeyError` for a duplicate name.
* `get(name)` raises `KeyError` for an unknown name.
* `list_metrics()` returns the names sorted.[^registry-tests]

The first metric on the contract is [step efficiency](step-efficiency.md),
registered with `register_agent_metrics(registry)`.

[^metric]: Metric and MetricOutcome
[^registry]: Registry
[^contract-tests]: Metric contract tests
[^registry-tests]: Registry tests
[^glossary]: Domain language

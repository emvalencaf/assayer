---
type: Reference
title: Package organization
description: How the assayer package is split by responsibility, and the conventions each subpackage follows.
resource: CODE_STANDARDS.md
tags: [architecture, conventions]
status: stable
generated: { by: claude-code/manual, at: 2026-10-16T00:00:00Z }
sources:
  - id: standards
    resource: CODE_STANDARDS.md
    title: Package organization section
  - id: metrics-init
    resource: assayer/metrics/__init__.py
    title: Public API of the metrics subpackage
---

# Overview

`assayer/` is a flat package split by responsibility. Dependencies point inward:
`runner` uses `evaluators`, `metrics`, `registries` and `integrations`, which all
build on `models`.

| Subpackage | Role |
|---|---|
| `models/` | Dataclasses that carry results (`TokenUsage`, `RunResult`, `ExperimentResult`, `Consistency*`). |
| `evaluators/` | `BaseEvaluator` and its implementations (NER, hallucination, consistency). |
| `metrics/` | Pure `(predictions, references) -> float` functions, one module per task. |
| `registries/` | `MetricRegistry` and `EvaluatorRegistry`, instantiable, no global state. |
| `runner/` | Evaluation, historical and consistency pipelines, field routing, pricing. |
| `integrations/` | Adapters for external services (LangSmith). |

# Conventions

* One concept per module; each subpackage re-exports its public API in `__init__.py` with `__all__`.
* Registration is explicit through `register_<task>_metrics(registry)` and `register_<task>_evaluators(registry)`; importing never registers.
* New metrics and evaluators are added, not edited into core files.
* Tests mirror the package under `tests/<subpackage>/`.

The full rules live in the **Package organization** section of `CODE_STANDARDS.md`.

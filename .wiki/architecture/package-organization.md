---
type: Reference
title: Package organization
description: How the assayer package is split by responsibility, and the conventions each subpackage follows.
resource: CODE_STANDARDS.md
tags: [architecture, conventions]
status: stable
generated: { by: claude-code/pre-commit, at: 2026-10-17T20:00:00Z }
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
| `models/` | Dataclasses that carry results (`TokenUsage`, `RunResult`, `ExperimentResult`, `Consistency*`) and the vendor-neutral [domain models](domain-models.md) (`Trajectory`, `Step`, `Score`, `Experiment`, `Dataset`, `Case`, `PricingConfig`). |
| `evaluators/` | `BaseEvaluator` and its implementations (NER, hallucination, consistency). |
| `metrics/` | The [`Metric` contract](../metrics/metric-contract.md) (`level`, `requires`, `kind`) and built-in metrics, one module per task (`agent`, `chat`, `classification`, `ner`); legacy ones are pure `(predictions, references) -> float` functions. |
| `registries/` | `Registry` (holds `Metric` objects) and the legacy `MetricRegistry` and `EvaluatorRegistry`, instantiable, no global state. |
| `runner/` | Evaluation, historical and consistency pipelines, field routing, pricing. |
| `integrations/` | Adapters for external services (LangSmith). |

# Conventions

* One concept per module; each subpackage re-exports its public API in `__init__.py` with `__all__`.
* Registration is explicit through `register_<task>_metrics(registry)` and `register_<task>_evaluators(registry)`; importing never registers.
* New metrics and evaluators are added, not edited into core files.
* Tests mirror the package under `tests/<subpackage>/`.

The full rules live in the **Package organization** section of `CODE_STANDARDS.md`.

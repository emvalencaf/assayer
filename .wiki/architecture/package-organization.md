---
type: Reference
title: Package organization
description: How the assayer package is split by responsibility, and the conventions each subpackage follows.
resource: CODE_STANDARDS.md
tags: [architecture, conventions]
status: stable
generated: { by: claude-code/pre-commit, at: 2026-10-17T22:00:00Z }
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
`runner` uses `evaluators`, `metrics`, `registries`, `integrations` and `adapters`, which all
build on `judges` and `models`.

| Subpackage | Role |
|---|---|
| `models/` | Dataclasses that carry results (`TokenUsage`, `RunResult`, `ExperimentResult`, `Consistency*`) and the vendor-neutral [domain models](domain-models.md) (`Trajectory`, `Step`, `Score`, `Experiment`, `Dataset`, `Case`, `PricingConfig`). |
| `judges/` | The Judge Protocol and `JudgeResponse`, `Prompt` (`id@version` plus a hash), tolerant `score` + `reason` parsing and the ledger of Judge calls and tokens. See [Judge metrics](../metrics/judge-metrics.md). |
| `evaluators/` | `BaseEvaluator` and its implementations (NER, hallucination, consistency). |
| `metrics/` | The [`Metric` contract](../metrics/metric-contract.md) (`level`, `requires`, `kind`) and built-in metrics, one module per task (`agent`, `chat`, `classification`, `ner`, `consistency`, `field` for the Field comparisons, `judge` for the Judge-based ones; `corpus` lifts the chat, classification and NER functions to Experiment level, see [Corpus and consistency metrics](../metrics/corpus-and-consistency.md)); legacy ones are pure `(predictions, references) -> float` functions. |
| `registries/` | `Registry` (holds `Metric` objects) and the legacy `MetricRegistry` and `EvaluatorRegistry`, instantiable, no global state. |
| `runner/` | Evaluation, historical and consistency pipelines, field routing, pricing, and the `field_map/` package (Alignment, Field scoring, schema utility, YAML/JSON loading). |
| `alignment.py`, `path.py` | Top-level pure helpers (Alignment of list items, dotted-path `resolve`) shared by `metrics/` and `runner/field_map/`; they import nothing else from `assayer` but each other. Still importable from `assayer.runner.field_map`. |
| `adapters/` | The `Adapter` Protocol, `ExportReport`/`ExportFailure`, the closed failure taxonomy, deterministic export ids, the retry policy, `plan_export`/`run_export` and `InMemoryAdapter`; no backend-specific clients. See [Adapters](adapters.md). |
| `integrations/` | Adapters for external services: `LangSmithAdapter` (see [Adapters](adapters.md)). |

# Conventions

* One concept per module; each subpackage re-exports its public API in `__init__.py` with `__all__`.
* Registration is explicit through `register_<task>_metrics(registry)` and `register_<task>_evaluators(registry)`; importing never registers.
* New metrics and evaluators are added, not edited into core files.
* Tests mirror the package under `tests/<subpackage>/`.

The full rules live in the **Package organization** section of `CODE_STANDARDS.md`.

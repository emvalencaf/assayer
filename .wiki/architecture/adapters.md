---
type: Reference
title: Adapters
description: The vendor-neutral boundary that exports an Experiment to an observability backend, with deterministic ids, a closed failure taxonomy and an ExportReport.
resource: assayer/adapters/__init__.py
tags: [adapters, export, observability]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T22:00:00Z }
sources:
  - id: adapter
    resource: assayer/adapters/adapter.py
    title: Adapter Protocol
  - id: export
    resource: assayer/adapters/export.py
    title: plan_export and run_export
  - id: ids
    resource: assayer/adapters/ids.py
    title: Deterministic ids
  - id: retry
    resource: assayer/adapters/retry.py
    title: Retry policy
  - id: conformance
    resource: tests/adapters/conformance.py
    title: Conformance suite
---

# Overview

`assayer.adapters` is the boundary between an [Experiment](domain-models.md) and an
observability backend (#35).[^adapter] An `Adapter` is a sync, not thread-safe Protocol
with `name`, `export(experiment, *, include_content=True) -> ExportReport`, `close()`
and context-manager support. Exporting the same Experiment again updates what is there,
it does not duplicate it.

`Runner(adapter=...)` holds the Adapter and `Runner.export(experiment, include_content=True)`
sends an Experiment through it; without an adapter it raises `ValueError`. See [Runner](runner.md).

# Errors

* `AdapterConfigError` (a `ValueError`) is raised by an Adapter's constructor for local misconfiguration, before any network call.
* `AdapterCallError(kind, message, retryable=None, retry_after=None)` is what backend code raises for a failed call. `kind` belongs to the closed taxonomy `auth | rate_limited | validation | transport | unsupported | unknown`, otherwise `ValueError`. `retryable` defaults to True for `rate_limited` and `transport` only.

# ExportReport

| Field | Meaning |
|---|---|
| `confirmed` | Items the backend acknowledged. |
| `queued` | Items handed to an SDK that buffers them, delivery not confirmed. |
| `failed` | `ExportFailure(target_kind, target_id, kind, message, retryable)`. |
| `skipped` | Items not tried because an `auth` failure aborted the export. |
| `notes` | Things dropped or degraded on purpose. |

`ok` means nothing failed and nothing was skipped. An item's failure is reported, never raised.

# Export flow

`plan_export(experiment, include_content=True)` lists the items in order: Cases, then each Trajectory followed by its Steps, then Scores.[^export] `run_export(planned, send, sleep=...)` sends them one by one, so an Adapter only has to say how to send one item. `send` returns `"queued"` for a buffered item, otherwise the item is confirmed; an `AdapterCallError` becomes a failure of its kind and any other exception becomes `unknown`. An `auth` failure stops the export and lists the remaining items as `skipped`.

`include_content=False` leaves out Case inputs and references, Step `input` and `output`, and the Trajectory `final_output` and `final_state`; structure, usage, Scores and metadata are kept.

# Deterministic ids

Ids are UUIDv5 hex strings derived from the Experiment name and the item's identity.[^ids]

* Case: Experiment name and Case id. Trajectory: Experiment name, Case id and repetition.
* Step: the exported Trajectory id and the Step's own id, or `case_id/repetition/index` when it has none.
* Score: target, target id, metric name and Field, plus its order among Scores sharing those (one per repetition, for instance). A trajectory Score attaches to the repetition it came from.

# Retry policy

`call_with_retry` makes 3 attempts on a retryable `AdapterCallError`, waiting `1 s * 2**n`, or the backend's `retry_after` capped at 60 s. A non-retryable error is raised at once; the last attempt's error is raised when retries run out.[^retry]

# InMemoryAdapter and conformance

`InMemoryAdapter(name="in-memory", queue=False, sleep=...)` keeps payloads in `items`, keyed by `ExportItem`, so re-exporting overwrites. `queue=True` reports items as queued, `fail_on(kind, *errors, nth=0)` injects failures, and an empty name is an `AdapterConfigError`. It is the bar for real Adapters: `tests/adapters/conformance.py` holds `AdapterConformance`, a suite every Adapter subclasses (three hooks: `make_adapter`, `inject`, `stored`) covering idempotent re-export, stable ids across Adapters, partial and `auth` failures, retries, `include_content` and the context manager.[^conformance]

[^adapter]: assayer/adapters/adapter.py
[^export]: assayer/adapters/export.py
[^ids]: assayer/adapters/ids.py
[^retry]: assayer/adapters/retry.py
[^conformance]: tests/adapters/conformance.py

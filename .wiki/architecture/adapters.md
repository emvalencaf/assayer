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
    title: plan_export, run_export and export_experiment
  - id: ids
    resource: assayer/adapters/ids.py
    title: Deterministic ids
  - id: retry
    resource: assayer/adapters/retry.py
    title: Retry policy
  - id: conformance
    resource: tests/adapters/conformance.py
    title: Conformance suite
  - id: langsmith
    resource: assayer/integrations/langsmith_adapter.py
    title: LangSmithAdapter
  - id: langsmith-export
    resource: assayer/integrations/langsmith_export.py
    title: One export to LangSmith
  - id: validate-langsmith
    resource: scripts/validate-langsmith.sh
    title: LangSmith validation wizard
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
| `notes` | Things dropped or degraded on purpose, such as Scores and Trajectories that could not be linked. |

`ok` means nothing failed and nothing was skipped. An item's failure is reported, never raised.

# Export flow

`plan_export(experiment, include_content=True)` returns an `ExportPlan(items, notes)`. `items` lists the `PlannedItem`s in order: Cases, then each Trajectory followed by its Steps, then Scores.[^export] `notes` lists Scores and Trajectories that could not be linked to what they refer to: a Trajectory with no `case_id` (its `case` link is empty) and a step or trajectory Score whose target is not in the Experiment (experiment-level Scores need no link).

`run_export(plan, send, sleep=...)` sends the items one by one and copies the plan's `notes` into the report, so an Adapter only has to say how to send one item. `send` returns `"queued"` for a buffered item, otherwise the item is confirmed; an `AdapterCallError` becomes a failure of its kind and any other exception becomes `unknown`. An `auth` failure stops the export and lists the remaining items as `skipped`.

`export_experiment(experiment, send, include_content=True, sleep=...)` plans and sends in one call, and is what an Adapter's `export` should call. An Experiment that cannot be planned is not raised: the report holds one `validation` failure with `target_kind="experiment"` (the fifth target kind, next to case, trajectory, step and score) and the exception as its message.

`include_content=False` leaves out Case inputs and references, Step `input`, `output` and `error`, Score `comment`, and the Trajectory `final_output` and `final_state`; structure, usage, Score values and metadata are kept.

# Deterministic ids

Ids are UUIDv5 hex strings derived from the Experiment name and the item's identity.[^ids]

* Case: Experiment name and Case id. Trajectory: Experiment name, Case id and repetition.
* Step: the exported Trajectory id and the Step's own id, or `case_id/repetition/index` when it has none.
* Score: target, target id, metric name and Field, plus its order among Scores sharing those (one per repetition, for instance). A trajectory Score attaches to the repetition it came from.

# Retry policy

`call_with_retry` makes 3 attempts on a retryable `AdapterCallError`, waiting `1 s * 2**n`, or the backend's `retry_after` capped at 60 s. A non-retryable error is raised at once; the last attempt's error is raised when retries run out.[^retry]

# InMemoryAdapter and conformance

`InMemoryAdapter(name="in-memory", queue=False, sleep=...)` keeps payloads in `items`, keyed by `ExportItem`, so re-exporting overwrites. `queue=True` reports items as queued, `fail_on(kind, *errors, nth=0)` injects failures, and an empty name is an `AdapterConfigError`. It is the bar for real Adapters: `tests/adapters/conformance.py` holds `AdapterConformance`, a suite every Adapter subclasses (three hooks: `make_adapter`, `inject`, `stored`) covering idempotent re-export, stable ids across Adapters, partial and `auth` failures, retries, `include_content` (Step errors and Score comments included), unlinkable Scores noted rather than lost, an unplannable Experiment reported as a failure, and the context manager.[^conformance]

# LangSmithAdapter

`assayer.integrations.LangSmithAdapter(client=None, *, api_key=None, dataset_name=None, started_at=None, name="langsmith")` exports an Experiment to LangSmith (#36) and replaces the removed `LangSmithPublisher`.[^langsmith] The client is an injected `langsmith.Client` (left open by `close`) or one built from `api_key`, `LANGSMITH_API_KEY` or `LANGCHAIN_API_KEY`, in that order; none of them is an `AdapterConfigError`.

* **Cases** are examples of a dataset (named after the Experiment, or `dataset_name`; created when missing, reused otherwise) with the deterministic Case id as `example_id` and `case_id` in the metadata. An existing example is updated, never deleted, and `include_content=False` leaves its inputs alone.
* **The Experiment** is a project (`create_project(upsert=True)`) whose `reference_dataset_id` is that dataset.
* **Trajectories** are run trees: a root `chain` run with `reference_example_id` set to its Case, and one child per Step with client UUIDs, `trace_id`, `parent_run_id` and `dotted_order`. Kind maps `model` to `llm`, `tool` to `tool`, `retrieval` to `retriever` and `other` to `chain`. Model Steps carry `usage_metadata` (tokens, and `total_cost` when known) and `ls_model_name`; the root run's `assayer.usage` metadata holds the Trajectory totals. Trajectories carry no timing, so start and end times are synthetic (the Adapter's first export time, or `started_at` when given, plus one microsecond per Step; `assayer.synthetic_timing` in the metadata). Pass the same timezone-aware `started_at` to export an Experiment again from a new Adapter without changing the runs' `dotted_order`. `LangSmithExport` (`langsmith_export.py`) holds the state and calls of one export.[^langsmith-export]
* **Scores** are feedback named `<metric>.<field>` (just `<metric>` without a Field) with the Field and the Score's metadata in `extra`, the label as `value` and the comment as `comment`. Step and Trajectory Scores attach to their run; Experiment-level Scores, and Scores that could not be linked, attach to the project (`project_id`). An existing feedback id is updated.
* Runs are reported `queued` (the SDK buffers them; the Adapter calls `flush()` at the end of an export), Cases and Scores `confirmed`.
* SDK errors map to the taxonomy: auth to `auth`, rate limit to `rate_limited`, connection and API errors to `transport`, not found, user and conflict errors to `validation`, anything else to `unknown`.

Tests use `create_autospec(langsmith.Client)` clients behind the conformance suite; `test_live_smoke` exports to the real LangSmith and is skipped without `LANGSMITH_API_KEY` (or `LANGCHAIN_API_KEY`). It exports twice from two Adapters and reads runs, examples and feedback back, reading the runs with the async-only `client.runs.query` (by project id, selecting `IS_ROOT`, `TRACE_ID`, `DOTTED_ORDER` and `REFERENCE_EXAMPLE_ID`) rather than `list_runs`, and checking that the single root run links to the example through `reference_example_id`, that every run shares the root's trace id and that every child's `dotted_order` extends the root's; it also checks that an existing example is updated, that run trees are not duplicated, and that run-level and project-level feedback are accepted. Project-level feedback (`overall.f`) has no run, so it is not in the project's `feedback_stats`; the test reads it back with `list_feedback` filtered by key and project id and checks its score and `session_id`. It prints the `assayer-smoke-<id>` project name and deletes the project and dataset afterwards, unless `ASSAYER_SMOKE_KEEP=1` keeps them for a look in the LangSmith UI.

`scripts/validate-langsmith.sh` is a wizard (generated by the `/wizard` skill) that runs the smoke test by hand: it saves the API key (and optionally `LANGSMITH_ENDPOINT` for EU or self-hosted, and `LANGSMITH_WORKSPACE_ID` for an organization-scoped key) to `.env`, runs `test_live_smoke` with `ASSAYER_SMOKE_KEEP=1`, walks through checking the kept project in the UI (the `exact` feedback shows on the trace; `overall.f` is experiment-level feedback that the API stores but the UI may not list like run feedback), and offers to delete the project and dataset.

[^adapter]: assayer/adapters/adapter.py
[^export]: assayer/adapters/export.py
[^ids]: assayer/adapters/ids.py
[^retry]: assayer/adapters/retry.py
[^conformance]: tests/adapters/conformance.py
[^langsmith]: assayer/integrations/langsmith_adapter.py
[^langsmith-export]: assayer/integrations/langsmith_export.py

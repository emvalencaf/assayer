# Research: Langfuse data model and Python SDK

Issue: emvalencaf/assayer#5 (child of map #2). Findings date: 2026-10. Sources are the
public Langfuse docs (langfuse.com/docs); items the docs did not state are listed under
"Gaps" and must be verified against the SDK source before the adapter is specified.

## 1. Data model

- **Trace**: one request or operation; the group of all observations sharing a `trace_id`.
  Trace-level attributes (`user_id`, `session_id`, `tags`, `metadata`) are propagated by the
  SDK onto every observation. Storage is a single observations table with a copy of the
  trace attributes on each row (so a trace has no standalone read in the v2 API; it is
  reconstructed by grouping observations by `traceId`).
- **Observation**: a step in a trace, nestable. Types: span, generation (LLM call), event;
  the docs also mention tool/retrieval-style steps as observation kinds. Carries usage/cost
  fields for generations.
- **Session**: optional grouping of traces (one session to many traces), for multi-turn chats.
- **Enrichment**: environment, tags, user, metadata, release, version.
- **Score**: an evaluation value attached to a trace, an observation, a session, or a dataset
  run. Data types: `NUMERIC` (float, default), `BOOLEAN` (0/1, must be set explicitly),
  `CATEGORICAL` (string, mapped to a config's categories when a config is given), `TEXT`
  (1-500 chars). Optional `comment` and `config_id` (score config: name and type must match,
  numeric min/max, categories enforced). A score may arrive before its trace exists and links
  once the trace appears.
- **Dataset**: named (unique per project; `/` makes virtual folders) collection of items;
  optional JSON Schema for `input` and `expectedOutput`.
- **Dataset item**: `input`, optional `expected_output`, `metadata`, optional link to a source
  trace/observation; archiving removes it from future runs. Every add/update/delete/archive
  creates a new dataset version; GET returns latest unless a version timestamp is given.
- **Dataset run / experiment**: output of running a task over a dataset (or local data);
  holds per-item traces and scores plus run-level scores.

Mapping to Assayer vocabulary (see `GLOSSARY.md`): Trajectory ~ trace with nested
observations; Score ~ Langfuse score (trace, observation, session or run target).

## 2. Python SDK (v3+ line, OpenTelemetry based; docs reference v5)

- **Auth and config**: `Langfuse(public_key, secret_key, base_url)` or `get_client()` reading
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` (default EU cloud
  `https://cloud.langfuse.com`; US, JP, HIPAA and self-hosted need an explicit URL). The
  client is a singleton per public key: later constructors with the same key reuse the first
  instance and ignore new arguments (matters for tests and multi-project use).
- **Publishing scores**: `create_score(name, value, trace_id, observation_id=, session_id=,
  data_type=, comment=, score_id=, config_id=)`; context helpers `score_current_trace` /
  `score_current_span` and `span.score()` / `span.score_trace()`. Observation scores need both
  ids; session scores need only `session_id`. A stable `score_id` (e.g. `trace_id-name`) gives
  idempotency: re-ingestion overwrites only when id, name and date match; send the full score
  each time. The Python score docs list no `metadata` field.
- **Experiments**: `langfuse.get_dataset(name, version=)` then `dataset.run_experiment(name,
  run_name, description, task, evaluators, run_evaluators, max_concurrency, metadata)`; or
  `langfuse.run_experiment(data=[{input, expected_output}], ...)` for local data. Task is
  `def task(*, item, **kwargs)`. Item evaluator: kwargs `input, output, expected_output,
  metadata` returning `Evaluation(name, value, comment)`. Run evaluator: `item_results` ->
  `Evaluation` (value may be `None`). Item scores land on the traces; run-level scores attach
  to the dataset run. `result.format()` prints a summary. Datasets: `create_dataset`,
  `create_dataset_item` (existing `id` + `status="ARCHIVED"` archives).
- **Reading**: `langfuse.api.*` resources (async: `langfuse.async_api.*`), e.g.
  `api.observations.get_many(trace_id=, fields="core,basic,usage", limit=)`,
  `api.scores.get_many` (v5+; earlier `api.scores_v3.get_many_v3`). v5+ removes the
  `api.legacy` namespace, which self-hosted v3 servers still require.
- **Batching and failure**: tracing is asynchronous via the OTel batch span processor; SDK
  errors are caught and logged (logger `langfuse`, default WARNING; `debug=True` for more), so
  the SDK "cannot break your application". Short-lived processes must call `flush()`
  (`shutdown()` in JS). `sample_rate` (0.0-1.0) drops whole traces including their scores.
  `mask_otel_spans` hook runs on the export worker thread (keep it fast). A `tracer_provider`
  can isolate Langfuse spans; the default span filter exports Langfuse, `gen_ai.*` and known
  LLM instrumentation spans.

## 3. Public REST API

- Basic auth (public key as user, secret key as password); base `<host>/api/public`.
- Ingestion is OTLP (`POST /api/public/otel/v1/traces`); the legacy ingestion API is
  deprecated and sunsets on Cloud on 2026-11-16. Trace/observation/session v1 GETs are
  deprecated; use `GET /api/public/v2/observations` (cursor pagination, default 50, max
  1000, newest first, `fields` groups, `fromStartTime`/`toStartTime`, `filter`).
- Scores: create `POST /api/public/scores`; read `GET /api/public/v3/scores` (cursor, default
  50, max 100). Experiments: `GET /api/public/experiments`, `/experiment-items`.
- Metrics API v2 for aggregates.

## 4. Limits that matter for an adapter (Langfuse Cloud, per organization)

| Bucket | Hobby | Core | Pro/Team/Ent |
|---|---|---|---|
| Tracing (`/ingestion`, `/otel`) | 1,000/min | 4,000/min | 20,000/min |
| Datasets and experiment APIs | 100/min | 200/min | 1,000/min |
| General API (incl. observations v2) | 30/min | 100/min | 1,000/min |
| Deprecated read APIs (traces, sessions) | 15/min | 30/min | 100/min |
| Metrics v2 | 100/day | 100/hour | 500/hour |
| Trace deletion | 50/day | 200/day | 1,000/day |

Fixed (not rolling) windows shared across all projects/keys of an org; exhausted bucket
returns HTTP 429 with `Retry-After` seconds. Payload cap 5 MB per request and response on
Cloud. Self-hosted has no enforced limits. Score text max 500 chars; BOOLEAN needs explicit
`data_type`.

## 5. Implications for the adapter (input to later decisions)

1. Export first: map each Assayer Score to `create_score` with a deterministic `score_id`
   so retries are idempotent; choose target (trace, observation, session, run) explicitly.
2. Declare `data_type` explicitly for booleans and categoricals; consider score configs for
   validation of the metric catalog.
3. Writes are fire-and-forget through a background queue: the adapter needs an explicit
   `flush()` in its lifecycle and cannot rely on exceptions to detect delivery failure.
4. Ingestion (read) should use observations v2 plus `scores` reads, not the deprecated trace
   endpoints; budget for the low general-API limit (30/min on Hobby) and handle 429/Retry-After.
5. Dataset items are versioned, so an offline evaluation should pin a dataset version.
6. The singleton client and sampling both affect tests and result completeness.
7. Langfuse does not expose a Trajectory type; Trajectory must be reconstructed from
   observation trees (parent ids, types, timing) when ingesting.

## 6. Gaps (not stated in the fetched docs; verify in SDK source)

- Constructor parameters `timeout`, `flush_at`, `flush_interval`, `tracing_enabled`,
  `httpx_client`; retry/backoff and queue-size behavior of the REST client and exporter.
- Whether the Python `create_score` accepts `metadata`; exact `ExperimentResult` attributes.
- Dataset REST endpoint shapes and dataset-run/run-item fields.
- Complete list of observation types and the exact score-target options for dataset runs.

## 7. Gaps resolved against `langfuse` 5.0.2 (issue #37)

Verified in the installed SDK source; behaviour against a live server was not tested (no
credentials), so the live smoke test in `tests/integrations/test_langfuse_adapter.py` is the check.

- **`create_score` and `metadata`**: accepted (`metadata`, also `dataset_run_id`, `session_id`,
  `timestamp`, `environment`), but it is queued and never raises, so a rejected score only
  shows in the `langfuse` logger. The adapter inspects the signature and drops `metadata`
  with a report note if a future or older SDK lacks it.
- **Constructor**: `timeout`, `flush_at`, `flush_interval`, `tracing_enabled`, `httpx_client`,
  `sample_rate`, `tracer_provider`, `id_generator` and `span_exporter` exist.
  `tracing_enabled=False` makes `create_score` a no-op and `sample_rate` drops whole traces.
- **Observation ids and times**: `start_observation` cannot set a span id or a start/end
  time; ids come from the tracer's `IdGenerator`, which only a client built with its own
  provider controls. The adapter therefore posts OTLP spans itself with
  `client.api.opentelemetry.export_traces` (explicit 16-hex span ids, 32-hex trace ids,
  nanosecond times as strings, header `x-langfuse-ingestion-version: 4`), which is
  synchronous and so confirms delivery.
- **Observation types**: `span`, `generation`, `embedding`, `agent`, `tool`, `chain`,
  `retriever`, `evaluator`, `guardrail` (plus `event` through `create_event`).
- **Dataset runs**: v5 has no dataset-run-items endpoint in `client.api`. A run is the group
  of traces whose spans carry `langfuse.experiment.id`, `.name`, `.dataset.id`,
  `.item.id` and `.item.root_observation_id`. The id is
  `sha256(json(["langfuse-experiment-v1", project_id, dataset_id, run_name]))[:16]`, copied
  from `Langfuse._create_experiment_id` (private, so a drift is possible); the project id
  comes from `client.api.projects.get()`.
- **Run-level scores**: `create_score(dataset_run_id=<experiment id>)`.
- **Datasets**: `create_dataset(name=...)` upserts by name; `create_dataset_item(id=...)`
  upserts by id. `api.datasets` has `create`, `get`, `list`; `api.dataset_items` has
  `create`, `get`, `list`, `delete`.
- **Errors**: REST failures raise `langfuse.api.core.api_error.ApiError` subclasses with
  `status_code` and `headers`; transport failures raise `httpx` errors.

## Sources

- https://langfuse.com/docs/observability/data-model
- https://langfuse.com/docs/evaluation/experiments/datasets
- https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk
- https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk
- https://langfuse.com/docs/api-and-data-platform/features/public-api
- https://langfuse.com/docs/observability/sdk/python/setup
- https://langfuse.com/docs/observability/sdk/python/advanced-usage
- https://langfuse.com/faq/all/api-limits

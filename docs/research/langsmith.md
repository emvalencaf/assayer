# Research: current LangSmith data model and API

Issue: emvalencaf/assayer#6 (child of map #2). Researched 2026-10-16 against the
`langsmith` Python SDK `main` branch (PyPI latest checked: 0.14.11) and the
official LangChain docs. Sources are listed per section and at the end.

## Question

How does LangSmith model runs, traces, feedback and datasets today? What does
`assayer/integrations/langsmith.py` already use? What is the common denominator
with Langfuse for a vendor-neutral adapter?

## 1. LangSmith data model

### Run, trace, thread, project

- **Run**: "a single unit of work executed by an agent" (LLM call, prompt
  formatting, retrieval...). Comparable to an OpenTelemetry span. [1]
- **Trace**: a collection of runs for one operation, linked by a shared
  `trace_id`; limited to 25,000 runs per trace. [1]
- **Thread**: a sequence of traces forming a multi-turn session, grouped via a
  `thread_id` key in run metadata. [1]
- **Project**: container for all traces of one application. In the schema it is
  `TracerSession` (`id`, `name`, `description`, `start_time`, `end_time`,
  `extra`, `tenant_id`, `reference_dataset_id`); `Run.session_id` is the
  project id. [2] Agent-based workspaces (beta) organise by agent/environment
  instead of project. [1]

`Run` fields (schemas.py, `RunBase` + `Run`) [2]:

- Identity and tree: `id`, `name`, `trace_id`, `parent_run_id`,
  `parent_run_ids`, `dotted_order` (string of `{time}{run-uuid}` segments that
  sorts runs in execution order), `session_id`, `child_runs`.
- Content: `run_type` (a plain string: tool, chain, llm, retriever, embedding,
  prompt, parser; `RunTypeEnum` is deprecated), `inputs: dict`,
  `outputs: dict | None`, `error`, `extra` (metadata lives in
  `extra["metadata"]`), `tags`, `events`, `attachments`, `serialized`.
- Timing: `start_time`, `end_time`, `first_token_time`.
- Native usage/cost columns: `prompt_tokens`, `completion_tokens`,
  `total_tokens`, `prompt_token_details`, `completion_token_details`,
  `total_cost`, `prompt_cost`, `completion_cost`, plus `*_cost_details`.
- Linking: `reference_example_id` (the dataset example a run was produced
  from), `feedback_stats`, `status`, `in_dataset`.

### Feedback

`FeedbackBase` [2]: `id`, `run_id`, `trace_id`, `key` (metric name),
`score` (float/int/bool/None), `value` (display or non-numeric value),
`comment`, `correction`, `feedback_source`, `session_id`, `start_time`,
`comparative_experiment_id`, `feedback_group_id`, `extra` (feedback
metadata). `FeedbackSourceType` has two members: `api` and `model`. `FeedbackConfig`
declares how a key is interpreted: `type` in `continuous | categorical |
freeform`, with `min`/`max` or `categories`. [2]

Docs summary: each feedback entry is a tag plus a score, bound to a run by id;
it may be continuous or categorical. [1]

### Dataset, example, experiment

- **Dataset**: "a collection of examples used for evaluating an application".
  Schema `Dataset`: `id`, `name`, `description`, `data_type` (`kv | llm | chat`),
  `inputs_schema`, `outputs_schema`, `transformations`, `metadata`,
  `example_count`, `session_count`. [2][3]
- **Example**: `id`, `dataset_id`, `inputs`, `outputs` (reference outputs, used
  only by evaluators), `metadata`, `source_run_id`, `attachments`; creation
  also accepts `split`. [2][3]
- **Experiment**: "the result of running one application version against a
  dataset", storing outputs, evaluator scores and execution traces per
  example; many experiments per dataset. [3] In the schema an experiment is a
  project (`TracerSession`) whose `reference_dataset_id` points at the dataset,
  and each of its runs carries `reference_example_id`. [2] (The inference
  "experiment = project with reference dataset" is drawn from the schema
  fields; the concepts page does not state it in words.)
- **Evaluators** return feedback dicts (`key`, `score` or `value`, optional
  `comment`). Offline evaluators see example + run; online evaluators see only
  the run. [3]

## 2. API surface (Python SDK `langsmith.Client`)

Signatures from `python/langsmith/client.py` on `main`. [4]

- `create_run(name, inputs, run_type, *, project_name=None, revision_id=None,
  ..., **kwargs) -> None`. `run_type` is a required positional argument.
  Returns `None`: the run is enqueued for background batch ingestion, not
  returned. Other run fields (`id`, `outputs`, `start_time`, `end_time`,
  `parent_run_id`, `trace_id`, `dotted_order`, `extra`, `tags`,
  `reference_example_id`) go through `**kwargs`. The docstring example passes
  `outputs`, `end_time` inside `create_run`.
- `update_run(run_id, *, name, run_type, start_time, end_time, error, inputs,
  outputs, events, extra, tags, attachments, reference_example_id, ...)`.
- `create_feedback(run_id=None, key="unnamed", *, score, value, trace_id,
  correction, comment, source_info, feedback_source_type, source_run_id,
  feedback_id, feedback_config, project_id, comparative_experiment_id,
  feedback_group_id, extra, error, session_id, start_time,
  extend_trace_retention, ...) -> Feedback`. Notes from the docstring: batching
  and backgrounding of feedback requires `trace_id`; `session_id` (project id)
  "is required for run-level feedback; omitting it is deprecated"; `extra`
  holds feedback metadata; `comment` is intended for justification or an LLM
  judge's reasoning.
- The official migration page states `create_feedback` now **requires**
  `session_id` in every SDK and in `POST /api/v1/feedback`; `trace_id` and
  `start_time` are not required. [5]
- `create_dataset(dataset_name, *, description, data_type=kv, inputs_schema,
  outputs_schema, transformations, metadata, ...) -> Dataset`;
  `create_examples(...)`, `create_example(...)`, `list_examples(...)`,
  `read_dataset(...)`.
- `evaluate(target, /, data, evaluators, summary_evaluators, metadata,
  experiment_prefix, description, max_concurrency, num_repetitions, blocking,
  upload_results, ...)`: the high-level path that creates the experiment
  project, runs the target per example, and writes feedback.
- Also present: `read_project`, `create_project`, `list_runs`, `read_run`,
  `list_feedback`, `get_experiment_results`.

## 3. What `assayer/integrations/langsmith.py` uses today

`LangSmithPublisher.publish(result, dataset_name)` per `RunResult`:

1. `client.create_run(name=experiment_name, inputs=run.input,
   outputs=run.output, metadata={input_tokens, output_tokens, cost_usd})`.
2. Per `FieldEvaluation`: `client.create_feedback(run_id=run.id,
   key=f"{field_name}/{evaluator_method}", score=score,
   comment=json.dumps(metadata + prompt_hash))`.

`make_langsmith_publisher()` checks `LANGCHAIN_API_KEY` then calls
`langsmith.Client()`.

Mapping today: experiment name -> run name (one flat run per `RunResult`, no
parent/child tree, no trajectory); token counts and cost -> metadata; field
score -> feedback `score`; evaluator metadata and `prompt_hash` -> JSON string
in feedback `comment`.

### Gaps against the current SDK

These follow from comparing the file with the signatures in section 2.
They were not executed against a live LangSmith.

1. **`run_type` is missing.** It is a required positional argument of
   `create_run`; the call as written would raise `TypeError`.
2. **`metadata=` is not a named parameter**; run metadata belongs in
   `extra={"metadata": {...}}`. It would be swallowed by `**kwargs` and, at
   best, not land where the UI reads it.
3. **`create_run` returns `None`**, so `run.id` fails with `AttributeError`.
   The caller must generate the run `id` (UUID) up front and pass it, then
   reuse it for feedback. Tests with a mocked client will not catch 1-3.
4. **Tokens and cost are not in native fields.** LangSmith has first-class
   `prompt_tokens`, `completion_tokens`, `total_tokens`, `total_cost` on runs
   (usually derived from `usage_metadata` on llm runs); metadata hides them
   from cost dashboards.
5. **`dataset_name` is unused.** No dataset, example or experiment project is
   created and no `reference_example_id` is set, so results are not linked to a
   dataset or comparable as an experiment in the UI.
6. **No `session_id`/`project_name`.** Runs go to the default project, and
   `create_feedback` omits `session_id`, which is now required [5].
7. **Runs are never ended**: no `end_time`/`start_time` set; the UI would show
   them as pending or with arbitrary timing.
8. **Feedback metadata is packed into `comment` as JSON**; the dedicated
   `extra` field (feedback metadata) is the intended place, keeping `comment`
   for human-readable justification.
9. Env var: file requires `LANGCHAIN_API_KEY` (legacy name; the SDK docstring
   still documents it as a default). Newer `LANGSMITH_*` names are the
   current convention in the SDK; accept both.
10. Feedback key `field/evaluator_method` mixes two dimensions into one string
    (see adapter notes).

## 4. Langfuse counterpart (for the common denominator)

Sourced from Langfuse docs [6][7][8]:

- **Trace**: one request/operation; groups **observations** sharing a
  `trace_id`. Observation types include span, generation (LLM), event; they
  nest. **Session** optionally groups traces (chat thread). [6]
- **Score**: `name`, `value`, `data_type` (`NUMERIC`, `CATEGORICAL`, `BOOLEAN`,
  also `TEXT` on the SDK page), `trace_id` (required for trace/observation
  scores), `observation_id`, `session_id`, `comment`, `score_id` (idempotency
  key), `config_id`. [7] Run-level evaluator scores attach to the DatasetRun. [8]
- **Dataset** -> n **DatasetItem** (`input`, `expectedOutput`, `metadata`,
  `sourceTraceId`, `status`); **DatasetRun** (an experiment execution:
  `id`, `name`, `datasetId`, `description`, `metadata`) -> n **DatasetRunItem**
  (`datasetRunId`, `datasetItemId`, `traceId`, optional `observationId`). One
  item appears once per run; repetitions are not supported yet. [8]

## 5. Common denominator

| Concept | LangSmith | Langfuse | Neutral name |
|---|---|---|---|
| Unit of work | run (`run_type`, `parent_run_id`) | observation (span/generation/event) | step |
| One execution | trace (`trace_id`, root run) | trace | trace |
| Multi-turn grouping | thread (`thread_id` metadata) | session | session |
| Score | feedback (`key`, `score`, `value`, `comment`, `extra`) | score (`name`, `value`, `data_type`, `comment`) | score |
| Score target | `run_id` (+`session_id`) | `trace_id`/`observation_id`/`session_id`/dataset run | trace or step |
| Test set | dataset / example (`inputs`, `outputs`) | dataset / item (`input`, `expectedOutput`) | dataset / case |
| Experiment | project with `reference_dataset_id`, runs have `reference_example_id` | DatasetRun + DatasetRunItem(`traceId`) | experiment |
| Grouping container | project | (project is the API key scope) | n/a |
| Usage/cost | native run token and cost fields | native generation usage/cost (not verified here) | usage |

Differences that matter for the adapter:

- LangSmith ties example -> run via `reference_example_id` on the run;
  Langfuse ties it via a separate DatasetRunItem record (item + trace).
- LangSmith feedback is addressed by run and needs project (`session_id`);
  Langfuse scores are addressed by trace (observation optional).
- Langfuse has typed score data types; LangSmith expresses the same through
  `score` vs `value` plus optional `FeedbackConfig`.
- LangSmith run ids and trace ids are client-generated UUIDs (the SDK enqueues
  asynchronously); the adapter should own id generation in both backends.
- Langfuse does not support repetitions of one item in a run; LangSmith has
  `num_repetitions` in `evaluate`. Assayer's consistency pipeline (k repeats)
  must map to separate runs/traces, possibly separate dataset runs.

Minimal neutral contract implied by the intersection: create/get a dataset of
cases (input, expected output, metadata); open an experiment against it;
record a trace per case (input, output, optional steps, token/cost usage,
metadata, optional link to the case); attach named scores (numeric, boolean or
categorical, comment, metadata) to a trace; flush. Trajectory (step tree)
maps to run tree (LangSmith) and observation tree (Langfuse).

## 6. Open questions for later tickets

- Is the SDK's `Client.evaluate`/`RunTree` the intended publish path, or the
  low-level `create_run`/`update_run`? `RunTree` handles `trace_id` and
  `dotted_order` for child runs; the raw client requires the caller to compute
  them.
- Langfuse usage/cost field names were not verified in this pass.
- Live-API behaviour was not tested (no credentials); gaps in section 3 are
  derived from SDK signatures and docs.

## Sources

1. LangSmith observability concepts: https://docs.langchain.com/langsmith/observability-concepts
2. `langsmith/schemas.py` (`main`): https://raw.githubusercontent.com/langchain-ai/langsmith-sdk/main/python/langsmith/schemas.py
3. LangSmith evaluation concepts: https://docs.langchain.com/langsmith/evaluation-concepts
4. `langsmith/client.py` (`main`): https://raw.githubusercontent.com/langchain-ai/langsmith-sdk/main/python/langsmith/client.py
5. Feedback create migration: https://docs.langchain.com/langsmith/smithdb-sdk-migration-feedback
6. Langfuse data model: https://langfuse.com/docs/observability/data-model
7. Langfuse scores via SDK: https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk
8. Langfuse experiments data model: https://langfuse.com/docs/evaluation/experiments/data-model

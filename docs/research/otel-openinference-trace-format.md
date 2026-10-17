# Research: OpenTelemetry GenAI and OpenInference as a vendor-neutral trace format

Issue: emvalencaf/assayer#8 (child of map #2). Researched 2026-10-16.

## Question

Can the OpenTelemetry GenAI semantic conventions and OpenInference serve as a neutral
agent-trajectory format (LLM, tool and agent spans)? What do they cover, what is missing,
and how do Langfuse and LangSmith relate to them?

## Short answer

- Both can carry a trajectory's structure (agent run, LLM calls, tool calls) as a tree of
  OpenTelemetry spans. Neither defines a "trajectory" object: it is reconstructed from the
  span tree (parent/child plus start time).
- OTel GenAI is the standards-track option, but its span conventions are still marked
  **Development** (unstable; names may change). OpenInference is an Arize-maintained
  attribute set that predates it, with a richer span-kind vocabulary.
- Both are lossy for evaluation needs: no scores, no expected output / reference, no
  dataset or run linkage in the span conventions read. These must come from Assayer's own
  model.
- Langfuse and LangSmith both ingest OTLP and understand `gen_ai.*` and (to varying
  degree) OpenInference, but each prefers its own namespace (`langfuse.*`, `langsmith.*`).
  Neither is a pure OTel/OpenInference store.
- Recommendation for the adapter design: treat OTel/OpenInference as an **interchange and
  import reference**, keep Assayer's own Trajectory model as the source of truth, and map
  to/from the two conventions at the edge.

## 1. OpenTelemetry GenAI semantic conventions

### Where they live and their status

- The pages under opentelemetry.io/docs/specs/semconv/gen-ai/ now only say the conventions
  "have moved to the OpenTelemetry GenAI semantic conventions repository"
  (https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/,
  https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/).
- New home: https://github.com/open-telemetry/semantic-conventions-genai (Apache-2.0). It
  covers spans, metrics and events for GenAI clients, MCP and provider-specific
  conventions; `docs/gen-ai/` holds inference, agents, tool execution, evaluation and MCP;
  `model/` holds the YAML source. The repo page does not state a maturity level.
- The span pages are marked **Status: Development**:
  https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md,
  .../gen-ai-agent-spans.md, .../client-inference.md.
  Consequence: pin a convention version and expect renames.

### Span types relevant to a trajectory

From gen-ai-agent-spans.md, gen-ai-spans.md and client-inference.md (all under
`docs/gen-ai/` in the repo above). Operation is `gen_ai.operation.name`.

| Concept | Operation | Span kind | Span name |
|---|---|---|---|
| LLM call | `chat`, `text_completion`, `generate_content` | CLIENT (INTERNAL if in-process) | `{operation} {gen_ai.request.model}` |
| Agent run (remote service) | `invoke_agent` | CLIENT | `invoke_agent {gen_ai.agent.name}` |
| Agent run (in-process framework) | `invoke_agent` | INTERNAL | same |
| Multi-agent / multi-step workflow | `invoke_workflow` | INTERNAL | `invoke_workflow {gen_ai.workflow.name}` |
| Planning | `plan` | INTERNAL | `plan {gen_ai.agent.name}` |
| Agent definition | `create_agent` | CLIENT | `create_agent {gen_ai.agent.name}` |
| Tool call | `execute_tool` | INTERNAL | `execute_tool {gen_ai.tool.name}` |
| Retrieval | `retrieval` | CLIENT | `retrieval {gen_ai.data_source.id}` |
| Embeddings | `embeddings` | CLIENT | `embeddings {gen_ai.request.model}` |
| Memory | `create_memory`, `search_memory`, ... | CLIENT/INTERNAL | `{operation}` |

Workflow spans SHOULD NOT be emitted for standalone agent invocations; plan spans only
when planning can be reliably identified.

### Key attributes

- Always: `gen_ai.operation.name`; `gen_ai.provider.name` on client spans (e.g. `openai`,
  `anthropic`, `aws.bedrock`, `gcp.gemini`).
- Agent: `gen_ai.agent.id` (stable provider id, not an in-memory id), `gen_ai.agent.name`,
  `gen_ai.agent.description`, `gen_ai.agent.version`, `gen_ai.workflow.name` (low
  cardinality), `gen_ai.conversation.id` (only when a real id exists; UUID or trace-id
  fallbacks are prohibited).
- Tool (`execute_tool`): required `gen_ai.tool.name`; recommended `gen_ai.tool.call.id`,
  `gen_ai.tool.description`, `gen_ai.tool.type`; opt-in `gen_ai.tool.call.arguments`,
  `gen_ai.tool.call.result`.
- LLM: `gen_ai.request.model`, `gen_ai.response.model`, request settings
  (`gen_ai.request.temperature`, `top_p`, `max_tokens`, `seed`, ...),
  `gen_ai.response.finish_reasons`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`
  (input includes cached tokens; cache/audio/image subtypes exist), `error.type`.
- Content, all **opt-in** (sensitive): `gen_ai.input.messages`, `gen_ai.output.messages`,
  `gen_ai.system_instructions`, `gen_ai.tool.definitions`. Messages are arrays with `role`
  and `parts`; part types include `text`, `tool_call` (`id`, `name`, `arguments`) and
  `tool_call_response` (`id`, `response`). Content capture is off by default; the options
  are none, on-span, or external storage with references (the external pattern is a TODO
  in the spec).
- Related signals: metrics (`gen_ai.client.inference.duration`, token usage) and an event
  `gen_ai.client.inference.operation.details` (DEBUG) for content outside traces.

### Fit and gaps for trajectories

Covers: hierarchical agent -> LLM -> tool structure, tool-call arguments and results,
token usage, errors, conversation grouping, model and provider identity.

Missing or weak:
- No first-class trajectory or step concept; ordering and branching come from span
  parentage and timestamps.
- Content is opt-in, so a trace may legitimately lack the inputs/outputs evaluation needs.
- No score, reference/expected output, dataset item or experiment run id in the span
  pages read. (The repo scope mentions "evaluation"; that page was not read, so verify.)
- Development status, and the home repository has just moved.

## 2. OpenInference

Source: https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md

- Attribute conventions for OTel spans, from Arize. They define keys that populate the
  `attributes` of OTel spans/events; structured lists are flattened to indexed keys
  `<prefix>.<index>.<suffix>` because OTel attributes hold only simple values.
- `openinference.span.kind` is required on every span: `LLM`, `EMBEDDING`, `CHAIN`,
  `RETRIEVER`, `RERANKER`, `TOOL`, `AGENT`, `GUARDRAIL`, `EVALUATOR`, `PROMPT`,
  `DECISION`. It is a hint to the backend for assembling the trace.
- Messages: `llm.input_messages.<i>.message.role|content`,
  `llm.output_messages.<i>.message.*`, multipart `message.contents.<j>.message_content.*`,
  tool calls `message.tool_calls.<k>.tool_call.id|function.name|function.arguments`, tool
  results via `message.tool_call_id`, `message.name`.
- Tools: advertised `llm.tools.<i>.tool.name|description|json_schema`; on TOOL spans
  `tool.name`, `tool.description`, `tool.parameters`, `tool.id`.
- Tokens/cost: `llm.token_count.prompt|completion|total` (plus `prompt_details.cache_read|
  cache_write|audio`, `completion_details.reasoning|audio`), `llm.cost.*`.
- Session/user: `session.id`, `user.id`. Agent/graph: `agent.name`, `graph.node.id`,
  `graph.node.name`, `graph.node.parent_id`.

Compared to OTel GenAI: richer span kinds (retriever, reranker, guardrail, evaluator,
chain), explicit graph-node attributes for agent graphs, and flattened keys instead of
structured JSON. Attribute names differ, so the two are not interchangeable; a converter
is required. It has an `EVALUATOR` span kind, but the page read defines no score or
reference attributes.

## 3. Langfuse and LangSmith

### Langfuse

Source: https://langfuse.com/integrations/native/opentelemetry

- Ingests OTLP over HTTP (JSON/protobuf, no gRPC) at `/api/public/otel`
  (`/api/public/otel/v1/traces`), Basic Auth; header `x-langfuse-ingestion-version: 4` for
  real-time ingestion.
- Attribute precedence: `langfuse.*` first (direct map to its data model); `gen_ai.*`
  supported (prompt/completion, model, usage, cost; the page notes the spec is still
  evolving); OpenInference-style `input.value`, `output.value`, `llm.model_name`,
  `llm.token_count.*`, `llm.invocation_parameters.*` are read, though the page does not
  claim full OpenInference support; `mlflow.*` also mapped.
- Observation type: a recognized `langfuse.observation.type` (span, generation, event,
  embedding, agent, tool, chain, retriever, guardrail, evaluator) wins; otherwise
  `gen_ai.operation.name`, then model-based inference, then `span`.
- Caveats: trace-level attributes (user, session, tags) must be on every span; metadata is
  nested under `metadata.attributes` unless `langfuse.*.metadata.` keys are used; a root
  span is required; Collector filtering can orphan traces.

### LangSmith

Source: https://docs.langchain.com/langsmith/trace-with-opentelemetry

- OTLP/HTTP at `https://api.smith.langchain.com/otel` (`/v1/traces` appended), header
  `x-api-key`, project via `Langsmith-Project`. SDK toggles `LANGSMITH_OTEL_ENABLED`,
  `LANGSMITH_OTEL_ONLY` (needs `langsmith>=0.4.1`).
- Reads `langsmith.*` (e.g. `langsmith.span.kind`, `langsmith.trace.session_name`,
  `langsmith.metadata.{key}`), `gen_ai.*` (including `gen_ai.prompt.{n}.*`,
  `gen_ai.input.messages`, `gen_ai.output.messages`, `gen_ai.tool.name`, `gen_ai.usage.*`),
  `traceloop.*`, OpenInference (`input.value`, `output.value`, `openinference.span.kind`,
  `llm.*`, `tool.name`), Logfire and span events.
- Run-type mapping: `langsmith.span.kind` in `llm|chain|tool|retriever|embedding|prompt|parser`;
  `gen_ai.operation.name` `chat|completion` -> llm, `embedding` -> embedding;
  `gen_ai.tool.name` -> tool. The per-value mapping of `openinference.span.kind` is not
  documented on the page, and no mapping is listed for `invoke_agent` / `execute_tool`
  operation values.
- Limits: orphaned child spans are dropped silently; OTLP span ids (8 bytes) do not become
  LangSmith run UUIDs, so nesting under an existing run needs manual
  `langsmith.trace.id`/`span.id`/`span.parent_id`/`span.dotted_order`; agent addressing is
  unavailable on the OTLP path.

### Relationship summary

| | OTel GenAI | OpenInference | Langfuse | LangSmith |
|---|---|---|---|---|
| Ingests OTLP | n/a (format) | n/a (format) | yes (HTTP) | yes (HTTP) |
| Reads `gen_ai.*` | defines | no | yes | yes |
| Reads OpenInference | no | defines | partly (`input.value`, `llm.*`) | yes |
| Preferred native namespace | - | - | `langfuse.*` | `langsmith.*` |
| Agent/tool types | `invoke_agent`, `execute_tool` | `AGENT`, `TOOL` | agent, tool observation types | tool run type; no agent run type listed |

## Implications for Assayer

1. A vendor-neutral export is feasible: emit OTLP spans using `gen_ai.*` (`invoke_agent`,
   `chat`, `execute_tool`), optionally also OpenInference attributes. Both backends accept
   OTLP, but each yields better results with its own namespace, so the adapter likely
   needs a thin per-backend enrichment layer.
2. Do not make an OTel span tree the domain model: it is Development-status, content
   capture is opt-in, and scores/references are absent. Keep Trajectory in Assayer and
   treat OTel/OpenInference as import/export formats.
3. Scores must be attached through backend-specific APIs (outside these conventions); the
   adapter contract must include them separately.
4. For later ingestion (reading traces), expect both `gen_ai.*` and OpenInference dialects
   plus missing content; a normalizer is needed.
5. Map #2 keeps OTel as a "format reference" only (generic OTel destination out of
   scope); this research supports that scoping.

## Not verified

- The truncated tails of gen-ai-agent-spans.md (about 47k characters, including skill and
  execute_tool sections) and client-inference.md (about 16k characters) were not read.
- The OTel GenAI evaluation conventions page was not read.
- No maturity roadmap for OTel GenAI was found.
- Instrumentation libraries (which attribute names they emit today) were not investigated.

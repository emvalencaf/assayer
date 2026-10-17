---
type: Reference
title: Examples and live evaluation
description: The runnable offline examples, and why live (online) evaluation is assembled from Runner.score rather than built in.
resource: examples/
tags: [examples, live-evaluation, historical-evaluation]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T22:30:00Z }
sources:
  - id: readme
    resource: README.md
    title: README sections "Examples" and "Historical and live evaluation"
  - id: examples
    resource: examples/
    title: Example scripts
---

# Overview

`examples/` holds runnable scripts that need no network or API key.[^examples] The README lists them in a table.[^readme]

| Script | Shows |
|---|---|
| `ticket_classification.py` | a custom `Metric` plus a built-in metric on one Field |
| `ner_extraction.py` | pure NER: `EntitySpan`s scored with entity-level macro F1 through `corpus_metric` |
| `support_pipeline.py` | one structured output scored per Field: classification, NER and text generation (ROUGE-L) |
| `schema_structured_output.py` | a field map drafted with `schema_to_field_map` from a JSON Schema, adjusted and passed to `Runner(field_metrics=...)`; see [Per-Field measurement](field-measurement.md) |
| `agent_tool_use.py` | agent metrics on a `Trajectory`, then two agents compared on quality and cost with `compare` and `PricingConfig` |
| `faithfulness_check.py` | `make_faithfulness` with a scripted Judge |
| `logged_traffic_scoring.py` | live traffic captured in a log and scored in batches |

# Historical and live evaluation

* **Historical (offline):** `Runner.run(dataset)` calls the target; `Runner.score(dataset, outputs)` scores outputs collected earlier without calling it. See [Runner](runner.md), [Comparison](comparison.md) and [Adapters](adapters.md).
* **Live (online):** Assayer has no live mode. No hook scores each request as it is served, and none is planned for now (it is an open item in the README roadmap). To build one, capture each interaction as a `Trajectory` in the app, and have a job call `Runner(metrics=...).score(Dataset(...), trajectories)` on a batch or a sample. Production traffic seldom has a reference answer, so use reference-free metrics: custom rules, [Judge metrics](../metrics/judge-metrics.md), faithfulness, cost and latency checks. `logged_traffic_scoring.py` is a minimal version of that loop.

[^readme]: README.md
[^examples]: examples/

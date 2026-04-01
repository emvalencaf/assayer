---
id: assayer-core
status: draft
created: 2026-03-30
updated: 2026-03-30
---

# PRD: Assayer — LLM Evaluation and Observability Core Platform

## Problem Statement
Teams building LLM-powered applications lack a systematic, reproducible way to evaluate model output quality. Current approaches are ad hoc: isolated scripts, manually computed metrics, no experiment history, and no cost visibility per call. This makes it impossible to compare experiments, detect quality regressions, or justify model switches with data. The problem is compounded when a single chain produces mixed structured output — combining chat responses, classification labels, and named entities — each requiring a different evaluation strategy. Additionally, fields like free-text responses are prone to hallucination, and without field-level audit trails, it is impossible to understand what was evaluated, how, and with what result.

## Goals
- Enable developers to define and run reproducible LLM evaluation pipelines, supporting datasets, evaluators, and metrics as first-class composable objects.
- Support evaluation of chains that produce mixed structured outputs: chat responses, classification labels, and named entity spans — each output field evaluated by the appropriate method.
- Provide built-in metrics for chat quality (BLEU, ROUGE-L, BERTScore, semantic similarity) alongside classification metrics (accuracy, precision, recall, F1) and NER metrics (entity-level F1 by type, macro F1).
- Support hallucination detection through both model-based (LLM-as-Judge) and reference-based methods (factual consistency scoring, faithfulness checks).
- Produce fully auditable evaluation results: for every evaluated output field, record the evaluation method used, the expected value, the obtained value, and a stable reference to any prompt used (via hash).
- Track token cost (input tokens, output tokens, estimated USD cost) per run and enable cross-experiment cost comparison via LangSmith.
- Allow extension with custom metrics and custom evaluator types without modifying core library code.

## Non-Goals
- Assayer does not train or fine-tune models.
- Assayer does not provide its own UI — visualization is delegated to LangSmith.
- Assayer does not manage LLM inference directly (no model hosting).
- Assayer does not issue billing — token cost tracking is observational only.
- Authentication, access control, and multi-tenancy are out of scope for this version.
- Async / streaming execution is out of scope for this version.

## Users & Scenarios

### Scenario 1: Chat quality evaluation
> As an ML engineer, I want to run an evaluation on a dataset of conversation turns and obtain quality scores per turn, so that I can compare two prompt variants and pick the best one.

### Scenario 2: Classification evaluation
> As a data scientist, I want to evaluate an LLM classifier on a labeled example set using accuracy, precision, recall, and F1, so that I can report standardized metrics to the product team.

### Scenario 3: NER evaluation
> As an NLP engineer, I want to compare entities extracted by the model against reference entities and get F1 per entity type, so that I can identify where the model underperforms.

### Scenario 4: Mixed structured output evaluation
> As an ML engineer, I want to evaluate a chain that returns a structured object containing a chat reply, a classification label, and a list of named entities in a single call, so that each output field is evaluated by the appropriate method without me wiring three separate pipelines.

### Scenario 5: Hallucination detection
> As a researcher, I want to flag responses where the model introduces facts not supported by the provided context, so that I can quantify hallucination rates across experiments without relying solely on LLM-as-Judge.

### Scenario 6: LLM-as-Judge
> As a researcher, I want to use a judge model (e.g. GPT-4o) to evaluate subjective responses from my target model using a default built-in system prompt, so that I can obtain quality scores without writing a judging prompt from scratch or providing manual ground truth for every example.

### Scenario 7: Token cost comparison
> As a tech lead, I want to compare the average input and output token cost between two models running on the same dataset, so that I can make data-driven cost-benefit decisions.

### Scenario 8: Custom metric registration
> As a developer, I want to register my own metric function and use it in the evaluation pipeline by name, so that I can incorporate business-specific logic without forking the library.

### Scenario 9: Audit trail review
> As a QA analyst, I want to inspect every evaluated output field and see which evaluation method was used, what the expected value was, what the model produced, and — when a judge prompt was involved — a stable reference to the exact prompt version used, so that I can trust and explain evaluation results to stakeholders.

## Acceptance Criteria

- [ ] AC-001: Given a dataset with at least 10 chat examples (JSON format), the Runner executes the target function on all examples synchronously and returns an `ExperimentResult` with per-run scores in under 60 s (excluding LLM API latency).
- [ ] AC-002: Built-in chat metrics (`bleu`, `rouge_l`, `bert_score`, `semantic_similarity`) produce values within ±0.01 of reference implementations for the same inputs.
- [ ] AC-003: `semantic_similarity` uses a default embedding model (configurable by the user at pipeline construction time) and returns a cosine similarity score between 0 and 1.
- [ ] AC-004: Built-in classification metrics (`accuracy`, `precision`, `recall`, `f1`) produce values within ±0.001 of scikit-learn reference implementations for binary and multi-class tasks.
- [ ] AC-005: The NER evaluator computes entity-level F1 (exact match) per entity type and macro F1, comparing predicted entities against reference entities.
- [ ] AC-006: A chain that returns a structured output containing a chat field, a classification field, and an NER field can be evaluated in a single pipeline run, with each field evaluated by its designated evaluator.
- [ ] AC-007: The hallucination evaluator provides at least one reference-based method (faithfulness / factual consistency scoring against a provided context) in addition to LLM-as-Judge.
- [ ] AC-008: The `LLMJudgeEvaluator` ships with a built-in default system prompt; users may override it with a custom prompt. When a custom prompt is provided, its SHA-256 hash is computed and stored in the `FieldEvaluation` record.
- [ ] AC-009: Every `FieldEvaluation` record exposes: `field_name: str`, `evaluator_method: str`, `expected_value: Any`, `obtained_value: Any`, `score: float`, `prompt_hash: str | None`, and `metadata: dict`.
- [ ] AC-010: Every `RunResult` contains `input_tokens: int`, `output_tokens: int`, and `cost_usd: float | None`, populated from LLM call metadata.
- [ ] AC-011: `ExperimentResult.compare(other: ExperimentResult)` returns a dict with per-metric deltas and average token cost delta between two experiments.
- [ ] AC-012: A custom `Metric` can be registered via `MetricRegistry.register(name, fn)` and used in the Runner by name, without modifying library files.
- [ ] AC-013: A custom `Evaluator` can be created by subclassing `BaseEvaluator`, registered via `EvaluatorRegistry.register(name, cls)`, and used in the Runner by name.
- [ ] AC-014: All experiment results are pushed to LangSmith with the experiment name, per-evaluator scores, tokens, cost, and field-level audit records per run.
- [ ] AC-015: Unit test coverage for core modules (evaluators, metrics, runner) is ≥ 90% as measured by pytest-cov.

## Assumptions
- Users have a valid LangSmith API key configured via the `LANGCHAIN_API_KEY` environment variable.
- The target function returns objects that expose usage metadata compatible with the LangChain/LangSmith standard (`usage_metadata` with `input_tokens` and `output_tokens` fields).
- The execution environment has internet access to reach the LangSmith API and the judge LLM API.
- Structured output fields are declared by the user when configuring the pipeline (the library does not auto-detect output types).
- All evaluation execution is synchronous; async support is explicitly deferred.
- Local datasets are provided in JSON format (list of objects with `input` and `expected_output` keys).

## Open Questions
- None — all open questions from previous review have been resolved (see Assumptions).

## Out of Scope
- Command-line interface (CLI) — may be added in a future PRD.
- Integration with backends other than LangSmith (MLflow, Weights & Biases, etc.).
- Streaming evaluation (token-by-token) and async execution.
- Multi-turn conversation evaluation beyond turn-level scoring.
- Custom dashboards or reports beyond what LangSmith natively provides.

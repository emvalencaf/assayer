---
id: consistency-evaluator
status: approved
created: 2026-04-07
updated: 2026-04-07
---

# PRD: Consistency Evaluator

## Problem Statement

LLM-powered applications exhibit output variability even when prompts are well-structured and outputs are constrained via schemas or function calling. A classifier that returns "BILLING" 80% of the time and "TECH" 20% of the time for the same input is not reliable — but this oscillation is invisible to existing evaluation pipelines, which evaluate each record in isolation and report aggregate accuracy without any notion of stability per input.

Teams have no systematic way to measure how consistently an LLM produces the same output across repeated runs for the same input, whether detected through historical production logs or through deliberate repeated execution during evaluation. Without this measurement, it is impossible to distinguish inputs that are inherently ambiguous from inputs where the model is simply unreliable.

## Goals

- Enable measurement of output consistency across repeated LLM runs for the same input, using either historical data or live repeated execution.
- Expose per-group consistency metrics — agreement rate, label entropy, score standard deviation, correct rate, pass@k, and recall@k — alongside the number of observations that back each measurement.
- Integrate with the existing `Evaluator` interface so that any built-in or custom evaluator can be wrapped without modification.
- Allow users to specify any dataset field as the grouping key, so that existing datasets do not require schema changes.
- Allow users to filter out groups with insufficient observations via a configurable minimum-k threshold.
- Surface which inputs are the most unstable, enabling targeted prompt improvement or input triage.

## Non-Goals

- `ConsistencyEvaluator` does not implement its own scoring logic — it delegates all evaluation to the wrapped `Evaluator`.
- This PRD does not cover consistency of chain-of-thought reasoning paths — only final output labels and scores.
- Automatic root-cause analysis of why a case is inconsistent (aleatoric vs. epistemic uncertainty) is out of scope.
- Async or parallel execution of the k repeated runs is out of scope for this version.
- Pushing per-group consistency results to LangSmith as a new experiment type is deferred to a future PRD.

## Users & Scenarios

### Scenario 1: Auditing a production classifier with historical data
> As an ML engineer, I want to pass a historical dataset of logged predictions — grouped by a field of my choosing (e.g. `ticket_id`, `session_id`) — through a `ConsistencyEvaluator` so that I can identify which inputs my classifier handles inconsistently across production runs.

### Scenario 2: Measuring prompt stability during development
> As a prompt engineer, I want to wrap my evaluator with a `ConsistencyEvaluator` in live mode and run it with `k=5` so that I can detect whether my prompt produces stable outputs before deploying to production.

### Scenario 3: Filtering groups with insufficient data
> As a data scientist, I want to configure a `min_k=3` threshold so that groups with fewer than 3 historical observations are excluded from consistency metrics, avoiding misleading agreement rates from single-run groups.

### Scenario 4: Wrapping a custom evaluator
> As a developer, I want to wrap my custom `Evaluator` subclass with `ConsistencyEvaluator` without modifying it, so that I can measure consistency on domain-specific scoring logic.

### Scenario 6: Measuring entity coverage across k NER runs
> As an NLP engineer, I want to evaluate a NER model in live mode with `k=5` so that I can measure what fraction of the reference entities the model can extract across repeated attempts, even if no single run extracts all of them.

### Scenario 5: Comparing consistency across experiments
> As a tech lead, I want to compare the mean agreement rate between two prompt versions evaluated over the same historical dataset, so that I can choose the more stable one for production.

## Acceptance Criteria

- [ ] AC-001: `ConsistencyEvaluator` accepts any object implementing the `BaseEvaluator` interface as its `evaluator` argument and wraps it without requiring any modification to the wrapped class.
- [ ] AC-002: In **historical mode**, `ConsistencyEvaluator.evaluate_dataset(dataset, group_by)` groups records by the field named in `group_by` (an arbitrary string — e.g. `"ticket_id"`, `"session_id"`, `"input_hash"`), runs the wrapped evaluator once per record within each group, and returns a `ConsistencyFieldEvaluation` per group.
- [ ] AC-003: In **live mode**, `ConsistencyEvaluator.evaluate_live(target_fn, input, reference)` calls `target_fn(input)` exactly `k` times (where `k` is configured at construction time), runs the wrapped evaluator once per returned prediction, and returns a single `ConsistencyFieldEvaluation`. `target_fn` has the signature `Callable[[Any], str]`.
- [ ] AC-004: Each `ConsistencyFieldEvaluation` exposes: `group_key: str | None`, `n: int`, `agreement_rate: float` (range 0.0–1.0), `dominant_label: str | None`, `entropy: float`, `score_std: float`, `correct_rate: float`, `pass_at_k: bool`, `recall_at_k: float`, and `raw_results: list[FieldEvaluation]`.
- [ ] AC-005: `agreement_rate` is computed as `count(dominant_label) / n`. When all labels are identical, `agreement_rate == 1.0`.
- [ ] AC-006: `entropy` is computed as `H = -Σ p(x) · log₂(p(x))` over the label distribution within the group. When all labels are identical, `entropy == 0.0`.
- [ ] AC-007: `score_std` is the standard deviation of the numeric `score` field across raw results within the group. When `n == 1`, `score_std == 0.0`.
- [ ] AC-008: `correct_rate` is computed as `count(runs where prediction exactly matched reference) / n`. For single-label outputs, exact string equality is used. For multi-label outputs (e.g. NER), exact set equality is used.
- [ ] AC-009: `pass_at_k` is `True` if at least one of the n runs produced a prediction that exactly matched the reference; `False` otherwise. Applies to both single-label and multi-label outputs.
- [ ] AC-010: `recall_at_k` is computed as `|union(all predicted labels across n runs) ∩ reference_labels| / |reference_labels|`. For single-label outputs, `recall_at_k` equals `1.0` if `pass_at_k` is `True`, else `0.0`. For multi-label outputs, it measures what fraction of the reference set the model covered across all k attempts.
- [ ] AC-011: When `min_k` is set, groups with `n < min_k` are excluded from the output of `evaluate_dataset` and a warning is emitted listing the excluded group key values.
- [ ] AC-012: If a record in the dataset is missing the field specified in `group_by`, `evaluate_dataset` raises a `ValueError` identifying the offending record index. Missing values are not silently ignored.
- [ ] AC-013: `evaluate_dataset` returns a `ConsistencySummary` containing: `per_group: list[ConsistencyFieldEvaluation]`, `mean_agreement_rate: float`, `mean_entropy: float`, `mean_score_std: float`, `mean_correct_rate: float`, `pass_at_k_rate: float` (proportion of groups where `pass_at_k` is `True`), `mean_recall_at_k: float`, and `worst_groups: list[ConsistencyFieldEvaluation]` (groups with the lowest `agreement_rate`, top-10 by default).
- [ ] AC-014: `ConsistencyEvaluator` can be instantiated and used with any registered built-in evaluator (`ClassificationEvaluator`, `LLMJudgeEvaluator`, `NERJudgeEvaluator`, `FaithfulnessEvaluator`) without code changes to those evaluators.
- [ ] AC-015: Unit test coverage for `ConsistencyEvaluator` and its supporting data models is ≥ 90% as measured by pytest-cov.
- [ ] AC-016: `ConsistencyEvaluator` and all supporting types carry Google-style docstrings and full type hints.

## Assumptions

- The wrapped `Evaluator` is deterministic enough that differences across k runs are meaningful signal, not infrastructure noise (e.g., network timeouts that silently return wrong labels).
- In historical mode, the field specified in `group_by` is present in every record of the dataset; missing values raise an error.
- In live mode, calling `target_fn` k times for the same input is acceptable — the caller is responsible for understanding the token cost implications (k × inference cost).
- Label-based metrics (`agreement_rate`, `dominant_label`, `entropy`) apply when the `FieldEvaluation` carries a `label` field (single-label) or a `labels` field (multi-label). Score-based metrics (`score_std`) apply when it carries a numeric `score` field. Both may be present simultaneously.
- `recall_at_k` requires the reference to expose a set of labels (multi-label). For single-label references, it degenerates to `1.0` if `pass_at_k` else `0.0`.
- The dataset in historical mode is provided as a list of dicts (same format as existing local datasets in Assayer).

## Open Questions

- Should `worst_groups` in `ConsistencySummary` be configurable (e.g., top-N by lowest agreement rate) or always return all groups below a fixed threshold? Proposed default: top-10 by ascending `agreement_rate`.
- Should `evaluate_dataset` in historical mode also accept a LangSmith dataset reference (by name or ID), or only local list-of-dicts for this version?

## Out of Scope

- Async or parallel execution of k repeated runs in live mode.
- LangSmith integration for pushing `ConsistencySummary` results as a named experiment.
- Visualization of per-group consistency distributions beyond what `ConsistencySummary` exposes as Python objects.
- Automatic remediation suggestions (e.g., "this input is ambiguous — consider adding a disambiguation step").
- Consistency evaluation across different models or prompt versions in a single call.
- Live mode consistency evaluation across a full dataset (calling `target_fn` k times for each of N inputs — k × N LLM calls). Live mode is for spot-checking a single input; full-dataset consistency uses the historical mode after collecting multiple pipeline runs.

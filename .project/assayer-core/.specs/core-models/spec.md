---
prd: assayer-core
id: core-models
status: done
depends-on: []
created: 2026-03-30
---

# Spec: Core Domain Models

## Context

This spec addresses **AC-009**, **AC-010**, and **AC-011** from the assayer-core PRD.

Every other spec in the assayer-core PRD depends on these foundational data structures. The models defined here carry evaluation results, token usage data, and experiment-level aggregations throughout the entire system. Getting their shape right is critical because every evaluator, metric, and runner will produce or consume these types.

## Scope

### In scope

- `TokenUsage` dataclass: `input_tokens: int`, `output_tokens: int`, `cost_usd: float | None`.
- `FieldEvaluation` dataclass: `field_name: str`, `evaluator_method: str`, `expected_value: Any`, `obtained_value: Any`, `score: float`, `prompt_hash: str | None`, `metadata: dict`.
- `RunResult` dataclass: wraps a single example execution containing the input, the output, a list of `FieldEvaluation` instances, and a `TokenUsage` instance.
- `ExperimentResult` dataclass: a collection of `RunResult` instances, an experiment name (`str`), and a `compare(other: ExperimentResult) -> dict` method signature. The method body raises `NotImplementedError` in this spec; implementation belongs to the runner spec.
- Basic construction-time validation (non-negative tokens, score in [0, 1], non-empty field_name, non-empty experiment_name).
- All classes live in a single module: `assayer/models.py`.

### Out of scope

- Business logic beyond construction and validation (no aggregation, no comparison implementation).
- Serialization to/from JSON or any wire format.
- Integration with LangSmith or any external system.
- Imports from other assayer modules; these models are leaf dependencies.

## Technical Design

All models are implemented as Python `dataclasses` with `frozen=False` (mutable by default since runners populate fields incrementally). Each model uses standard-library types only (`dataclasses`, `typing`). No third-party dependencies.

### TokenUsage

Fields:
- `input_tokens: int` -- number of input tokens consumed. Must be >= 0.
- `output_tokens: int` -- number of output tokens consumed. Must be >= 0.
- `cost_usd: float | None` -- estimated USD cost. `None` when no pricing table is available. When provided, must be >= 0.

### FieldEvaluation

Fields:
- `field_name: str` -- the name of the output field being evaluated. Must be non-empty.
- `evaluator_method: str` -- identifier of the evaluation method used (e.g., `"bleu"`, `"llm_judge"`). Must be non-empty.
- `expected_value: Any` -- the ground-truth value.
- `obtained_value: Any` -- the value produced by the target function.
- `score: float` -- evaluation score, normalized to the range [0.0, 1.0].
- `prompt_hash: str | None` -- SHA-256 hash of the judge prompt when applicable; `None` otherwise.
- `metadata: dict` -- arbitrary key-value pairs for extensibility. Defaults to an empty dict via `field(default_factory=dict)`.

### RunResult

Fields:
- `input: Any` -- the input passed to the target function.
- `output: Any` -- the raw output returned by the target function.
- `evaluations: list[FieldEvaluation]` -- per-field evaluation results. Defaults to empty list.
- `token_usage: TokenUsage` -- token consumption for this run.

### ExperimentResult

Fields:
- `experiment_name: str` -- human-readable name. Must be non-empty.
- `runs: list[RunResult]` -- the collection of run results.

Methods:
- `compare(other: ExperimentResult) -> dict` -- raises `NotImplementedError` with a message indicating the implementation lives in the runner spec.

### Validation strategy

Each dataclass uses a `__post_init__` method to enforce invariants. Violations raise `ValueError` with a descriptive message.

## Acceptance Criteria

- **AC-SPEC-001**: `TokenUsage` can be instantiated with valid `input_tokens`, `output_tokens`, and `cost_usd` values; accessing each attribute returns the provided value.
- **AC-SPEC-002**: `TokenUsage.__post_init__` raises `ValueError` when `input_tokens < 0`, `output_tokens < 0`, or `cost_usd < 0`.
- **AC-SPEC-003**: `FieldEvaluation` can be instantiated with all seven fields; `metadata` defaults to an empty dict when not provided.
- **AC-SPEC-004**: `FieldEvaluation.__post_init__` raises `ValueError` when `field_name` is empty, `evaluator_method` is empty, or `score` is outside [0.0, 1.0].
- **AC-SPEC-005**: `RunResult` holds an `input`, `output`, a list of `FieldEvaluation`, and a `TokenUsage`.
- **AC-SPEC-006**: `ExperimentResult` holds an `experiment_name` and a list of `RunResult`; raises `ValueError` when `experiment_name` is empty.
- **AC-SPEC-007**: `ExperimentResult.compare(other)` raises `NotImplementedError`.
- **AC-SPEC-008**: No module within `assayer/models.py` imports from any other `assayer.*` module.

## Edge Cases

- `TokenUsage` with `cost_usd=None` is valid (no pricing table available).
- `TokenUsage` with `input_tokens=0` and `output_tokens=0` is valid (e.g., cached response).
- `FieldEvaluation` with `expected_value=None` is valid (unsupervised evaluation).
- `FieldEvaluation` with `score=0.0` and `score=1.0` are both valid boundary values.
- `FieldEvaluation` with `prompt_hash=None` is valid (non-judge evaluator).
- `RunResult` with an empty `evaluations` list is valid (run completed but not yet evaluated).
- `ExperimentResult` with an empty `runs` list is valid (experiment created but no runs executed).
- Whitespace-only strings for `field_name`, `evaluator_method`, or `experiment_name` should be treated as empty and raise `ValueError`.

## Risks

- **Risk**: Future specs may need additional fields on these models.
  **Mitigation**: Dataclasses are easy to extend; adding fields with defaults is backward-compatible.
- **Risk**: Freezing models too early could block the runner spec.
  **Mitigation**: Models are not frozen (`frozen=False`), allowing incremental population.

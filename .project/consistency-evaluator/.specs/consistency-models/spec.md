---
prd: consistency-evaluator
id: consistency-models
status: pending
depends-on: []
created: 2026-04-07
---

# Spec: Consistency Models

## Context

Addresses AC-004, AC-005, AC-006, AC-007, AC-008, AC-009, AC-010, AC-013, AC-016 from the consistency-evaluator PRD.

This spec defines the data structures that carry consistency evaluation results throughout the framework. Both `consistency-metrics` and `consistency-evaluator` specs depend on these types, so they must be implemented first.

## Scope

### In scope

- `ConsistencyFieldEvaluation` dataclass: per-group result with all consistency fields
- `ConsistencySummary` dataclass: dataset-level aggregation of `ConsistencyFieldEvaluation` instances
- Field-level validation via `__post_init__`
- Google-style docstrings and full type hints on all public types

### Out of scope

- Computation logic for any metric (belongs to `consistency-metrics`)
- Grouping or dataset-iteration logic (belongs to `consistency-evaluator`)
- LangSmith serialization

## Technical Design

> **HUMAN REVIEW — 2026-04-08:** The original design placed both models in
> `assayer/evaluators/consistency_models.py`. After implementation, the module
> layout was refactored: `ConsistencyFieldEvaluation` and `ConsistencySummary`
> now live in `assayer/models/consistency_field_evaluation.py` and
> `assayer/models/consistency_summary.py` respectively, and are re-exported
> from `assayer/models/__init__.py`. The `assayer/evaluators/consistency_models.py`
> file was removed. All public imports remain available via `assayer.models`.

Both models are `@dataclass` classes placed in a new module `assayer/evaluators/consistency_models.py`, following the same pattern as `assayer/models.py`.

### ConsistencyFieldEvaluation

Represents the consistency measurement for a single group (one input case across k runs).

```
ConsistencyFieldEvaluation
├── group_key: str | None          — value of the group_by field (None in live mode)
├── n: int                         — number of runs in this group (≥ 1)
├── agreement_rate: float          — [0.0, 1.0]
├── dominant_label: str | None     — most frequent label; None when labels unavailable
├── entropy: float                 — [0.0, log₂(n_distinct_labels)]
├── score_std: float               — [0.0, ∞); 0.0 when n == 1
├── correct_rate: float            — [0.0, 1.0]
├── pass_at_k: bool                — True if any run matched the reference exactly
├── recall_at_k: float             — [0.0, 1.0]
└── raw_results: list[FieldEvaluation]  — individual evaluator outputs
```

Validation in `__post_init__`:
- `n >= 1`
- `agreement_rate` in `[0.0, 1.0]`
- `entropy >= 0.0`
- `score_std >= 0.0`
- `correct_rate` in `[0.0, 1.0]`
- `recall_at_k` in `[0.0, 1.0]`

### ConsistencySummary

Aggregates multiple `ConsistencyFieldEvaluation` instances from `evaluate_dataset`.

```
ConsistencySummary
├── per_group: list[ConsistencyFieldEvaluation]   — one entry per group (after min_k filtering)
├── mean_agreement_rate: float
├── mean_entropy: float
├── mean_score_std: float
├── mean_correct_rate: float
├── pass_at_k_rate: float                — proportion of groups where pass_at_k is True
├── mean_recall_at_k: float
└── worst_groups: list[ConsistencyFieldEvaluation] — top-10 by ascending agreement_rate
```

Validation in `__post_init__`:
- All mean fields in `[0.0, 1.0]` except `mean_entropy` (unbounded above) and `mean_score_std` (unbounded above)
- `pass_at_k_rate` in `[0.0, 1.0]`
- `worst_groups` is a subset of `per_group` (no new instances introduced)

## Acceptance Criteria

- [ ] AC-001: `ConsistencyFieldEvaluation` can be instantiated with all required fields and exposes them as typed attributes.
- [ ] AC-002: `ConsistencyFieldEvaluation.__post_init__` raises `ValueError` if `n < 1`.
- [ ] AC-003: `ConsistencyFieldEvaluation.__post_init__` raises `ValueError` if `agreement_rate` is outside `[0.0, 1.0]`.
- [ ] AC-004: `ConsistencyFieldEvaluation.__post_init__` raises `ValueError` if `entropy < 0.0`.
- [ ] AC-005: `ConsistencyFieldEvaluation.__post_init__` raises `ValueError` if `score_std < 0.0`.
- [ ] AC-006: `ConsistencyFieldEvaluation.__post_init__` raises `ValueError` if `correct_rate` is outside `[0.0, 1.0]`.
- [ ] AC-007: `ConsistencyFieldEvaluation.__post_init__` raises `ValueError` if `recall_at_k` is outside `[0.0, 1.0]`.
- [ ] AC-008: `ConsistencyFieldEvaluation` allows `group_key=None` and `dominant_label=None` without raising.
- [ ] AC-009: `ConsistencyFieldEvaluation.raw_results` defaults to an empty list when not provided.
- [ ] AC-010: `ConsistencySummary` can be instantiated with all required fields and exposes them as typed attributes.
- [ ] AC-011: `ConsistencySummary.__post_init__` raises `ValueError` if `pass_at_k_rate` is outside `[0.0, 1.0]`.
- [ ] AC-012: `ConsistencySummary.__post_init__` raises `ValueError` if `mean_correct_rate` is outside `[0.0, 1.0]`.
- [ ] AC-013: `ConsistencySummary.__post_init__` raises `ValueError` if `mean_recall_at_k` is outside `[0.0, 1.0]`.
- [ ] AC-014: `ConsistencySummary.per_group` and `ConsistencySummary.worst_groups` default to empty lists when not provided.
- [ ] AC-015: All public classes and their fields carry Google-style docstrings and full type hints.

## Edge Cases

- `n == 1`: valid; `score_std` must be `0.0`, `entropy` must be `0.0`, `agreement_rate` must be `1.0`.
- `dominant_label=None`: valid for evaluators that return only a numeric score with no label (e.g., LLM-as-Judge with continuous score).
- `group_key=None`: valid in live mode where there is no dataset group key.
- `worst_groups` can be empty if `per_group` is empty.
- `recall_at_k` and `correct_rate` may both be `0.0` at the same time without conflict.

## Risks

- `FieldEvaluation` from `assayer/models.py` is the existing type for raw evaluator outputs — `ConsistencyFieldEvaluation.raw_results` must reference it directly to avoid duplication.

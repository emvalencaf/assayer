---
id: TASK-002
spec: consistency-models
status: pending
depends-on: [TASK-001]
created: 2026-04-07
---

# TASK-002: Define ConsistencySummary dataclass

## What to do

In `assayer/evaluators/consistency_models.py`, implement the `ConsistencySummary` dataclass with all fields, types, default values, and `__post_init__` validation as described in the spec's Technical Design section.

Fields:
- `per_group: list[ConsistencyFieldEvaluation]` — defaults to empty list
- `mean_agreement_rate: float`
- `mean_entropy: float`
- `mean_score_std: float`
- `mean_correct_rate: float`
- `pass_at_k_rate: float`
- `mean_recall_at_k: float`
- `worst_groups: list[ConsistencyFieldEvaluation]` — defaults to empty list

Validation:
- `pass_at_k_rate` in `[0.0, 1.0]`
- `mean_correct_rate` in `[0.0, 1.0]`
- `mean_recall_at_k` in `[0.0, 1.0]`
- `mean_agreement_rate` in `[0.0, 1.0]`

Add `ConsistencySummary` to the module's `__all__`.

## Acceptance Criteria

- [ ] `ConsistencySummary` can be instantiated with all required fields and exposes them as typed attributes.
- [ ] `__post_init__` raises `ValueError` if `pass_at_k_rate` is outside `[0.0, 1.0]`.
- [ ] `__post_init__` raises `ValueError` if `mean_correct_rate` is outside `[0.0, 1.0]`.
- [ ] `__post_init__` raises `ValueError` if `mean_recall_at_k` is outside `[0.0, 1.0]`.
- [ ] `__post_init__` raises `ValueError` if `mean_agreement_rate` is outside `[0.0, 1.0]`.
- [ ] `per_group` and `worst_groups` default to empty lists when not provided.
- [ ] All public fields carry Google-style docstrings and full type hints.

## Dependencies

- TASK-001

## Tests

Test file:

## Implementation Notes

## Commit

Hash:

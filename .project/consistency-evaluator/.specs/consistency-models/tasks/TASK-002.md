---
id: TASK-002
spec: consistency-models
status: done
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

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_consistency_models.py`

Tests for ConsistencySummary dataclass covering:
- Instantiation with all required fields and typed attribute access
- Validation of rate fields (pass_at_k_rate, mean_correct_rate, mean_recall_at_k, mean_agreement_rate) within [0.0, 1.0] range
- Default empty lists for per_group and worst_groups fields
- Boundary value acceptance for all validated fields
- Unbounded validation for mean_entropy and mean_score_std
- Edge cases with empty groups

## Implementation Notes

Added the `ConsistencySummary` dataclass to `assayer/evaluators/consistency_models.py` with all required fields and validation:

- Implemented all fields with proper Google-style docstrings and type hints
- Added `__post_init__` validation for the four rate fields that must be in [0.0, 1.0]
- Used `field(default_factory=list)` for `per_group` and `worst_groups` to provide empty list defaults
- Left `mean_entropy` and `mean_score_std` unbounded above as specified
- Added `ConsistencySummary` to the module's `__all__` list for proper public API exposure

All tests now pass, including the specific TASK-002 tests for:
- Field instantiation and type validation
- Range validation for bounded rate fields  
- Default empty list behavior
- Boundary value acceptance
- Unbounded validation for entropy and score std

## Commit

Hash:

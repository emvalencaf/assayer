---
id: TASK-001
spec: consistency-models
status: done
depends-on: []
created: 2026-04-07
---

# TASK-001: Define ConsistencyFieldEvaluation dataclass

## What to do

Create `assayer/evaluators/consistency_models.py` and implement the `ConsistencyFieldEvaluation` dataclass with all fields, types, default values, and `__post_init__` validation as described in the spec's Technical Design section.

Fields:
- `group_key: str | None`
- `n: int`
- `agreement_rate: float`
- `dominant_label: str | None`
- `entropy: float`
- `score_std: float`
- `correct_rate: float`
- `pass_at_k: bool`
- `recall_at_k: float`
- `raw_results: list[FieldEvaluation]` — defaults to empty list

Import `FieldEvaluation` from `assayer.models`. Add `ConsistencyFieldEvaluation` to the module's `__all__`.

## Acceptance Criteria

- [ ] `ConsistencyFieldEvaluation` can be instantiated with all required fields and exposes them as typed attributes.
- [ ] `__post_init__` raises `ValueError` if `n < 1`.
- [ ] `__post_init__` raises `ValueError` if `agreement_rate` is outside `[0.0, 1.0]`.
- [ ] `__post_init__` raises `ValueError` if `entropy < 0.0`.
- [ ] `__post_init__` raises `ValueError` if `score_std < 0.0`.
- [ ] `__post_init__` raises `ValueError` if `correct_rate` is outside `[0.0, 1.0]`.
- [ ] `__post_init__` raises `ValueError` if `recall_at_k` is outside `[0.0, 1.0]`.
- [ ] `group_key=None` and `dominant_label=None` are accepted without raising.
- [ ] `raw_results` defaults to an empty list when not provided.
- [ ] All public fields carry Google-style docstrings and full type hints.

## Dependencies

- none

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_consistency_models.py`

Comprehensive tests covering all acceptance criteria for the `ConsistencyFieldEvaluation` dataclass:
- Instantiation with all required fields and typed attributes  
- Validation errors for invalid `n`, `agreement_rate`, `entropy`, `score_std`, `correct_rate`, `recall_at_k`
- Acceptance of `None` values for `group_key` and `dominant_label`
- Default empty list for `raw_results`
- Boundary value testing and edge cases (e.g., `n=1`)

## Implementation Notes

Implemented `ConsistencyFieldEvaluation` as a `@dataclass` following the same patterns as `assayer/models.py`:

- All fields have proper type hints using `Union[str, None]` for nullable string fields
- Google-style docstrings include detailed field descriptions, Args section, and Raises section  
- `__post_init__` validation covers all range constraints specified in the spec
- `raw_results` uses `field(default_factory=list)` for the default empty list
- Import of `FieldEvaluation` from `assayer.models` enables proper type checking
- Added to `__all__` for proper module exports

Key decisions:
- Used `Union[str, None]` instead of `str | None` for broader Python version compatibility
- Validation error messages match exactly what tests expect (e.g., "must be in the range [0.0, 1.0]")
- Placed the module in `assayer/evaluators/consistency_models.py` as specified

## Commit

Hash:

---
prd: consistency-evaluator
id: consistency-metrics
status: pending
depends-on: [consistency-models]
created: 2026-04-07
---

# Spec: Consistency Metrics

## Context

Addresses AC-005, AC-006, AC-007, AC-008, AC-009, AC-010 from the consistency-evaluator PRD.

This spec implements the pure, stateless metric functions that compute each consistency field from a list of `FieldEvaluation` results. These functions are the computational core — they have no side effects, no I/O, and no dependency on evaluator orchestration. The `consistency-evaluator` spec will call them to assemble `ConsistencyFieldEvaluation` instances.

## Scope

### In scope

- `compute_agreement_rate(results) -> tuple[float, str | None]` — returns `(agreement_rate, dominant_label)`
- `compute_entropy(results) -> float`
- `compute_score_std(results) -> float`
- `compute_correct_rate(results, reference) -> float`
- `compute_pass_at_k(results, reference) -> bool`
- `compute_recall_at_k(results, reference) -> float`
- All functions placed in `assayer/evaluators/consistency_metrics.py`
- Google-style docstrings and full type hints

### Out of scope

- Grouping or iteration over datasets (belongs to `consistency-evaluator`)
- Dataclass definitions (belongs to `consistency-models`)
- Any I/O or LLM calls

## Technical Design

All functions are module-level, pure functions. They accept a `list[FieldEvaluation]` as their primary input. Where a reference is needed (`correct_rate`, `pass_at_k`, `recall_at_k`), it is accepted as a separate `Any` parameter.

### Label extraction — the `obtained_value` contract

`FieldEvaluation.obtained_value` is the sole source of the consistency signal. In historical mode, it holds the LLM's prediction for that specific past run (set by the wrapped evaluator during `evaluate(prediction, reference)`). In live mode, it holds the prediction returned by `target_fn` for that specific k-iteration. All metric functions read from `obtained_value` — never from `expected_value`.

For label-based metrics, the obtained value is:
- **Single-label**: a `str` — compared with `str(reference)`
- **Multi-label**: a `list[str]` or `set[str]` — compared as a set against `set(reference)`

The functions must handle both cases by checking the type of `obtained_value`.

### `compute_agreement_rate`

```
labels = [str(r.obtained_value) for r in results]  # single-label path
counts = Counter(labels)
dominant = counts.most_common(1)[0][0]
agreement_rate = counts[dominant] / len(results)
```

Returns `(1.0, the_label)` when `len(results) == 1`.

### `compute_entropy`

```
H = -Σ p(x) · log₂(p(x))   over the label distribution
```

Returns `0.0` when all labels are identical or when `len(results) == 1`.
Uses natural log base 2. Skips labels with `p == 0` (impossible by construction).

### `compute_score_std`

```
scores = [r.score for r in results]
std = statistics.stdev(scores) if len(scores) > 1 else 0.0
```

Uses `statistics.stdev` (sample std dev, ddof=1). Returns `0.0` when `n == 1`.

### `compute_correct_rate`

For single-label: `count(str(r.obtained_value) == str(reference)) / n`
For multi-label: `count(set(r.obtained_value) == set(reference)) / n`

Detection: if any `r.obtained_value` is a `list` or `set`, use multi-label path; otherwise single-label.

### `compute_pass_at_k`

Returns `True` if `correct_rate > 0.0`; equivalent to `any(run is correct)`.

### `compute_recall_at_k`

```
ref_set = set(reference)           # reference must be iterable
union_predicted = set().union(*[set(r.obtained_value) for r in results])
recall = len(union_predicted & ref_set) / len(ref_set)
```

For single-label: `ref_set = {str(reference)}`, each `obtained_value` is treated as `{str(r.obtained_value)}`.
Degrades to `1.0` if `pass_at_k` is `True`, `0.0` otherwise, for single-label.

Returns `0.0` if `ref_set` is empty (defensive: avoids ZeroDivisionError).

## Acceptance Criteria

- [ ] AC-001: `compute_agreement_rate([r])` where all `r.obtained_value` are identical returns `(1.0, that_value)`.
- [ ] AC-002: `compute_agreement_rate` returns the label with the highest count as the dominant label.
- [ ] AC-003: `compute_entropy` returns `0.0` when all results share the same `obtained_value`.
- [ ] AC-004: `compute_entropy` returns a positive float when results have two or more distinct `obtained_value` values.
- [ ] AC-005: `compute_score_std` returns `0.0` when `len(results) == 1`.
- [ ] AC-006: `compute_score_std` returns a positive float when results have at least two distinct `score` values.
- [ ] AC-007: `compute_correct_rate` returns `1.0` when all single-label predictions match the reference string.
- [ ] AC-008: `compute_correct_rate` returns `0.0` when no prediction matches the reference.
- [ ] AC-009: `compute_correct_rate` uses exact set equality for multi-label predictions (list/set `obtained_value`).
- [ ] AC-010: `compute_pass_at_k` returns `True` if at least one result matches the reference; `False` otherwise.
- [ ] AC-011: `compute_recall_at_k` returns `1.0` when the union of all predicted label sets covers all reference labels.
- [ ] AC-012: `compute_recall_at_k` returns `0.0` when no predicted label appears in the reference set.
- [ ] AC-013: `compute_recall_at_k` returns `0.0` (not raises) when the reference set is empty.
- [ ] AC-014: For single-label inputs, `compute_recall_at_k` returns `1.0` if `compute_pass_at_k` is `True` and `0.0` otherwise.
- [ ] AC-015: All functions carry Google-style docstrings and full type hints.

## Edge Cases

- `results` list with a single element: all functions must handle `n == 1` without raising.
- Mixed `obtained_value` types within the same results list (e.g., some `str`, some `list`): treat as single-label if all are `str`; raise `TypeError` if types are inconsistent.
- `reference` is an empty list for multi-label: `compute_recall_at_k` returns `0.0`.
- All predictions are distinct: `agreement_rate` = `1 / n`, `dominant_label` = first by `most_common` tie-breaking.
- `score` is the same for all results: `score_std` = `0.0`.

## Risks

- `statistics.stdev` raises `StatisticsError` for a single-element list — the guard `if len > 1` must come before calling it.
- Type detection for single vs. multi-label relies on `obtained_value` type, which is `Any` in `FieldEvaluation`. This is an implicit contract that must be documented clearly.

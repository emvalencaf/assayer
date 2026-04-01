---
prd: assayer-core
id: ner-evaluator
status: pending
depends-on: [registry-and-extension, core-models]
created: 2026-03-30
---

# Spec: NER Evaluator

## Context
Addresses AC-005 from the assayer-core PRD.
NLP applications that extract named entities need structured evaluation beyond simple string matching. This spec implements a per-type entity F1 evaluator with exact-match semantics and registers it in `EvaluatorRegistry`.

## Scope

### In scope
- `EntitySpan` dataclass representing a single extracted entity
- `NERMatcher` — logic for computing precision, recall, F1 per entity type
- `NERBatchMetric` — dataset-level macro F1 registered in `MetricRegistry` as `"ner_macro_f1"`
- `NEREvaluator` subclassing `BaseEvaluator`, registered as `"ner"`
- Returns `FieldEvaluation` with per-type F1 details in `metadata`

### Out of scope
- Partial/fuzzy entity matching
- Span-only matching without entity type
- Coreference resolution
- Token-level (BIO tagging) evaluation

## Technical Design
See `design.md` for full detail on `EntitySpan`, `NERMatcher`, and the `FieldEvaluation` metadata contract.

### EntitySpan
```python
@dataclass
class EntitySpan:
    text: str
    entity_type: str
    start: int   # character offset, inclusive
    end: int     # character offset, exclusive
```
A true positive requires exact match on all four fields.

### NERMatcher
Stateless helper. Given `predicted: list[EntitySpan]` and `reference: list[EntitySpan]`:
1. Group spans by `entity_type`
2. For each type: compute precision = TP / (TP + FP), recall = TP / (TP + FN), F1
3. Macro F1 = unweighted mean of per-type F1 scores
4. Zero-division: when no predictions and no references for a type, skip that type; when one side is empty, F1 = 0.0

### NERBatchMetric
Callable with signature `MetricFn`:
```
ner_macro_f1(predictions: list[list[EntitySpan]], references: list[list[EntitySpan]]) -> float
```
Returns the mean macro F1 across all examples.

### NERResult metadata shape
```python
{
    "per_type_f1":       {"PERSON": 0.85, "ORG": 0.72},
    "per_type_precision": {"PERSON": 0.90, "ORG": 0.68},
    "per_type_recall":    {"PERSON": 0.80, "ORG": 0.76},
    "macro_f1":           0.785,
}
```

## Acceptance Criteria
- [ ] AC-NER-001: `NERMatcher` returns correct precision, recall, and F1 per entity type for a known input fixture.
- [ ] AC-NER-002: Macro F1 equals the unweighted mean of per-type F1 scores.
- [ ] AC-NER-003: An entity type present only in predictions (not in references) contributes precision=0, recall=0, F1=0 for that type.
- [ ] AC-NER-004: An entity type present only in references contributes F1=0 for that type.
- [ ] AC-NER-005: `NERBatchMetric` registered as `"ner_macro_f1"` returns the mean macro F1 across a list of examples.
- [ ] AC-NER-006: `NERMatcher` handles an empty predictions list without raising, returning F1=0.0.
- [ ] AC-NER-007: `NEREvaluator.evaluate()` returns a `FieldEvaluation` with `metadata` matching the NERResult shape above.
- [ ] AC-NER-008: `NEREvaluator` is registered in `EvaluatorRegistry` as `"ner"`.

## Edge Cases
- Both `predicted` and `reference` empty → macro F1 = 0.0 (no types to average)
- All predictions correct, no false positives or negatives → F1 = 1.0
- Entity type appears in predictions only → precision = 0, F1 = 0 for that type
- Entity type appears in references only → recall = 0, F1 = 0 for that type

## Risks
- Exact-match semantics on character offsets require that callers normalize offset conventions (0-indexed, end-exclusive); this must be documented clearly.

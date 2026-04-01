---
prd: assayer-core
spec: ner-evaluator
created: 2026-03-30
---

# Design: NER Evaluator

## EntitySpan data model

```python
@dataclass(frozen=True)
class EntitySpan:
    text: str
    entity_type: str
    start: int   # character offset, inclusive, 0-indexed
    end: int     # character offset, exclusive

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("EntitySpan.text must not be empty")
        if not self.entity_type:
            raise ValueError("EntitySpan.entity_type must not be empty")
        if self.start < 0:
            raise ValueError("EntitySpan.start must be >= 0")
        if self.end <= self.start:
            raise ValueError("EntitySpan.end must be > start")
```

`frozen=True` enables hashing and set operations needed for TP/FP/FN counting.

## NERMatcher algorithm

```
def match(
    predicted: list[EntitySpan],
    reference: list[EntitySpan],
) -> NERMatchResult
```

**NERMatchResult**:
```python
@dataclass
class NERMatchResult:
    per_type_precision: dict[str, float]
    per_type_recall: dict[str, float]
    per_type_f1: dict[str, float]
    macro_f1: float
```

**Algorithm**:
1. Collect all entity types from both lists: `types = {s.entity_type for s in predicted + reference}`
2. For each type `t`:
   - `pred_set = {s for s in predicted if s.entity_type == t}`
   - `ref_set = {s for s in reference if s.entity_type == t}`
   - `tp = len(pred_set & ref_set)`
   - `precision = tp / len(pred_set) if pred_set else 0.0`
   - `recall = tp / len(ref_set) if ref_set else 0.0`
   - `f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0`
3. `macro_f1 = mean(per_type_f1.values()) if per_type_f1 else 0.0`

## FieldEvaluation metadata contract

When `NEREvaluator.evaluate()` runs, it returns:
```python
FieldEvaluation(
    field_name=self.field_name,          # configured at evaluator construction
    evaluator_method="ner_exact_match",
    expected_value=reference_spans,      # list[EntitySpan]
    obtained_value=predicted_spans,      # list[EntitySpan]
    score=match_result.macro_f1,
    prompt_hash=None,
    metadata={
        "per_type_f1": match_result.per_type_f1,
        "per_type_precision": match_result.per_type_precision,
        "per_type_recall": match_result.per_type_recall,
        "macro_f1": match_result.macro_f1,
    }
)
```

## NERBatchMetric

Signature matches `MetricFn` but with typed inputs:
```python
def ner_macro_f1(
    predictions: list[list[EntitySpan]],
    references: list[list[EntitySpan]],
) -> float:
    """Compute mean macro F1 across all examples."""
    scores = [
        NERMatcher().match(pred, ref).macro_f1
        for pred, ref in zip(predictions, references)
    ]
    return sum(scores) / len(scores) if scores else 0.0
```

## File layout

```
assayer/
  evaluators/
    ner.py          # EntitySpan, NERMatcher, NERMatchResult, NEREvaluator
  metrics/
    ner.py          # ner_macro_f1 batch metric, register_ner_metrics()
```

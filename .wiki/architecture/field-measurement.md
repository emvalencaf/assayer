---
type: Reference
title: Per-Field measurement
description: The Runner's field map, which scores each output Field on its own by dotted path, and how the Scores and failures carry the Field.
resource: assayer/runner/field_map.py
tags: [runner, metrics, field]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T23:59:00Z }
sources:
  - id: field-map
    resource: assayer/runner/field_map.py
    title: build_field_map and resolve
  - id: runner
    resource: assayer/runner/runner.py
    title: Runner
  - id: alignment
    resource: assayer/runner/alignment.py
    title: Alignment strategies
  - id: scoring
    resource: assayer/runner/field_scoring.py
    title: List Field scoring
  - id: tests
    resource: tests/runner/test_field_map.py
    title: Field map tests
---

# Overview

`Runner(field_metrics={...})` scores each field of a structured output on its own
(#28).[^field-map] The map goes from the dotted path of a Field to a list of
trajectory-level metrics:

```python
Runner(
    target,
    field_metrics={
        "label": [exact],
        "address.city": [exact, (within, {"tolerance": 1})],
        "meta.tags.0": [exact],
    },
)
```

* A path walks nested dictionaries; a numeric segment indexes a list (`meta.tags.0`). Only ASCII digits count as an index: a segment such as `²` is not one, so it resolves to a missing Field and fails as an `EvaluationFailure` instead of aborting the run.[^field-map]
* An entry is a `Metric` or a `(Metric, params)` pair. `params` go to the metric's function as keyword arguments for that Field only.
* The metric sees the Field's value as the Trajectory's `final_output` and the Case's value as `expected_output`. A Field absent from the prediction reaches the metric as `None`; one absent from the Case fails the metric's `requires` check as an `EvaluationFailure`.[^tests]
* Each resulting `Score` and `EvaluationFailure` carries the `field` path. A metric in `Runner(metrics=...)` still scores the whole output, with `field` `None`.
* `Experiment.scores_by_field()` groups the Scores by `field`, in computed order; the whole-output Scores are under `None`. See [Domain models](domain-models.md).
* Works in both `run` and `score`. `load_cases` also validates the Case fields that the field metrics `require`.[^runner]

# List Fields

A Field that is a list of objects maps to a `ListField` instead of a list of metrics (#29):

```python
Runner(target, field_metrics={
    "items": ListField(
        properties={"name": [exact], "tags": ListField({"v": [exact]})},
        align="best_match",  # or "key" (with key="id") or "positional"
    ),
})
```

* The Alignment pairs each predicted item with an expected one. `best_match` (default) is greedy by descending similarity (the mean of the pair's property Scores; a nested list counts as its `list_f1`, through each entry's `similarity_name`), threshold 0.5, ties by position (expected index, then predicted index). `key` pairs equal `key` values; `positional` pairs equal indexes.[^alignment]
* Property Scores are the mean over the aligned pairs, at `items.name`; a nested `ListField` aligns inside each pair, recursively.
* `list_precision`, `list_recall` and `list_f1` are Scores of the list Field. Both empty: 1.0 on all three; expected empty with predictions: precision 0, recall 1.0; expected non-empty and none predicted (or no list): recall 0, precision 1.0.
* `metadata["alignment"]` holds `pairs` (`(expected, predicted)` index tuples), `unmatched_expected` and `unmatched_predicted`. For a nested list the metadata is `alignments`, one entry per outer pair, tagged with `within`.[^scoring]
* An expected value that is absent or not a list is an `EvaluationFailure` of `list_alignment`.

# Validation

`build_field_map` checks the map when the `Runner` is built, before any target
call.[^field-map]

* `TypeError`: the map is not a mapping, a value is not a list, an entry is not a `Metric` or `(Metric, params)`, or `params` is not a mapping.
* `ValueError`: a path is blank or has an empty segment (`a..b`), a metric is listed twice under one path (their Scores could not be told apart), or a metric is not trajectory-level. Only trajectory-level metrics are accepted for now, because a Field is cut out of a Trajectory's output.

[^field-map]: assayer/runner/field_map.py
[^runner]: assayer/runner/runner.py
[^alignment]: assayer/runner/alignment.py
[^scoring]: assayer/runner/field_scoring.py
[^tests]: tests/runner/test_field_map.py

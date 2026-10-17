---
type: Reference
title: Per-Field measurement
description: The Runner's field map, which scores each output Field on its own by dotted path, and how the Scores and failures carry the Field.
resource: assayer/runner/field_map/
tags: [runner, metrics, field]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-18T00:30:00Z }
sources:
  - id: field-map
    resource: assayer/runner/field_map/
    title: build_field_map and resolve
  - id: runner
    resource: assayer/runner/runner.py
    title: Runner
  - id: alignment
    resource: assayer/runner/field_map/alignment.py
    title: Alignment strategies
  - id: scoring
    resource: assayer/runner/field_map/scoring.py
    title: List Field scoring
  - id: schema
    resource: assayer/runner/field_map/schema.py
    title: Schema utility
  - id: loader
    resource: assayer/runner/field_map/loader.py
    title: Field map loading
  - id: tests
    resource: tests/runner/test_field_map.py
    title: Field map tests
---

# Overview

`Runner(field_metrics={...})` scores each field of a structured output on its own
(#28).[^field-map] The map goes from the dotted path of a Field to a list of
trajectory- or experiment-level metrics:

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
* An entry may also be an `experiment`-level metric, such as a [corpus or consistency metric](../metrics/corpus-and-consistency.md) (#30). It sees that Field of every Trajectory (`final_output`) and Case (`expected_output`) and only the Scores already computed for that Field, and yields one Experiment-level Score with the `field`. These entries run after the whole-output metrics and the entries listed before them, so `score_std` must follow the metric it measures. A Case lacking the Field fails the metric on that Field.[^scoring]
* Works in both `run` and `score`. `load_cases` also validates the Case fields that the field metrics `require`.[^runner]

# List Fields

A Field that is a list of objects maps to a `ListField` instead of a list of metrics (#29):

```python
Runner(
    target,
    field_metrics={
        "items": ListField(
            properties={"name": [exact], "tags": ListField({"v": [exact]})},
            align="best_match",  # or "key" (with key="id") or "positional"
        ),
    },
)
```

* The Alignment pairs each predicted item with an expected one. `best_match` (default) is greedy by descending similarity (the mean of the pair's property Scores; a nested list counts as its `list_f1`, through each entry's `similarity_name`), threshold 0.5, ties by position (expected index, then predicted index). `key` pairs equal `key` values; `positional` pairs equal indexes.[^alignment]
* Property Scores are the mean over the aligned pairs, at `items.name`; a nested `ListField` aligns inside each pair, recursively.
* `list_precision`, `list_recall` and `list_f1` are Scores of the list Field. Both empty: 1.0 on all three; expected empty with predictions: precision 0, recall 1.0; expected non-empty and none predicted (or no list): recall 0, precision 1.0.
* `metadata["alignment"]` holds `pairs` (`[expected, predicted]` index pairs), `unmatched_expected` and `unmatched_predicted`. For a nested list the metadata is `alignments`, one entry per outer pair, tagged with `within`.[^scoring]
* An expected value that is absent or not a list is an `EvaluationFailure` of `list_alignment`.

# Validation

`build_field_map` checks the map when the `Runner` is built, before any target
call.[^field-map]

* `TypeError`: the map is not a mapping, a value is not a list, an entry is not a `Metric` or `(Metric, params)`, or `params` is not a mapping.
* `ValueError`: a path is blank or has an empty segment (`a..b`), a metric is listed twice under one path (their Scores could not be told apart), or a metric is neither trajectory- nor experiment-level (a Field is cut out of a Trajectory's output, or of all of an Experiment's). The properties of a `ListField` accept trajectory-level metrics only, as an item has no corpus to be scored over.

# Schema utility and file loading

`schema_to_field_map(schema)` drafts a field map from a JSON Schema or a Pydantic model (anything with `model_json_schema()`), and `load_field_map(path)` reads one back from a file (#31).[^schema]

* The draft's `spec` is plain data: each dotted path maps to a list of entries (a metric name, or `{name: params}`) or, for an array of objects, to `{align, properties}`. `to_yaml()` and `to_json()` write it out for editing.
* Defaults: enum/boolean `exact_match` + `f1`; short string (`format`, `pattern` or `maxLength` <= 64) `normalized_exact_match`; other string `rouge_l`; number `numeric_tolerance` (`tolerance: 0`); array of non-objects `list_f1`; object recursed into dotted paths; array of objects a `best_match` list Field. Inside list items `f1` and `rouge_l` (corpus-level) give way to `exact_match` and `normalized_exact_match`.
* An id-like item property (`id`, `key`, `uuid`, `*_id`, `*_key`) is not scored; the YAML gets a commented `# key: id` hint and the alignment stays `best_match`.
* `load_field_map` reads `.json`, `.yaml` or `.yml` (YAML needs `assayer[yaml]`); `parse_field_map(data, registry=None)` resolves names against a registry (default: the field-level and corpus metrics) and returns a map `Runner(field_metrics=...)` accepts.[^loader]
* A malformed map raises `FieldMapError` (a `ValueError`) at load: unknown metric or list option, bad entry shape, or any rule `build_field_map` enforces.

[^field-map]: assayer/runner/field_map/
[^schema]: assayer/runner/field_map/schema.py
[^loader]: assayer/runner/field_map/loader.py
[^runner]: assayer/runner/runner.py
[^alignment]: assayer/runner/field_map/alignment.py
[^scoring]: assayer/runner/field_map/scoring.py
[^tests]: tests/runner/test_field_map.py

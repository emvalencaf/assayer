# Update Log

## 2026-10-17
* **Update**: [Adapters](architecture/adapters.md) records that `plan_export` returns an `ExportPlan` with `notes` for unlinkable Scores and Trajectories, the new `export_experiment` (an unplannable Experiment is one `validation` failure of target kind `experiment`), and that `include_content=False` now also drops Step errors and Score comments.
* **Addition**: Documented the [Adapters](architecture/adapters.md) core (#35): `Adapter` Protocol, `ExportReport`, failure taxonomy, deterministic ids, retry policy and `InMemoryAdapter`, listed in the [architecture index](architecture/index.md).
* **Update**: [Runner](architecture/runner.md) records `Runner(adapter=...)` and `Runner.export`; [Package organization](architecture/package-organization.md) lists `adapters/`.
* **Addition**: Documented [goal success, faithfulness, context precision and recall, and pass^k](metrics/rag-and-pass-hat-k.md) (#34), listed in the [metrics index](metrics/index.md).
* **Addition**: Documented [Judge metrics](metrics/judge-metrics.md) (Judge Protocol, prompts, parsing, accounting, `make_criteria_judge`).
* **Update**: [Package organization](architecture/package-organization.md) now lists `judges/`.
* **Update**: [Tool and end-state metrics](metrics/tool-and-state-metrics.md) records that `end_state_match` pairs leaves by a tuple path, so a key with a dot or a key `"0"` no longer collides with a nested path or a list index (the Score `field` is still the dotted path). Alignment and dotted-path `resolve` gained unit tests only.
* **Addition**: Documented the [tool and end-state metrics](metrics/tool-and-state-metrics.md) (#32): `tool_correctness`, `tool_argument_match` and `end_state_match`, listed in the [metrics index](metrics/index.md).
* **Update**: [Metric contract](metrics/metric-contract.md) records that `fn` may return `Detailed` or `None`; [Package organization](architecture/package-organization.md) lists the top-level `alignment.py` and `path.py` (moved out of `runner/field_map/`), and [Per-Field measurement](architecture/field-measurement.md) points at the new Alignment path.
* **Update**: [Per-Field measurement](architecture/field-measurement.md) documents the schema utility and YAML/JSON field-map loading (#31), with the new field-level metrics `exact_match`, `normalized_exact_match`, `numeric_tolerance` and `list_f1`.
* **Update**: [Runner](architecture/runner.md) now records that `run` and `score` reject Cases with repeated ids (a position id counts); [Corpus and consistency metrics](metrics/corpus-and-consistency.md) records that a consistency metric with no Trajectories is an `EvaluationFailure`, not a 0, and that the corpus is pooled rather than averaged per Case (other changes were internal refactors).
* **Addition**: Documented [Corpus and consistency metrics](metrics/corpus-and-consistency.md) (#30), listed in the [metrics index](metrics/index.md).
* **Update**: [Per-Field measurement](architecture/field-measurement.md) now accepts Experiment-level metrics in `field_metrics` (not in `ListField` properties); [Metric contract](metrics/metric-contract.md) records that an Experiment-level `requires` must hold for every Case; [Runner](architecture/runner.md) and [Domain models](architecture/domain-models.md) record `Experiment.cases`; [Package organization](architecture/package-organization.md) lists the `consistency` and `corpus` modules.
* **Update**: [Per-Field measurement](architecture/field-measurement.md) now records that Alignment `pairs` are `(expected, predicted)` tuples and that `best_match` breaks ties by expected then predicted index; field map entries expose `similarity_name` and `metrics()` (internal refactor, no scoring change).
* **Addition**: [Per-Field measurement](architecture/field-measurement.md) documents the Alignment of list Fields (#29): `ListField`, `key`/`best_match`/`positional`, and the `list_precision`/`list_recall`/`list_f1` Scores.
* **Update**: [Per-Field measurement](architecture/field-measurement.md) now records that listing the same metric twice under one path raises `ValueError`, and that only ASCII digits index a list in a path.
* **Addition**: Documented [Per-Field measurement](architecture/field-measurement.md) (#28): `Runner(field_metrics=...)`, dotted paths, per-pair parameters and construction-time validation; listed in the [architecture index](architecture/index.md).
* **Update**: [Runner](architecture/runner.md), [Metric contract](metrics/metric-contract.md) (`evaluate(field, params)`) and [Domain models](architecture/domain-models.md) (`EvaluationFailure.field`, `Experiment.scores_by_field()`) now record per-Field measurement.
* **Update**: `compare(a, b)` now computes the token and cost deltas over the Cases both Experiments have only, and `Comparison` gained `only_in_a` and `only_in_b` listing the others. See [Comparison](architecture/comparison.md) and [Domain models](architecture/domain-models.md).
* **Update**: `Experiment.pricing`, set by `Runner(pricing=...)`, now prices the target; `compare(a, b)` lost its `pricing` argument and returns `None` token and cost deltas when a side has no recorded usage. See [Comparison](architecture/comparison.md), [Runner](architecture/runner.md) and [Domain models](architecture/domain-models.md).
* **Addition**: Documented [Comparison](architecture/comparison.md) and `compare(a, b)` (#27), listed in the [architecture index](architecture/index.md).
* **Update**: [Runner](architecture/runner.md) now records `Runner.score(dataset, outputs)` and the optional `target` (`run` raises `ValueError` without one).
* **Update**: [Domain models](architecture/domain-models.md) now list `Comparison`.
* **Update**: [Runner](architecture/runner.md) now records a target exception as `ExceptionType: message` in the model Step `error`; `load_cases` no longer reassigns its `source` argument (no behavior change).
* **Addition**: Documented the [Runner](architecture/runner.md) and `load_cases`.
* **Update**: [Metric contract](metrics/metric-contract.md) now records that a wrong subject becomes an `EvaluationFailure` rather than raising, and the `Registry` import-cycle note; tests moved to `test_metric.py` and `tests/registries/test_registry.py`.
* **Update**: [Step efficiency](metrics/step-efficiency.md) tolerates unset `expected_steps`; tests moved to `tests/metrics/test_agent.py`.
* **Update**: [Package organization](architecture/package-organization.md) now describes the `Metric` contract and `Registry`.
* **Addition**: Documented the public [metric contract and Registry](metrics/metric-contract.md) (`Metric`, `MetricOutcome`, `Registry`); a missing `requires` input emits an `EvaluationFailure` and no Score.
* **Addition**: Documented the [step efficiency](metrics/step-efficiency.md) agent metric.
* **Update**: Listed both in the [metrics index](metrics/index.md).
* **Update**: [Domain models](architecture/domain-models.md) now record `Experiment.total_judge_usage(pricing)` for pricing the Judge bucket, and `PricingConfig.cost`, which `Trajectory.total_usage` now uses.
* **Update**: [Domain models](architecture/domain-models.md) now record `TokenUsage` addition, `Score` rejecting non-numeric values and requiring `target_id` for step targets, and the `StepKind` and `ScoreTarget` types.
* **Addition**: Documented the vendor-neutral [domain models](architecture/domain-models.md) (`Trajectory`, `Step`, `Score`, `Experiment`, `EvaluationFailure`, `Dataset`, `Case`); `PricingConfig` moved to `assayer.models`.
* **Update**: Listed the new models in [package organization](architecture/package-organization.md).

## 2026-10-16
* **Addition**: Documented the [semantic similarity](metrics/semantic-similarity.md) metric, now clamped to the [0, 1] range (float overshoot above 1 is capped).
* **Addition**: Documented the [package organization](architecture/package-organization.md) conventions.

## 2026-10-11
* **Addition**: Documented the `usage-report` session recaps (`away_summary`) in [usage-report skill](skills/usage-report.md).

## 2026-09-20
* **Creation**: Scaffolded the Project knowledge bundle with `okf_init.py` — see [getting started](getting-started.md).

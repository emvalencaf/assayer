# Update Log

## 2026-10-17
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

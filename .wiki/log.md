# Update Log

## 2026-10-17
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

# Architecture

* [Package organization](package-organization.md) - subpackages, their roles and conventions.
* [Domain models](domain-models.md) - Trajectory, Step, Score, Experiment, Dataset, Case and their validation rules.
* [Runner](runner.md) - runs a target over a Dataset and returns an Experiment; `score` scores collected outputs.
* [Adapters](adapters.md) - export an Experiment to an observability backend: `Adapter`, `ExportReport`, deterministic ids.
* [Per-Field measurement](field-measurement.md) - `Runner(field_metrics=...)` scores output Fields by dotted path.
* [Comparison](comparison.md) - `compare(a, b)` diffs two Experiments (b minus a).

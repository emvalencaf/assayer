# Architecture

* [Package organization](package-organization.md) - subpackages, their roles and conventions.
* [Domain models](domain-models.md) - Trajectory, Step, Score, Experiment, Dataset, Case and their validation rules.
* [Runner](runner.md) - runs a target over a Dataset and returns an Experiment; `score` scores collected outputs.
* [Comparison](comparison.md) - `compare(a, b)` diffs two Experiments (b minus a).

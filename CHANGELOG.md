# Changelog

## [Unreleased]

### Fixed
- README no longer claims that results are pushed to LangSmith automatically: the `Runner` never calls `LangSmithPublisher`.

### Added
- Alignment of list Fields (#29): `Runner(field_metrics={"items": ListField(properties={"name": [metric]}, align="best_match")})` pairs each predicted item with an expected one by `key`, `best_match` (default: greedy by descending similarity, threshold 0.5, ties by position) or `positional`, and scores the pairs property by property (mean over the pairs, at `items.name`). `list_precision`, `list_recall` and `list_f1` penalise missing and extra items, with the pairs and the unmatched indexes in their `metadata["alignment"]`; both empty scores 1.0, and nested `ListField`s align recursively.
- Per-Field measurement (#28): `Runner(field_metrics={"address.city": [metric, (metric, {"tolerance": 1})]})` scores each Field on its own, addressed by dotted path (a numeric segment indexes a list), with per-pair parameters passed to the metric's function. The metric sees the Field's value as `final_output` and the Case's as `expected_output`; its Scores and `EvaluationFailure`s carry the `field`, `Experiment.scores_by_field()` groups them, and a metric without a Field still scores the whole output. A malformed map is rejected when the Runner is built, before any target call; only trajectory-level metrics are accepted for now.
- `Runner.score(dataset, outputs)` scores collected outputs or Trajectories without calling the target, and `compare(a, b)` (`assayer.runner`) returns a `Comparison` with the delta per (metric, Field), `None` when a metric is on one side only, plus mean token and cost deltas per Case (#27). `Experiment.pricing` (set by `Runner(pricing=...)`) keeps the target's prices so `compare` can price each side; it is never applied to the Judge, and an Experiment with no recorded usage yields `None` token and cost deltas, not `0`. The usage deltas cover only the Cases both Experiments have; the others are listed in `Comparison.only_in_a` and `only_in_b`.
- New `Runner` (`assayer.runner`) that runs a target over a Dataset and returns an Experiment (#26): a plain return value is wrapped in one model Step, `repetitions=k` keeps each repetition as its own Trajectory, and Scores and evaluation failures land on the Experiment. `load_cases` loads a Dataset from a list or JSON and validates only the fields the chosen metrics `require`. The legacy pipelines are untouched.
- Public metric contract `Metric` (`level`, `requires`, deterministic or Judge-based), the `Registry` that holds built-in and custom metrics alike, and `step_efficiency` as the first metric on it (#25). A missing `requires` input emits no Score and an `EvaluationFailure`; the legacy registries stay until the clean break.
- Vendor-neutral models `Trajectory`, `Step`, `Score`, `Experiment`, `EvaluationFailure`, `Dataset` and `Case` beside the legacy ones (#24); `PricingConfig` moved to `assayer.models` and still importable from `assayer.runner.pricing`.
- `Experiment.total_judge_usage(pricing)` prices the Judge bucket. `TokenUsage` supports addition; `Score` requires `target_id` for step targets and rejects non-numeric values.
- Research notes under `docs/research/` on agent metrics, LLM/RAG metrics, Langfuse, LangSmith, OpenTelemetry/OpenInference and library packaging.
- `GLOSSARY.md` with the initial domain language: Trajectory, Score, Adapter and Judge.
- Domain terms Step, Dataset, Case, Experiment, Field, Alignment and End state in `GLOSSARY.md`, and ADR 0001 for the own Trajectory format.
- Harness template: agent skills, git hooks, CI, `.wiki/` knowledge bundle and `docs/agents/`.
- `Package organization` section in `CODE_STANDARDS.md`.
- Test job in CI and a `dev` dependency group with `pytest`.

### Fixed
- `semantic_similarity` clamps float overshoot to the documented [0, 1] range.

### Changed
- CI skips the test job on PRs that only touch Markdown, `docs/` or `.wiki/`, and caches Hugging Face models.
- README follows the Best-README-Template structure.
- `register_chat_metrics` moved to `assayer/metrics/chat.py`; `assayer.metrics` now re-exports the chat, classification and NER metrics with `__all__`.
- Tests moved into `tests/<subpackage>/` mirroring the package.
- Runtime dependencies declared in `pyproject.toml` and `uv.lock` generated.
- ruff lint and format applied to the whole repository; tests relax stylistic rules via `per-file-ignores`.
- README documents the status line budget.
- Commit convention: `Session-Id` trailer is optional and the title has no length limit.

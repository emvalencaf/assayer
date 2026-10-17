# Changelog

## [Unreleased]

### Fixed
- README no longer claims that results are pushed to LangSmith automatically: the `Runner` never calls `LangSmithPublisher`.

### Added
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

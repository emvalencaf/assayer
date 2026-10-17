# Changelog

## [Unreleased]

### Added
- Harness template: agent skills, git hooks, CI, `.wiki/` knowledge bundle and `docs/agents/`.
- `Package organization` section in `CODE_STANDARDS.md`.
- Test job in CI and a `dev` dependency group with `pytest`.

### Changed
- README follows the Best-README-Template structure.
- `register_chat_metrics` moved to `assayer/metrics/chat.py`; `assayer.metrics` now re-exports the chat, classification and NER metrics with `__all__`.
- Tests moved into `tests/<subpackage>/` mirroring the package.
- Runtime dependencies declared in `pyproject.toml` and `uv.lock` generated.
- ruff lint and format applied to the whole repository; tests relax stylistic rules via `per-file-ignores`.
- README documents the status line budget.
- Commit convention: `Session-Id` trailer is optional and the title has no length limit.

# Code Standards

These standards apply to everything committed here.

## General

- Keep changes small and focused; one concern per commit.
- No secrets, tokens or personal data in the repo. Use `.env` (ignored) and
  document variables in `.env.example`.
- Every behavior change comes with a test, or a stated reason why not.

## Stack

- Language: Python ≥ 3.11, managed with `uv`.
- Lint and format: `ruff` (config in `pyproject.toml`), enforced by the `pre-commit` hook.
- Encoding: UTF-8, NFC-normalized, no BOM, no zero-width or bidi control characters
  (enforced by `scripts/check_unicode.py`).
- Types: no type checker.
- Tests: `pytest`, run as `uv run --group dev pytest`; tests live in `tests/`.
- Directory layout: flat package `assayer/` at the repository root; tests in `tests/`.
- Docstrings: Google style.

## Package organization

The `assayer/` package is split by responsibility. Each subpackage owns one
concern, and dependencies point from the outer layers inward:
`runner` → `evaluators`, `metrics`, `registries`, `integrations` → `judges` → `models`.

| Subpackage | Holds | Does not hold |
|---|---|---|
| `models/` | Plain data structures (`@dataclass`) that carry results: `TokenUsage`, `PricingConfig`, `FieldEvaluation`, `RunResult`, `ExperimentResult`, the `Consistency*` family and the vendor-neutral `Trajectory`, `Step`, `Score`, `Experiment`, `EvaluationFailure`, `Dataset` and `Case` | Logic that calls evaluators, I/O or external services |
| `judges/` | The Judge Protocol and `JudgeResponse`, the versioned and hashed `Prompt`, tolerant verdict parsing (`score` + `reason`) and the ledger of Judge calls and tokens | Metrics, scoring decisions, provider clients |
| `evaluators/` | `BaseEvaluator` (ABC) and its implementations (`ner`, `hallucination`, `consistency`) | Aggregation across a dataset |
| `metrics/` | The `Metric` contract (`level`, `requires`, `kind`) and built-in metrics, grouped by task (`agent`, `chat`, `classification`, `ner`, `consistency`, `field` for the Field comparisons, `judge` for the Judge-based ones; `corpus` lifts the chat, classification and NER functions to Experiment level); legacy ones are pure functions `(predictions, references) -> float` | State, network calls |
| `registries/` | `Registry` (holds `Metric` objects) and the legacy `MetricRegistry` and `EvaluatorRegistry` | Built-in metric or evaluator definitions |
| `runner/` | Pipelines (`EvaluationPipeline`, `HistoricalPipeline`, `ConsistencyPipeline`), `FieldRouter`, dataset loading, `Runner` (target → Experiment), the `field_map/` package (field metrics, Alignment of list Fields, Field scoring, the schema utility and YAML/JSON loading), token extraction, pricing, comparison | Metric math |
| `alignment.py`, `path.py` (top level) | Alignment of list items and dotted-path `resolve`, pure helpers shared by `metrics/` and `runner/field_map/`; they import nothing else from `assayer` but each other | Metric or pipeline logic |
| `integrations/` | Adapters for external services (`langsmith`) | Domain rules |

Conventions:

- **One concept per module.** One model or pipeline class per file, named after
  the class in `snake_case` (`token_usage.py` holds `TokenUsage`). Metrics are
  grouped by task, one module per task.
- **Public API through `__init__.py`.** Each subpackage re-exports its public
  names and lists them in `__all__`. Import across subpackages from the package
  (`from assayer.models import FieldEvaluation`), not from the inner module.
- **Registries are instantiable.** They hold no global state. Shared defaults
  (`default_metric_registry`, `default_evaluator_registry`) are a convenience, not
  the only access path.
- **Registration is explicit.** A task module exposes `register_<task>_metrics(registry)`
  or `register_<task>_evaluators(registry)` that fills a registry passed in.
  Importing a module never registers anything as a side effect.
- **Extend by adding, not editing.** A new metric or evaluator is a new module or
  function plus a registration call; core files stay untouched.
- **Metric factories** that need configuration are named `make_<metric>` and
  return a `MetricFn` (`Callable[[list, list], float]`).
- **Optional heavy dependencies** (for example `sentence_transformers`) are
  imported defensively so the package still imports without them.

Tests mirror the package: `tests/<subpackage>/test_<module>.py` (`tests/runner/test_pipeline.py` covers `assayer/runner/pipeline.py`).

## Documentation

- Every project `README.md` follows the section structure of
  [Best-README-Template](https://github.com/othneildrew/Best-README-Template), in
  this order: header block (title, one-line description, links), Table of Contents,
  About The Project (with Built With), Getting Started (Prerequisites,
  Installation), Usage, Roadmap, Contributing, License, Contact, Acknowledgments.
  Drop a section that does not apply instead of leaving it empty.
- Keep the `readme-top` anchor and a "back to top" link after each section.
- Start a new README from
  `.agents/skills/setup-project-harness/assets/README.template.md`; `/setup-project-harness`
  does this for you.
- Do not add badges that point to a private repository (they render broken), and
  do not put personal e-mail addresses in the README; link the GitHub profile.
- Update the README in the same PR as the change it describes.

## Skills

- **Location:** the source lives in `.agents/skills/<name>/`. `.claude/skills/<name>`
  is a relative symlink to it (`../../.agents/skills/<name>`). Never duplicate a
  skill's files.
- **Entry point:** each skill has a `SKILL.md` with YAML frontmatter:
  - `name` — matches the directory name, kebab-case.
  - `description` — what it does **and** when to use it, including trigger
    phrases. This is what an agent reads to decide whether to invoke it.
  - `user-invocable` and, when it takes input, `argument-hint` listing every
    argument (`<required>`, `[optional]`).
  - `allowed-tools` — the minimum needed; read-only skills get no write tools.
- **Body:** imperative instructions for an agent, not prose for a human. State
  defaults, limits and failure behavior explicitly. Keep `SKILL.md` short; move
  long material to `references/` and link it.
- **Supporting files:** never leave them loose in the skill root, which holds
  only `SKILL.md` and these folders: scripts in `scripts/`, documents the agent
  reads on demand in `references/`, and templates or seed files the agent copies
  into a project in `assets/`. Link them from `SKILL.md` with relative paths.
  Scripts must be deterministic and runnable from the CLI.
- **Third-party skills** tracked in `skills-lock.json` follow the same layout.
  Moving their files changes the lock hash and a `skills update` brings the files
  back to the root, so re-apply the layout after updating. Local skills are not
  listed there.

## Markdown

- One H1 per file. Headings in sentence case.
- Wrap prose at ~80 columns. Tables and code blocks are exempt.
- Fenced code blocks always declare a language (`bash`, `yaml`, `text`).
- Use relative links between files in the repo.

## Scripts

- Python scripts run with `uv run` and declare dependencies inline (PEP 723).
- Fail with a non-zero exit code and a clear message; never swallow errors.

## Language

- Code, comments, commits, PRs and documentation are written in English.

## Review checklist

- [ ] Follows the commit convention in [CONTRIBUTING.md](CONTRIBUTING.md)
- [ ] Skill frontmatter complete; `.claude/skills` symlink present
- [ ] No secrets, tokens or personal data
- [ ] [CHANGELOG.md](CHANGELOG.md) updated

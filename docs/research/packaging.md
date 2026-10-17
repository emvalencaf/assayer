# Research: Python library patterns for heavy extras and publishing

Issue: emvalencaf/assayer#7 (child of map #2). Date: 2026-10-16.

## Question

Which patterns suit a Python library with a lightweight core and heavy extras
(torch, transformers)? Covers extras layout in `pyproject.toml`, lazy imports
with clear errors, versioning, publishing options (PyPI, private index, git),
and how other repositories consume the library via uv/pip.

## Current state

`pyproject.toml` declares every dependency as mandatory: `bert-score`,
`langchain-core`, `langsmith`, `nltk`, `numpy`, `rouge-score`, `scikit-learn`,
`sentence-transformers`, `torch`, `transformers`. No upper/lower bounds, no
extras. Version is static `0.1.0`; build backend is setuptools.

Heavy imports in the code today:

| Module | Import | Style |
|---|---|---|
| `metrics/chat.py` | `sentence_transformers` | module-level `try/except ImportError` -> `None`, plus inline fallback import |
| `metrics/chat.py` | `bert_score` | inline import inside a function, inside `try` |
| `evaluators/hallucination.py` | `transformers` | inline import in `_get_classifier` (lazy, no friendly error) |
| `metrics/chat.py` | `nltk`, `numpy`, `rouge_score` | module-level (light enough) |
| `metrics/classification.py` | `sklearn` | module-level |
| `integrations/langsmith.py` | `langsmith` | module-level |
| `evaluators/hallucination.py` | `langchain_core` | module-level |

`torch` is never imported directly; it arrives transitively via
`sentence-transformers`, `transformers` and `bert-score`.

## Findings

### 1. Extras layout

- Published extras live in `[project.optional-dependencies]`; users request
  them as `assayer[ml]`. Dependency groups (`[dependency-groups]`, PEP 735) are
  local-only and are NOT published, so they are for dev tooling (pytest, ruff),
  never for user-facing features.
- Common convention (scikit-learn, Hugging Face libs, LangChain partners): a
  small core with pure-Python / light deps, one extra per heavy capability,
  and an `all` extra that unions them.
- Do not declare `torch` as a hard dependency of the core. Let the extra that
  needs it pull it in transitively (`sentence-transformers`, `transformers`
  already require torch). Listing torch explicitly is only useful to pin a
  floor.
- Self-referencing extras keep `all` DRY:
  `all = ["assayer[embeddings,bertscore,hallucination,langsmith]"]` (supported
  by pip and uv; requires the project name to be installable).
- Torch variant (CPU vs CUDA) is a consumer decision. PyPI torch gives CUDA
  wheels on Linux and CPU on macOS/Windows. A library should NOT pin a torch
  index in published metadata: `[tool.uv.sources]` is honored only by uv, only
  for the root project, and is ignored when the package is installed as a
  dependency. Per-variant `cpu`/`cu130` extras with `[tool.uv] conflicts` are
  documented by uv but are meant for applications; for a library, document how
  consumers pick an index instead.

### 2. Lazy imports with clear errors

Pattern in widespread use (pandas `import_optional_dependency`, Hugging Face
`requires_backends`, LangChain `ImportError("... pip install ...")`):

- Keep `import assayer` and `import assayer.metrics` free of heavy imports.
  Import inside the function/method that needs it, or via a small helper.
- Raise an `ImportError` (or subclass) that names the missing package AND the
  extra to install, chaining the original with `from exc`.
- Do not swallow the error into `None` at module level (current
  `SentenceTransformer = None`); that hides the real cause and defers a
  confusing `TypeError`. The only reason to keep a module-level name is test
  patching; a lazy getter function can be patched equally well.
- For type hints use `if TYPE_CHECKING:` imports plus string annotations.
- Check version floors in the helper if a feature needs one.

Sketch (one helper in e.g. `assayer/_optional.py`):

```python
from importlib import import_module


def require(module: str, extra: str, purpose: str):
    try:
        return import_module(module)
    except ImportError as exc:
        raise ImportError(
            f"{purpose} requires '{module}'. Install it with: pip install 'assayer[{extra}]'"
        ) from exc
```

Gotchas: `import sklearn`, `import nltk` and `import langsmith` are moderately
heavy (sklearn pulls scipy); if the core is meant to be truly light, either
accept them in core or move `classification` to an extra. Also note
`transformers.pipeline(..., return_all_scores=True)` is deprecated upstream in
favor of `top_k=None`; unrelated to packaging but will break with newer
transformers, so bounds matter.

### 3. Proposed split (for the map to confirm)

| Group | Dependencies | Used by |
|---|---|---|
| core | `numpy`, `nltk`, `rouge-score`, `scikit-learn`, `langchain-core`, `langsmith` | deterministic metrics, evaluators, LangSmith integration |
| `embeddings` | `sentence-transformers` | embedding-similarity metric |
| `bertscore` | `bert-score` | BERTScore metric |
| `hallucination` | `transformers` (+ `torch`) | classifier-based hallucination evaluator |
| `ml` | union of the three above | convenience |
| `all` | `ml` plus any future extras | convenience |
| dev group | `pytest`, `pytest-cov`, `ruff` | contributors only |

`langsmith` could itself become an extra if the LLM-as-Judge path should work
without it; decision depends on map #2. Add lower bounds on every dependency
(and upper bounds only on known-fragile ones such as `transformers`).

### 4. Versioning

- Use SemVer; while `0.x`, minor bumps may break. Keep `CHANGELOG.md`
  (already present) as the source for release notes.
- Single source of truth for the version: either static in `pyproject.toml`
  (simple, current) or dynamic from git tags via `setuptools-scm` /
  `hatch-vcs`. Static plus a release PR from `development` to `master` (the
  existing branch strategy) is the least moving parts; tag `vX.Y.Z` on
  `master` after the release PR merges. Dynamic versioning matters mainly when
  consuming from git without PyPI, since the commit hash then maps to a
  version; with setuptools-scm, sdist/wheel builds from a tag are exact.
- Expose `assayer.__version__` via `importlib.metadata.version("assayer")`
  rather than a duplicated literal.
- Commit `uv.lock` for dev reproducibility; it is not used by consumers.

### 5. Publishing options

| Option | Pros | Cons |
|---|---|---|
| PyPI (public) | `pip install assayer`, extras resolve normally, version pinning, best discoverability | public; name must be free; releases are immutable (yank only) |
| TestPyPI | safe rehearsal of the release pipeline | not a real distribution channel |
| Private index (GitHub Packages does NOT host Python; use devpi, Artifactory, AWS CodeArtifact, Gemfury, Cloudsmith) | access control, fits an internal project | needs infra and credentials; consumers must configure an index and `--index-strategy` carefully (dependency-confusion risk) |
| Git dependency (`git+https://github.com/emvalencaf/assayer@vX.Y.Z`) | zero infra; works today; can pin tag or commit | builds from source on each install, no index-side metadata, slower resolves, private repo needs a token/SSH; uv cache keys on the commit |
| GitHub Release wheels (attach built wheel/sdist, install by URL) | pinned artifact, no build on install | manual URL management, no resolver discovery |

Release automation: build with `uv build` (or `python -m build`), publish with
`uv publish` or `pypa/gh-action-pypi-publish` using PyPI Trusted Publishing
(OIDC, no stored token), triggered by a `v*` tag. Validate with `twine check`
and install the built wheel in a clean venv with and without extras.

Recommendation: start with git tags (immediate, free), add TestPyPI to
exercise the pipeline, then PyPI under Trusted Publishing once the API is
stable; use a private index only if the project must stay non-public.

### 6. How other repositories consume it

pip:

```bash
pip install 'assayer[ml] @ git+https://github.com/emvalencaf/assayer@v0.2.0'
pip install 'assayer[ml]'            # once on PyPI
pip install 'assayer[ml]' --extra-index-url https://pkg.example.com/simple  # private
```

uv (consumer `pyproject.toml`):

```toml
[project]
dependencies = ["assayer[embeddings]"]

[tool.uv.sources]
assayer = { git = "https://github.com/emvalencaf/assayer", tag = "v0.2.0" }
# local development against a checkout:
# assayer = { path = "../assayer", editable = true }

# private index alternative:
# assayer = { index = "internal" }
# [[tool.uv.index]]
# name = "internal"
# url = "https://pkg.example.com/simple"
# explicit = true
```

CLI shortcut: `uv add "assayer[embeddings] @ git+https://github.com/emvalencaf/assayer" --tag v0.2.0`.

Notes:

- `[tool.uv.sources]` must be set in the CONSUMER; assayer cannot ship it to
  downstream users. Plain pip ignores it, so assayer's own metadata must stay
  index-agnostic.
- The consumer chooses the torch build with its own `[[tool.uv.index]]`
  (`explicit = true`, name e.g. `pytorch-cpu`) and
  `torch = { index = "pytorch-cpu" }` in its sources. With `uv pip`, the
  `--torch-backend=auto` flag picks a build from the detected driver.
- Tell consumers that installing the core alone should be fast and small; the
  README should list extras and the exact `ImportError` hint they will see.

## Recommendations (summary)

1. Move `sentence-transformers`, `bert-score`, `transformers` (and thereby
   torch) out of core into extras `embeddings`, `bertscore`, `hallucination`;
   add `ml` and `all`.
2. Replace the module-level `try/except -> None` and bare inline imports with
   one `require()` helper raising an actionable `ImportError` naming the extra.
3. Keep the version static, tag releases `vX.Y.Z` from `master`, expose
   `__version__` via `importlib.metadata`.
4. Distribute via git tag first, rehearse on TestPyPI, then PyPI with Trusted
   Publishing; do not embed torch index config in published metadata.
5. Document consumer snippets (pip and uv) and torch variant selection in the
   README.

## Open questions for the map

- Is the library meant to be public (PyPI) or internal (private index/git)?
- Should `langsmith` and `scikit-learn` stay in core?
- Minimum supported versions of torch/transformers to test against (a CI
  matrix with a core-only job and a full-extras job would verify the split).

## Sources

- uv: Managing dependencies (extras, groups, sources, indexes):
  https://docs.astral.sh/uv/concepts/projects/dependencies/
- uv: Using PyTorch: https://docs.astral.sh/uv/guides/integration/pytorch/
- Python Packaging User Guide, optional dependencies / PEP 735 dependency
  groups / PyPI Trusted Publishing (general knowledge, not re-fetched).
- Code inspection of this repository at branch `research/packaging-redo`.

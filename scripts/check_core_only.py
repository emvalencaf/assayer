"""Check that the environment holds only the core: no extra is installed, and the core works.

Run in CI by `uv run --isolated --no-dev scripts/check_core_only.py`.
"""

import importlib
import importlib.util
import sys

import assayer.adapters
import assayer.judges
from assayer.metrics import bleu

OPTIONAL = [
    "bert_score",
    "langchain_core",
    "langfuse",
    "langsmith",
    "nltk",
    "rouge_score",
    "sentence_transformers",
    "torch",
    "transformers",
    "yaml",
]

installed = [name for name in OPTIONAL if importlib.util.find_spec(name)]
if installed:
    sys.exit(f"not a core-only environment, installed: {installed}")

for name in ("assayer", "assayer.metrics", "assayer.judges", "assayer.adapters"):
    importlib.import_module(name)

for load, extra in (
    (lambda: assayer.judges.LangChainJudge, "langchain"),
    (lambda: assayer.adapters.LangfuseAdapter, "langfuse"),
    (lambda: assayer.adapters.LangSmithAdapter, "langsmith"),
    (lambda: bleu(["a"], ["a"]), "text"),
):
    try:
        load()
    except ImportError as exc:
        if f"assayer[{extra}]" not in str(exc):
            sys.exit(f"ImportError does not name assayer[{extra}]: {exc}")
    else:
        sys.exit(f"no ImportError for the {extra} extra")

print("core-only environment OK")

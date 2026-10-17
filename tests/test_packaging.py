import subprocess
import sys
import textwrap

import pytest

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


def run_core_only(code: str) -> subprocess.CompletedProcess:
    """Run code in a fresh interpreter where no optional dependency can be imported."""
    prelude = f"""
import sys

class Blocker:
    def find_spec(self, name, path=None, target=None):
        if name.split(".")[0] in {OPTIONAL!r}:
            raise ImportError(f"No module named {{name!r}}")

sys.meta_path.insert(0, Blocker())
"""
    return subprocess.run(
        [sys.executable, "-I", "-c", prelude + textwrap.dedent(code)],
        capture_output=True,
        text=True,
        cwd=".",
        env={"PYTHONPATH": "."},
    )


def test_public_modules_import_without_extras():
    result = run_core_only(
        """
        import assayer, assayer.metrics, assayer.judges, assayer.adapters
        for module in (assayer, assayer.metrics, assayer.judges, assayer.adapters):
            assert isinstance(module.__all__, list)
        """
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("statement", "extra"),
    [
        ("from assayer.judges import LangChainJudge", "langchain"),
        ("from assayer.adapters import LangfuseAdapter", "langfuse"),
        ("from assayer.adapters import LangSmithAdapter", "langsmith"),
        ("from assayer.integrations import LangfuseAdapter", "langfuse"),
        ("from assayer.metrics import bleu; bleu(['a'], ['a'])", "text"),
        ("from assayer.metrics import rouge_l; rouge_l(['a'], ['a'])", "text"),
        ("from assayer.metrics import bert_score; bert_score(['a'], ['a'])", "semantic"),
        (
            "from assayer.metrics import make_semantic_similarity;"
            " make_semantic_similarity()(['a'], ['a'])",
            "semantic",
        ),
    ],
)
def test_missing_extra_raises_import_error_naming_it(statement, extra):
    result = run_core_only(
        f"""
        try:
            {statement}
        except ImportError as exc:
            assert "assayer[{extra}]" in str(exc), str(exc)
        else:
            raise SystemExit("no ImportError")
        """
    )
    assert result.returncode == 0, result.stderr + result.stdout


def test_unknown_attribute_is_still_an_attribute_error():
    import assayer.adapters

    with pytest.raises(AttributeError):
        _ = assayer.adapters.NoSuchAdapter


def test_py_typed_is_shipped():
    from importlib.resources import files

    assert files("assayer").joinpath("py.typed").is_file()

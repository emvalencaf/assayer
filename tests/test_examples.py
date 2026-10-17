"""The examples and the offline README snippets run against the current API."""

import re
import runpy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "examples").glob("*.py"))


@pytest.mark.parametrize("path", EXAMPLES, ids=lambda p: p.name)
def test_example_runs(path, capsys):
    runpy.run_path(str(path), run_name="__main__")

    assert capsys.readouterr().out.strip()


def _readme_snippets() -> dict[str, str]:
    """The README's Python blocks, keyed by the first line of the text above each."""
    blocks = re.findall(r"```python\n(.*?)```", (ROOT / "README.md").read_text(), re.S)
    return {block.splitlines()[0]: block for block in blocks}


# first line of the snippet -> (label, modules it needs beyond the core)
OFFLINE = {
    "from assayer.metrics import corpus_metric, make_f1": ("quick start", []),
    "from assayer.metrics import Metric": ("custom metric", []),
    "from assayer.metrics import bleu, corpus_metric, rouge_l": (
        "text extra",
        ["nltk", "rouge_score"],
    ),
    "from pathlib import Path": ("yaml extra", ["yaml"]),
    "from langchain_core.language_models.fake_chat_models import FakeListChatModel": (
        "langchain extra",
        ["langchain_core"],
    ),
}


@pytest.mark.parametrize("first_line", OFFLINE, ids=[label for label, _ in OFFLINE.values()])
def test_offline_readme_snippet_runs(first_line, tmp_path, monkeypatch):
    for module in OFFLINE[first_line][1]:
        pytest.importorskip(module)
    monkeypatch.chdir(tmp_path)

    exec(compile(_readme_snippets()[first_line], "README.md", "exec"), {"__name__": "__main__"})

<a id="readme-top"></a>

<!-- Structure adapted from https://github.com/othneildrew/Best-README-Template -->

<br />
<div align="center">
  <h3 align="center">Assayer</h3>

  <p align="center">
    A Python library for evaluating and observing LLM-powered applications, with
    deterministic metrics and LLM-as-Judge.
    <br />
    <a href="https://github.com/emvalencaf/assayer/blob/master/CONTRIBUTING.md"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/emvalencaf/assayer/issues/new">Report Bug</a>
    &middot;
    <a href="https://github.com/emvalencaf/assayer/issues/new">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#features">Features</a></li>
        <li><a href="#core-abstractions">Core Abstractions</a></li>
        <li><a href="#non-goals">Non-Goals</a></li>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#usage">Usage</a>
      <ul>
        <li><a href="#quick-start">Quick start</a></li>
        <li><a href="#using-assayer-from-another-repository">Using Assayer from another repository</a></li>
        <li><a href="#token-cost-tracking">Token cost tracking</a></li>
        <li><a href="#examples">Examples</a></li>
        <li><a href="#migrating-from-the-legacy-api">Migrating from the legacy API</a></li>
        <li><a href="#running-tests">Running tests</a></li>
        <li><a href="#status-line-budget">Status line budget</a></li>
      </ul>
    </li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## About The Project

A Python library for evaluating and observing LLM-powered applications and agents.
A `Runner` runs your target over a `Dataset` of `Case`s, keeps what it did as
`Trajectory`s and scores them with metrics, deterministic or judge-based
(LLM-as-Judge), into an `Experiment`. Token costs are tracked per run, and an
Experiment can be exported to LangSmith with `LangSmithAdapter` and to Langfuse with
`LangfuseAdapter`.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Features

- **Chat quality metrics**: BLEU, ROUGE-L, BERTScore, semantic similarity
- **Classification metrics**: accuracy, precision, recall, F1
- **NER evaluation**: entity-level F1 by type, macro F1
- **Agent metrics**: tool correctness, tool arguments, end state and step efficiency
- **Judge-based metrics**: criteria, goal success and faithfulness to the retrieved context, with any Judge you inject
- **Retrieval metrics**: context precision and recall
- **Structured output**: score each Field of the output on its own, including lists of objects, with a field map in code, YAML or JSON
- **Consistency**: run a Case k times and measure agreement, entropy, pass@k and pass^k
- **Token cost tracking**: input/output tokens and estimated USD cost per run, comparable across experiments
- **Extensible**: write a `Metric` and register it, without modifying core files
- **Observability integrations**: `Runner(adapter=LangSmithAdapter()).export(experiment)` (or `LangfuseAdapter()`) sends Cases, traces and Scores to LangSmith or Langfuse through a vendor-neutral Adapter

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Core Abstractions

| Abstraction | Role |
|-------------|------|
| `Dataset` / `Case` | A named collection of inputs, each with an optional reference to compare against (a list, a JSON file or `Dataset`) |
| `Runner` | Runs a target over a Dataset, applies metrics and returns an Experiment; `score` does the same for outputs collected beforehand |
| `Trajectory` / `Step` | What the target did for one input: model calls, tool calls and retrievals, up to the final answer |
| `Metric` | Names a way of computing Scores for a Step, a Trajectory or a whole Experiment |
| `Registry` | Holds metrics by name, built-in and custom alike |
| `Experiment` | The Trajectories, Scores and evaluation failures of one run, with tokens and cost |
| `Judge` | The injected language model behind judge-based metrics |
| `Adapter` | The boundary to an observability backend |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Non-Goals

- No model training or fine-tuning
- No built-in UI; visualization is delegated to an observability backend once the Adapters land
- No LLM inference hosting
- No billing; cost tracking is observational only

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [Python](https://www.python.org) managed with [uv](https://docs.astral.sh/uv/)
* [LangSmith](https://www.langchain.com/langsmith) and [Langfuse](https://langfuse.com)
* [Transformers](https://huggingface.co/docs/transformers) and [PyTorch](https://pytorch.org)
* [pytest](https://docs.pytest.org) for tests
* [ruff](https://docs.astral.sh/ruff/) for lint and format

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

* Python 3.11.13+
* [`uv`](https://docs.astral.sh/uv/) (runs the git hooks and tests)

### Installation

To use the library, install it from PyPI (the import name is `assayer`):

```bash
pip install llm-assayer-eval            # or 'llm-assayer-eval[all]' for every extra
```

To work on it, clone the repository:

1. Clone the repository
   ```bash
   git clone https://github.com/emvalencaf/assayer.git
   cd assayer
   ```
2. Create a virtual environment and install the package
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e '.[all]'
   ```
   The core (`pip install llm-assayer-eval`) needs only `numpy` and `scikit-learn`. Add what you use:

   | Extra | Brings | Needed for |
   |---|---|---|
   | `semantic` | `bert-score`, `sentence-transformers`, `torch`, `transformers` | `bert_score`, `make_semantic_similarity` |
   | `text` | `nltk`, `rouge-score` | `bleu`, `rouge_l` |
   | `langchain` | `langchain-core` | `LangChainJudge` |
   | `langfuse` | `langfuse` | `LangfuseAdapter` |
   | `langsmith` | `langsmith` | `LangSmithAdapter` |
   | `yaml` | `pyyaml` | YAML field maps |
   | `all` | all of the above | |

   Using something whose extra is missing raises an `ImportError` naming `llm-assayer-eval[<extra>]`.
   Consumers import from `assayer.models`, `assayer.metrics`, `assayer.runner`, `assayer.registries`, `assayer.judges` and `assayer.adapters`.

   **Lazy downloads and offline use.** BERTScore and semantic similarity download their
   Hugging Face models (`roberta-large` and `sentence-transformers/all-MiniLM-L6-v2`, plus the
   BERTScore baseline) on first use into `~/.cache/huggingface`. `bleu` splits on whitespace and needs no NLTK data today; if you add metrics that use NLTK
   tokenizers or corpora, fetch them once with `nltk.download(...)`. To run
   offline, run each metric once with network access, then set `HF_HUB_OFFLINE=1` (and
   `TRANSFORMERS_OFFLINE=1`) so the cache is used without reaching the Hub.
3. Enable the git hooks
   ```bash
   scripts/setup.sh
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

### Quick start

```python
from assayer.metrics import corpus_metric, make_f1
from assayer.models import Case, Dataset
from assayer.runner import Runner

dataset = Dataset(
    "tickets",
    [
        Case(input="My invoice is wrong", id="c1", expected_output="billing"),
        Case(input="The app crashes", id="c2", expected_output="technical"),
    ],
)


def my_llm_chain(text: str) -> str:  # your target: any callable
    return "billing" if "invoice" in text else "general"


runner = Runner(my_llm_chain, [corpus_metric("f1", make_f1())])
experiment = runner.run(dataset)

for score in experiment.scores:
    print(score.name, score.value)
```

`dataset` may also be a list of dictionaries or the path to a JSON file. The target
returns a plain value, which becomes the `final_output` of a one-Step Trajectory, or a
`Trajectory` when it wants to report its Steps, tokens and tool calls.

### Using Assayer from another repository

Install the core plus the extras you use (see [Installation](#installation)), then
import from the subpackages. The core needs no extra:

```bash
pip install llm-assayer-eval                    # numpy and scikit-learn only
pip install 'llm-assayer-eval[text,langchain]'  # or the extras you need
```

The distribution is named `llm-assayer-eval` (the name `assayer` belongs to another
project on PyPI), but the import name stays `assayer`:

```python
import assayer
```


**A custom metric.** A `Metric` is a function `fn(subject, case)` that returns a number in
[0, 1] (or a boolean), at the level it scores: `"step"`, `"trajectory"` or `"experiment"`.
`requires` names the inputs it cannot work without; a Case that lacks one is an
`EvaluationFailure` on the Experiment, not a score of 0.

```python
from assayer.metrics import Metric
from assayer.models import Case, Dataset, Trajectory
from assayer.registries import Registry
from assayer.runner import Runner


def polite(trajectory: Trajectory, case: Case) -> float:
    return float("please" in trajectory.final_output.lower())


registry = Registry()  # optional: look metrics up by name, built-in or custom
registry.register(Metric(name="polite", level="trajectory", fn=polite))

dataset = Dataset("greetings", [Case(input="Greet the user", id="c1")])
experiment = Runner(lambda text: "Please come in", [registry.get("polite")]).run(dataset)

print([(s.name, s.value) for s in experiment.scores])  # [('polite', 1.0)]
```

**One runnable example per extra.** Each snippet is self-contained; the first four run
offline (the semantic one downloads its model once), the last two need credentials.

`text`: BLEU and ROUGE-L over a corpus.

```python
from assayer.metrics import bleu, corpus_metric, rouge_l
from assayer.models import Case, Dataset
from assayer.runner import Runner

dataset = Dataset("qa", [Case(input="q", id="c1", expected_output="the cat sat on the mat")])
metrics = [corpus_metric("bleu", bleu), corpus_metric("rouge_l", rouge_l)]
experiment = Runner(lambda q: "the cat sat on a mat", metrics).run(dataset)
print({s.name: round(s.value, 2) for s in experiment.scores})
```

`semantic`: semantic similarity with a sentence-transformers model.

```python
from assayer.metrics import corpus_metric, make_semantic_similarity
from assayer.models import Case, Dataset
from assayer.runner import Runner

dataset = Dataset("qa", [Case(input="q", id="c1", expected_output="a feline rests on a rug")])
metric = corpus_metric("semantic_similarity", make_semantic_similarity())
experiment = Runner(lambda q: "a cat sleeps on a carpet", [metric]).run(dataset)
print(experiment.scores[0].value)
```

`yaml`: a field map in a YAML file scores each Field of a structured output on its own.

```python
from pathlib import Path

from assayer.models import Case, Dataset
from assayer.runner import Runner, load_field_map

Path("field_map.yaml").write_text(
    "label: [exact_match]\nscore:\n  - numeric_tolerance: {tolerance: 1}\n"
)

dataset = Dataset("fields", [Case(input="x", id="c1", expected_output={"label": "a", "score": 5})])
runner = Runner(
    lambda x: {"label": "a", "score": 6}, field_metrics=load_field_map("field_map.yaml")
)
experiment = runner.run(dataset)
print({(s.field, s.name): s.value for s in experiment.scores})
```

`langchain`: any LangChain chat model becomes the Judge of a judge-based metric. A fake
model keeps the snippet offline; swap in `ChatOpenAI()`, `ChatAnthropic()` or similar.

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from assayer.judges import LangChainJudge
from assayer.metrics import make_criteria_judge
from assayer.models import Case, Dataset
from assayer.runner import Runner

judge = LangChainJudge(FakeListChatModel(responses=['{"score": 5, "reason": "Clear."}']))
metric = make_criteria_judge(judge, criteria="The answer is clear and correct.")

dataset = Dataset("qa", [Case(input="What is 2 + 2?", id="c1")])
experiment = Runner(lambda q: "4", [metric]).run(dataset)
print(experiment.scores[0].value, experiment.scores[0].comment)  # 1.0 Clear.
print(experiment.judge_calls)  # the Judge's calls and tokens are kept apart from the target's
```

`langsmith`: export an Experiment (needs `LANGSMITH_API_KEY`).

```python
from assayer.adapters import LangSmithAdapter
from assayer.models import Case, Dataset
from assayer.runner import Runner

dataset = Dataset("greetings", [Case(input="hi", id="c1", expected_output="hi")])
runner = Runner(lambda text: text, adapter=LangSmithAdapter())
report = runner.export(runner.run(dataset))
print(report.ok, len(report.confirmed))
```

`langfuse`: the same with Langfuse (needs `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` and,
outside the EU cloud, `LANGFUSE_BASE_URL`).

```python
from assayer.adapters import LangfuseAdapter
from assayer.models import Case, Dataset
from assayer.runner import Runner

dataset = Dataset("greetings", [Case(input="hi", id="c1", expected_output="hi")])
runner = Runner(lambda text: text, adapter=LangfuseAdapter())
report = runner.export(runner.run(dataset))
print(report.ok, len(report.confirmed), len(report.queued))
```

An export never raises for an item that fails: read `report.failed` and `report.notes`.
Using something whose extra is missing raises an `ImportError` naming `llm-assayer-eval[<extra>]`.

### Token cost tracking

A Step reports its tokens in `Step.usage`; `model_step(reply, model=...)` (`assayer.runner`) builds a model Step from a LangChain-style reply, reading its `usage_metadata`; `Runner(pricing=PricingConfig(...))` keeps the
target's prices on the `Experiment`, and `Trajectory.total_usage()` and
`Experiment.total_usage()` sum tokens and cost. `compare(a, b)` (`assayer.runner`)
returns a `Comparison` with the delta per (metric, Field) and the mean token and cost
deltas per Case between two Experiments. The Judge's tokens are kept apart in
`Experiment.judge_usage` and are never priced with the target's prices.

### Examples

Runnable scripts in [`examples/`](examples), all offline:

| Script | Shows |
|---|---|
| [`ticket_classification.py`](https://github.com/emvalencaf/assayer/blob/master/examples/ticket_classification.py) | a custom `Metric` plus a built-in metric on one Field of a structured output |
| [`ner_extraction.py`](https://github.com/emvalencaf/assayer/blob/master/examples/ner_extraction.py) | pure NER: `EntitySpan`s scored with entity-level macro F1 |
| [`support_pipeline.py`](https://github.com/emvalencaf/assayer/blob/master/examples/support_pipeline.py) | one structured output scored per Field: classification (accuracy, F1), NER and text generation (ROUGE-L) |
| [`schema_structured_output.py`](https://github.com/emvalencaf/assayer/blob/master/examples/schema_structured_output.py) | a field map drafted from a JSON Schema with `schema_to_field_map`: enums (classification), free text (generation) and extracted values, nested objects, a list of objects and a list of strings, each scored by its type |
| [`agent_tool_use.py`](https://github.com/emvalencaf/assayer/blob/master/examples/agent_tool_use.py) | an agent `Trajectory` scored on tool calls, arguments, end state and steps, then two agents compared on quality and cost |
| [`faithfulness_check.py`](https://github.com/emvalencaf/assayer/blob/master/examples/faithfulness_check.py) | `make_faithfulness` with a scripted Judge over a retrieval Trajectory |
| [`logged_traffic_scoring.py`](https://github.com/emvalencaf/assayer/blob/master/examples/logged_traffic_scoring.py) | scoring live traffic by logging it and scoring batches (see below) |

```bash
uv run --extra all python examples/ner_extraction.py
```

### Historical and live evaluation

- **Historical (offline).** `Runner.run(dataset)` runs your target over a Dataset;
  `Runner.score(dataset, outputs)` scores outputs you collected earlier, from a log, a
  trace export or a CSV, without calling the target. `compare(a, b)` tells two
  Experiments apart, and `export` sends them to LangSmith or Langfuse.
- **Live (online).** Assayer has no live mode of its own: there is no hook that scores
  each request as it is served, and none is planned for now. You can build one in your
  project from the same pieces: capture each interaction as a `Trajectory` where your
  app serves it, and have a job (a cron, a worker, a notebook) call
  `Runner(metrics=...).score(Dataset(...), trajectories)` on the batch, or on a sample of
  it. Production traffic rarely has a reference answer, so use reference-free metrics
  (custom rules, judge-based criteria and faithfulness, cost and latency checks).
  [`examples/logged_traffic_scoring.py`](https://github.com/emvalencaf/assayer/blob/master/examples/logged_traffic_scoring.py) is a
  minimal version of that loop.

### Migrating from the legacy API

The legacy pipelines and their models were removed in one clean break; there are no
aliases. See "Breaking" in [CHANGELOG.md](https://github.com/emvalencaf/assayer/blob/master/CHANGELOG.md) for the full list.

| Legacy | Now |
|---|---|
| `EvaluationPipeline`, `HistoricalPipeline` | `Runner(...).run(dataset)` and `Runner(...).score(dataset, outputs)` |
| `ConsistencyPipeline` | `Runner(repetitions=k)` with `register_consistency_metrics` |
| `ExperimentResult`, `RunResult`, `FieldEvaluation` | `Experiment`, `Trajectory`, `Score` |
| `field_evaluators={"f": ["name"]}`, `FieldRouter` | `Runner(field_metrics={"f": [metric]})` |
| `BaseEvaluator` and `EvaluatorRegistry` | a `Metric` and `Registry` |
| `MetricRegistry`, `register_chat_metrics` and the like | `Registry`, `register_corpus_metrics` |
| `FaithfulnessEvaluator`, `LLMJudgeEvaluator` | `make_faithfulness(judge)`, `make_criteria_judge(judge, ...)` |
| `result.compare(other)` | `compare(a, b)` |
| `LangSmithPublisher` | `LangSmithAdapter` |

### Running tests

```bash
uv run --group dev pytest
uv run --group dev pytest --cov=assayer   # coverage report (target: ≥ 90%)
```

### Status line budget

The Claude Code status line shows spend against a USD budget when you pay per
token. The default is `$ 100`; change it with:

```bash
scripts/set-budget.sh 50            # this project only (.claude/budget, git-ignored)
scripts/set-budget.sh 50 --global   # every project (~/.claude/budget)
scripts/set-budget.sh --show        # budget in effect and where it comes from
scripts/set-budget.sh --clear       # remove it (add --global for the global one)
```

`CLAUDE_BUDGET_USD` overrides both files. The cost is the estimate reported by
Claude Code, not your invoice.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [x] Add a `LICENSE` file
- [x] Pick the PyPI name: `llm-assayer-eval` (import name stays `assayer`)
- [x] Tag and publish `v0.1.0`
- [ ] A first-class live mode (scoring requests as they are served)

See the [open issues](https://github.com/emvalencaf/assayer/issues) for proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions follow the branch strategy and commit convention in
[CONTRIBUTING.md](https://github.com/emvalencaf/assayer/blob/master/CONTRIBUTING.md): cut a branch from `development`, commit as
`tag(subject/subsubject): summary`, and open a pull request into `development`.
Coding and documentation rules are in [CODE_STANDARDS.md](https://github.com/emvalencaf/assayer/blob/master/CODE_STANDARDS.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Released under the MIT license. See [LICENSE](LICENSE).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Edson Mota Valença Filho - [@emvalencaf](https://github.com/emvalencaf)

Project Link: [https://github.com/emvalencaf/assayer](https://github.com/emvalencaf/assayer)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments

* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

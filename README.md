<a id="readme-top"></a>

<!-- Structure adapted from https://github.com/othneildrew/Best-README-Template -->

<br />
<div align="center">
  <h3 align="center">Assayer</h3>

  <p align="center">
    A Python library for evaluating and observing LLM-powered applications, with
    deterministic metrics and LLM-as-Judge.
    <br />
    <a href="CONTRIBUTING.md"><strong>Explore the docs »</strong></a>
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
        <li><a href="#extending-assayer">Extending Assayer</a></li>
        <li><a href="#token-cost-tracking">Token cost tracking</a></li>
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

A Python library for evaluating and observing LLM-powered applications. It
provides a unified interface to run structured evaluations (chat turn quality,
classification accuracy and named entity extraction) using both deterministic
metrics and model-based judges (LLM-as-Judge). Results and token costs are
tracked via LangSmith.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Features

- **Chat quality metrics**: BLEU, ROUGE-L, BERTScore, semantic similarity
- **Classification metrics**: accuracy, precision, recall, F1
- **NER evaluation**: entity-level F1 by type, macro F1
- **Hallucination detection**: reference-based (faithfulness scoring) and LLM-as-Judge
- **Mixed structured output**: evaluate a single chain that returns chat, classification and NER fields in one pipeline run
- **Token cost tracking**: input/output tokens and estimated USD cost per run, comparable across experiments
- **Extensible**: register custom metrics and evaluator types without modifying core files
- **Audit trail**: every evaluated field records method, expected value, obtained value, score and prompt hash
- **LangSmith integration**: all results pushed automatically for experiment tracking and visualization

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Core Abstractions

| Abstraction | Role |
|-------------|------|
| `Dataset` | Collection of input/expected-output pairs (LangSmith or local JSON) |
| `Evaluator` | Scores a single prediction against a reference |
| `Metric` | Aggregates scores across a full dataset |
| `Runner` | Orchestrates runs, applies evaluators/metrics, tracks tokens, pushes to LangSmith |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Non-Goals

- No model training or fine-tuning
- No built-in UI; visualization via LangSmith
- No LLM inference hosting
- No billing; cost tracking is observational only

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

* [Python](https://www.python.org) managed with [uv](https://docs.astral.sh/uv/)
* [LangSmith](https://www.langchain.com/langsmith)
* [Transformers](https://huggingface.co/docs/transformers) and [PyTorch](https://pytorch.org)
* [pytest](https://docs.pytest.org) for tests
* [ruff](https://docs.astral.sh/ruff/) for lint and format

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

### Prerequisites

* Python 3.11.13+
* [`uv`](https://docs.astral.sh/uv/) (runs the git hooks and tests)
* A LangSmith account and API key, exported as `LANGCHAIN_API_KEY`

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/emvalencaf/assayer.git
   cd assayer
   ```
2. Create a virtual environment and install the package
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```
3. Enable the git hooks
   ```bash
   scripts/setup.sh
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

### Quick start

```python
from assayer import Runner, Dataset
from assayer.metrics import bleu, f1
from assayer.evaluators import ChatEvaluator, ClassificationEvaluator

dataset = Dataset.from_json("data/examples.json")

runner = Runner(
    target_fn=my_llm_chain,
    evaluators=[ChatEvaluator(), ClassificationEvaluator()],
    metrics=[bleu, f1],
    experiment_name="my-experiment-v1",
)

result = runner.run(dataset)
print(result.summary())
```

### Extending Assayer

**Custom metric:**
```python
from assayer.registry import MetricRegistry


def my_metric(predictions, references): ...


MetricRegistry.register("my_metric", my_metric)
```

**Custom evaluator:**
```python
from assayer.evaluators import BaseEvaluator
from assayer.registry import EvaluatorRegistry


class MyEvaluator(BaseEvaluator):
    def evaluate(self, prediction, reference): ...


EvaluatorRegistry.register("my_evaluator", MyEvaluator)
```

### Token cost tracking

Every `RunResult` exposes `input_tokens`, `output_tokens` and `cost_usd`. Use
`ExperimentResult.compare(other)` to get per-metric deltas and the average token
cost delta between two experiments.

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

- [ ] Add a `LICENSE` file
- [ ] Tag and publish `v0.1.0`

See the [open issues](https://github.com/emvalencaf/assayer/issues) for proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contributing

Contributions follow the branch strategy and commit convention in
[CONTRIBUTING.md](CONTRIBUTING.md): cut a branch from `development`, commit as
`tag(subject/subsubject): summary`, and open a pull request into `development`.
Coding and documentation rules are in [CODE_STANDARDS.md](CODE_STANDARDS.md).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## License

Released under the MIT license. A `LICENSE` file has not been added yet.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Contact

Edson Mota Valença Filho - [@emvalencaf](https://github.com/emvalencaf)

Project Link: [https://github.com/emvalencaf/assayer](https://github.com/emvalencaf/assayer)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments

* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

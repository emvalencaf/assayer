# Assayer

A Python library for evaluating and observing LLM-powered applications. Provides a unified interface to run structured evaluations — chat turn quality, classification accuracy, and named entity extraction — using both deterministic metrics and model-based judges (LLM-as-Judge). Results and token costs are tracked via LangSmith.

## Features

- **Chat quality metrics** — BLEU, ROUGE-L, BERTScore, semantic similarity
- **Classification metrics** — accuracy, precision, recall, F1
- **NER evaluation** — entity-level F1 by type, macro F1
- **Hallucination detection** — reference-based (faithfulness scoring) and LLM-as-Judge
- **Mixed structured output** — evaluate a single chain that returns chat + classification + NER fields in one pipeline run
- **Token cost tracking** — input/output tokens and estimated USD cost per run, comparable across experiments
- **Extensible** — register custom metrics and evaluator types without modifying core files
- **Audit trail** — every evaluated field records method, expected value, obtained value, score, and prompt hash
- **LangSmith integration** — all results pushed automatically for experiment tracking and visualization

## Requirements

- Python 3.11.13+
- LangSmith account and API key (`LANGCHAIN_API_KEY` env var)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

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

## Core Abstractions

| Abstraction | Role |
|-------------|------|
| `Dataset` | Collection of input/expected-output pairs (LangSmith or local JSON) |
| `Evaluator` | Scores a single prediction against a reference |
| `Metric` | Aggregates scores across a full dataset |
| `Runner` | Orchestrates runs, applies evaluators/metrics, tracks tokens, pushes to LangSmith |

## Extending Assayer

**Custom metric:**
```python
from assayer.registry import MetricRegistry

def my_metric(predictions, references):
    ...

MetricRegistry.register("my_metric", my_metric)
```

**Custom evaluator:**
```python
from assayer.evaluators import BaseEvaluator
from assayer.registry import EvaluatorRegistry

class MyEvaluator(BaseEvaluator):
    def evaluate(self, prediction, reference):
        ...

EvaluatorRegistry.register("my_evaluator", MyEvaluator)
```

## Token Cost Tracking

Every `RunResult` exposes `input_tokens`, `output_tokens`, and `cost_usd`. Use `ExperimentResult.compare(other)` to get per-metric deltas and average token cost delta between two experiments.

## Running Tests

```bash
source .venv/bin/activate
pytest
pytest --cov=assayer   # coverage report (target: ≥ 90%)
```

## Non-Goals

- No model training or fine-tuning
- No built-in UI — visualization via LangSmith
- No LLM inference hosting
- No billing — cost tracking is observational only

## License

MIT

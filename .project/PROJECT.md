# Project: Assayer

## Vision
Assayer is a Python library for evaluating and observing LLM-powered applications. It provides a unified interface to run structured evaluations — chat turn quality, classification accuracy, and named entity extraction — using both deterministic metrics (accuracy, precision, recall, F1) and model-based judges (LLM-as-Judge). Results, including token cost comparisons, are tracked and visualized through LangSmith.

## Goals
- Enable developers to define and run reproducible LLM evaluation pipelines with minimal boilerplate.
- Support a range of evaluation tasks: chat quality, binary/multi-class classification, and named entity recognition (NER).
- Provide deterministic metrics (accuracy, precision, recall, F1) and LLM-as-Judge scoring in a composable API.
- Allow users to define and register custom metrics and custom evaluator types, extending the framework without modifying core code.
- Track and compare token usage costs (input tokens, output tokens, total cost) across experiments to support model selection and cost optimization.
- Integrate natively with LangSmith for experiment tracking, dataset management, and result visualization.
- Maintain a clean, SOLID-compliant Python codebase that is easy to extend with new evaluators and metrics.

## Non-Goals
- Assayer does not train or fine-tune models.
- Assayer does not provide a UI — visualization is delegated to LangSmith.
- Assayer is not a general-purpose data pipeline or ETL framework.
- Assayer does not manage LLM inference directly (no model hosting).
- Assayer does not bill or invoice users — token cost tracking is observational only.

## Stack
- **Language:** Python 3.11.13
- **Evaluation tracking:** LangSmith (`langsmith`)
- **Testing:** pytest
- **Typing:** built-in `typing` + `dataclasses` / `pydantic` as needed

## Architecture Overview
Assayer is organized around four core abstractions:

1. **Dataset** — a collection of input/expected-output pairs, loaded from LangSmith or local files.
2. **Evaluator** — a callable that receives a prediction and a reference and returns a scored result. New evaluator types can be registered by subclassing the base `Evaluator` interface.
3. **Metric** — a scoring function that takes predictions and references and returns a numeric score. Custom metrics can be registered alongside built-in ones (accuracy, precision, recall, F1).
4. **Runner** — orchestrates running a target LLM function over a dataset, applying evaluators and metrics, recording token usage (input/output), and pushing results to LangSmith.

Evaluators and metrics are composable: a pipeline can combine deterministic metrics with one or more LLM-as-Judge evaluators, and token cost data is attached to every experiment run.

## Key Constraints
- Python 3.11.13 minimum.
- All public APIs must carry type hints.
- All modules must have Google-style docstrings.
- No global mutable state — evaluators and runners must be instantiable as independent objects.
- Custom metrics and evaluators must be registerable without modifying library core files (Open/Closed Principle).

## Glossary
| Term | Definition |
|------|------------|
| Evaluator | A function or class that scores a single prediction against a reference |
| Metric | A scoring function that aggregates scores across a dataset (e.g. F1, accuracy) |
| LLM-as-Judge | Using a separate LLM call to score or classify a model output |
| Run | A single execution of a target function on one dataset example |
| Experiment | A named collection of runs tracked in LangSmith |
| NER | Named Entity Recognition — extracting labeled entities from text |
| F1 | Harmonic mean of precision and recall |
| Token cost | The monetary or unit cost of input and output tokens for a given LLM call |

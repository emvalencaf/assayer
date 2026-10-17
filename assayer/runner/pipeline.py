"""EvaluationPipeline implementation for running comprehensive evaluations.

This module contains the EvaluationPipeline class that orchestrates the entire
evaluation process from dataset loading to metric aggregation.
"""

from collections.abc import Callable
from typing import Any

from assayer.models import ExperimentResult, PricingConfig, RunResult
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry
from assayer.runner.dataset_loader import load_dataset
from assayer.runner.field_router import FieldRouter
from assayer.runner.token_extractor import extract_token_usage


class EvaluationPipeline:
    """Orchestrates the evaluation of a target function across a dataset.

    The EvaluationPipeline class manages the complete evaluation workflow:
    - Loading and validating datasets
    - Validating field evaluators and metrics against registries
    - Executing the target function on each example
    - Routing outputs to appropriate evaluators
    - Aggregating metrics across all runs
    - Returning comprehensive experiment results

    Args:
        target_fn: The function to evaluate. Should accept an input value and
            return a result object (potentially with usage_metadata).
        dataset: Either a list of example dictionaries or a path to a JSON file
            containing the dataset.
        field_evaluators: Mapping from field names to lists of evaluator names.
            All evaluator names must be registered in evaluator_registry.
        metrics: List of metric names to compute. All metric names must be
            registered in metric_registry.
        evaluator_registry: Registry containing evaluator classes.
        metric_registry: Registry containing metric functions.
        pricing_config: Optional pricing configuration for cost calculation.
        experiment_name: Human-readable name for the experiment. Defaults to
            "unnamed_experiment".

    Raises:
        KeyError: If any evaluator name or metric name is not registered in
            their respective registries. This validation occurs before execution.
    """

    def __init__(
        self,
        target_fn: Callable[[Any], Any],
        dataset: list[dict] | str,
        field_evaluators: dict[str, list[str]],
        metrics: list[str],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
        pricing_config: PricingConfig | None = None,
        experiment_name: str = "unnamed_experiment",
    ) -> None:
        """Initialize the EvaluationPipeline with all required components.

        Validates metric names against the MetricRegistry before storing parameters.
        FieldRouter construction will validate evaluator names.

        Args:
            target_fn: Function to evaluate.
            dataset: Dataset source (list or file path).
            field_evaluators: Field to evaluator name mappings.
            metrics: List of metric names to compute.
            evaluator_registry: Registry for evaluator classes.
            metric_registry: Registry for metric functions.
            pricing_config: Optional pricing configuration.
            experiment_name: Name for this experiment.

        Raises:
            KeyError: If any metric name is not registered in metric_registry,
                or if any evaluator name is not registered (via FieldRouter).
        """
        # Validate metric names before storing anything
        for metric_name in metrics:
            if metric_name not in metric_registry.list_metrics():
                raise KeyError(f"Metric '{metric_name}' is not registered")

        # Store all parameters
        self.target_fn = target_fn
        self.dataset = dataset
        self.field_evaluators = field_evaluators
        self.metrics = metrics
        self.evaluator_registry = evaluator_registry
        self.metric_registry = metric_registry
        self.pricing_config = pricing_config
        self.experiment_name = experiment_name

        # Validate evaluator names and create FieldRouter (this will raise KeyError if invalid)
        self._field_router = FieldRouter(field_evaluators, evaluator_registry)

    def run(self) -> ExperimentResult:
        """Execute the evaluation pipeline and return aggregated results.

        Loads the dataset, executes the target function on each example,
        routes outputs to evaluators, extracts token usage, and computes
        aggregate metrics across all runs.

        Returns:
            An ExperimentResult containing all run results and computed metrics.

        Raises:
            ValueError: If target function raises an exception, the error is
                propagated with context about which example caused the failure.
            FileNotFoundError: If dataset is a file path that doesn't exist.
            json.JSONDecodeError: If dataset file contains invalid JSON.
        """
        # Load and validate the dataset
        dataset = load_dataset(self.dataset)

        # Execute target function on each example and collect results
        runs: list[RunResult] = []
        all_predictions: list[Any] = []
        all_references: list[Any] = []

        for i, example in enumerate(dataset):
            try:
                # Call target function
                result = self.target_fn(example["input"])

                # Extract token usage
                token_usage = extract_token_usage(result, self.pricing_config)

                # Route output to evaluators
                evaluations = self._field_router.route(result, example["expected_output"])

                # Create run result
                run_result = RunResult(
                    input=example["input"],
                    output=result,
                    token_usage=token_usage,
                    evaluations=evaluations,
                )
                runs.append(run_result)

                # Collect predictions and references for metric computation
                all_predictions.append(result)
                all_references.append(example["expected_output"])

            except Exception as e:
                # Propagate exception with example context
                raise type(e)(f"Error processing example {i}: {e!s}") from e

        # Compute aggregate metrics
        computed_metrics: dict[str, float] = {}
        for metric_name in self.metrics:
            metric_fn = self.metric_registry.get(metric_name)
            computed_metrics[metric_name] = metric_fn(all_predictions, all_references)

        # Return experiment result
        return ExperimentResult(
            experiment_name=self.experiment_name, runs=runs, metrics=computed_metrics
        )

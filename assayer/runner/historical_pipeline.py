"""HistoricalPipeline implementation for evaluating pre-collected datasets.

This module contains the HistoricalPipeline class that orchestrates evaluation
of already-collected (historical) data without requiring a live target function.
"""

from typing import Union

from assayer.runner.field_router import FieldRouter
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry


class HistoricalPipeline:
    """Orchestrates the evaluation of a historical dataset without a target function.

    The HistoricalPipeline class manages the evaluation workflow for pre-collected
    data. Unlike EvaluationPipeline, it does not require a live target function;
    instead, it operates on an existing dataset that already contains predictions.

    Validation is performed at construction time (fail-fast):
    - All metric names are checked against the MetricRegistry.
    - All evaluator names are validated via FieldRouter construction.

    Args:
        dataset: Either a list of example dictionaries or a path to a JSON file
            containing the dataset.
        field_evaluators: Mapping from field names to lists of evaluator names.
            All evaluator names must be registered in evaluator_registry.
        metrics: List of metric names to compute. All metric names must be
            registered in metric_registry.
        evaluator_registry: Registry containing evaluator classes.
        metric_registry: Registry containing metric functions.
        experiment_name: Human-readable name for the experiment. Defaults to
            "unnamed_experiment".

    Raises:
        KeyError: If any metric name is not registered in metric_registry, or if
            any evaluator name is not registered in evaluator_registry. This
            validation occurs at construction time before any data is processed.
    """

    def __init__(
        self,
        dataset: Union[list[dict], str],
        field_evaluators: dict[str, list[str]],
        metrics: list[str],
        evaluator_registry: EvaluatorRegistry,
        metric_registry: MetricRegistry,
        experiment_name: str = "unnamed_experiment",
    ) -> None:
        """Initialize the HistoricalPipeline with all required components.

        Validates metric names against the MetricRegistry before storing parameters.
        FieldRouter construction will validate evaluator names.

        Args:
            dataset: Dataset source — a list of example dicts or a file path to a
                JSON file. When a string path is provided, loading is deferred to
                run() time.
            field_evaluators: Field to evaluator name mappings.
            metrics: List of metric names to compute.
            evaluator_registry: Registry for evaluator classes.
            metric_registry: Registry for metric functions.
            experiment_name: Name for this experiment. Defaults to
                "unnamed_experiment".

        Raises:
            KeyError: If any metric name is not registered in metric_registry, or
                if any evaluator name is not registered in evaluator_registry (via
                FieldRouter).
        """
        # Validate metric names before storing anything
        for metric_name in metrics:
            if metric_name not in metric_registry.list_metrics():
                raise KeyError(f"Metric '{metric_name}' is not registered")

        # Store all parameters
        self.dataset = dataset
        self.field_evaluators = field_evaluators
        self.metrics = metrics
        self.evaluator_registry = evaluator_registry
        self.metric_registry = metric_registry
        self.experiment_name = experiment_name

        # Validate evaluator names and create FieldRouter (raises KeyError if invalid)
        self._field_router = FieldRouter(field_evaluators, evaluator_registry)

    def run(self) -> None:
        """Execute the historical evaluation pipeline.

        Raises:
            NotImplementedError: This method is not yet implemented.
        """
        raise NotImplementedError

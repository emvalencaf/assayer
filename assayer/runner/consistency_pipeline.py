"""ConsistencyPipeline for evaluating LLM consistency across multiple runs."""

from typing import Any, Callable

from assayer.evaluators.consistency import ConsistencyEvaluator
from assayer.registries.evaluator_registry import EvaluatorRegistry


class ConsistencyPipeline:
    """Pipeline that evaluates LLM output consistency by running k evaluations per input.

    ConsistencyPipeline wraps one or more field evaluators in ConsistencyEvaluator
    instances, enabling consistency measurement over repeated calls to a target
    function. Each field in ``field_evaluators`` gets its own ConsistencyEvaluator
    backed by the named evaluator class from the registry.

    Args:
        target_fn: Callable that takes an input and returns a prediction.
        dataset: A list of dicts or a path string to a JSONL/JSON dataset.
        field_evaluators: Mapping from field name to registered evaluator name.
            One ConsistencyEvaluator is created per entry.
        evaluator_registry: Registry used to look up evaluator classes by name.
        k: Number of evaluations (calls to target_fn) to perform per input.
        min_k: Minimum number of evaluations required in historical mode.
            Passed through to each ConsistencyEvaluator.
        experiment_name: Human-readable label for the experiment run.

    Raises:
        KeyError: If any evaluator name in ``field_evaluators`` is not registered
            in ``evaluator_registry``.
    """

    def __init__(
        self,
        target_fn: Callable[[Any], Any],
        dataset: list[dict] | str,
        field_evaluators: dict[str, str],
        evaluator_registry: EvaluatorRegistry,
        k: int = 5,
        min_k: int | None = None,
        experiment_name: str = "unnamed_experiment",
    ) -> None:
        """Initialize the ConsistencyPipeline with fail-fast evaluator validation.

        Args:
            target_fn: Callable that takes an input and returns a prediction.
            dataset: A list of dicts or a path string to a JSONL/JSON dataset.
            field_evaluators: Mapping from field name to registered evaluator name.
                One ConsistencyEvaluator is created per entry.
            evaluator_registry: Registry used to look up evaluator classes by name.
            k: Number of evaluations (calls to target_fn) to perform per input.
            min_k: Minimum number of evaluations required in historical mode.
                Passed through to each ConsistencyEvaluator.
            experiment_name: Human-readable label for the experiment run.

        Raises:
            KeyError: If any evaluator name in ``field_evaluators`` is not registered
                in ``evaluator_registry``.
        """
        self.target_fn = target_fn
        self.dataset = dataset
        self.field_evaluators = field_evaluators
        self.evaluator_registry = evaluator_registry
        self.k = k
        self.min_k = min_k
        self.experiment_name = experiment_name

        self._consistency_evaluators: dict[str, ConsistencyEvaluator] = {}
        for field_name, evaluator_name in field_evaluators.items():
            evaluator_cls = evaluator_registry.get(evaluator_name)
            base_evaluator = evaluator_cls(evaluator_name, field_name=field_name)
            self._consistency_evaluators[field_name] = ConsistencyEvaluator(
                evaluator=base_evaluator,
                k=k,
                min_k=min_k,
            )

    def run(self) -> None:
        """Run the consistency pipeline.

        Raises:
            NotImplementedError: Always — implemented in a future task.
        """
        raise NotImplementedError

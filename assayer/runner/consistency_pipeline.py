"""ConsistencyPipeline for evaluating LLM consistency across multiple runs."""

import statistics
from typing import Any, Callable

from assayer.evaluators.consistency import ConsistencyEvaluator
from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation
from assayer.models.consistency_report import ConsistencyReport
from assayer.models.consistency_run_result import ConsistencyRunResult
from assayer.models.consistency_summary import ConsistencySummary
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.runner.dataset_loader import load_dataset


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

    def run(self) -> ConsistencyReport:
        """Run the consistency pipeline and return aggregated consistency results.

        Loads the dataset, runs each consistency evaluator in live mode for
        every record, and aggregates results into a ConsistencyReport with
        per-field summaries and per-run detailed evaluations.

        Returns:
            ConsistencyReport containing experiment metadata, per-field
            ConsistencySummary aggregations, and a list of ConsistencyRunResult
            instances (one per dataset record).

        Raises:
            Any exception raised by the underlying evaluators or target_fn
            will propagate without being caught.
        """
        records = load_dataset(self.dataset)

        runs: list[ConsistencyRunResult] = []
        field_evals: dict[str, list[ConsistencyFieldEvaluation]] = {
            field: [] for field in self._consistency_evaluators
        }

        for record in records:
            per_field_evaluations: dict[str, ConsistencyFieldEvaluation] = {}
            for field_name, evaluator in self._consistency_evaluators.items():
                eval_result = evaluator.evaluate_live(
                    self.target_fn, record["input"], record["expected_output"]
                )
                per_field_evaluations[field_name] = eval_result
                field_evals[field_name].append(eval_result)
            runs.append(
                ConsistencyRunResult(
                    input=record["input"],
                    per_field_evaluations=per_field_evaluations,
                )
            )

        per_field: dict[str, ConsistencySummary] = {}
        for field, evals in field_evals.items():
            if not evals:
                per_field[field] = ConsistencySummary(
                    per_group=[],
                    worst_groups=[],
                    mean_agreement_rate=0.0,
                    mean_entropy=0.0,
                    mean_score_std=0.0,
                    mean_correct_rate=0.0,
                    mean_recall_at_k=0.0,
                    pass_at_k_rate=0.0,
                )
            else:
                mean_agreement_rate = statistics.mean(e.agreement_rate for e in evals)
                mean_entropy = statistics.mean(e.entropy for e in evals)
                mean_score_std = statistics.mean(e.score_std for e in evals)
                mean_correct_rate = statistics.mean(e.correct_rate for e in evals)
                mean_recall_at_k = statistics.mean(e.recall_at_k for e in evals)
                pass_at_k_rate = sum(1 for e in evals if e.pass_at_k) / len(evals)
                worst_groups = sorted(evals, key=lambda x: x.agreement_rate)[:10]
                per_field[field] = ConsistencySummary(
                    per_group=evals,
                    worst_groups=worst_groups,
                    mean_agreement_rate=mean_agreement_rate,
                    mean_entropy=mean_entropy,
                    mean_score_std=mean_score_std,
                    mean_correct_rate=mean_correct_rate,
                    mean_recall_at_k=mean_recall_at_k,
                    pass_at_k_rate=pass_at_k_rate,
                )

        return ConsistencyReport(
            experiment_name=self.experiment_name,
            k=self.k,
            per_field=per_field,
            runs=runs,
        )

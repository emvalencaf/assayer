"""Runs a target over a Dataset and returns an Experiment."""

import copy
import dataclasses
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Any

from assayer.metrics import Metric
from assayer.models import Case, Dataset, Experiment, PricingConfig, Step, Trajectory
from assayer.runner.case_loader import load_cases
from assayer.runner.field_map import (
    FieldMetric,
    build_field_map,
    metrics_of,
    score_experiment_field,
    score_field,
)


class Runner:
    """Runs a target over the Cases of a Dataset and scores the result.

    Args:
        target: Called with `Case.input`. Returns a Trajectory, or a plain value
            that is wrapped in one model Step. An exception it raises is kept as
            the `error` of a model Step instead of aborting the Experiment. Only
            `run` needs it; `score` works on outputs collected beforehand.
        metrics: The metrics to apply, at their own level, to the whole output.
        field_metrics: Maps the dotted path of an output Field to the trajectory- or
            Experiment-level metrics that score it on its own (an Experiment-level one,
            such as a corpus metric, sees that Field of every Trajectory and Case, and runs
            after the whole-output metrics and the entries listed before it), each a Metric
            or a `(Metric, params)` pair whose params are passed to the metric's function
            for that Field only; or a `ListField` that aligns a list of objects and scores the pairs
            property by property. The metric sees the Field's value as `final_output` and the
            Case's as `expected_output`; its Scores carry the `field`.
        repetitions: How many times each Case is run; each repetition is kept as
            its own Trajectory.
        pricing: Prices of the target's model, kept on the Experiment so its cost
            can be compared. Not applied to the Judge.

    Raises:
        ValueError: If repetitions is less than 1, or a field path or metric in
            `field_metrics` is invalid. Checked on construction, before any
            target call.
        TypeError: If `field_metrics` is not a map of metrics.
    """

    def __init__(
        self,
        target: Callable[[Any], Any] | None = None,
        metrics: Iterable[Metric] = (),
        repetitions: int = 1,
        pricing: PricingConfig | None = None,
        field_metrics: Mapping[str, Sequence[Any]] | None = None,
    ) -> None:
        if repetitions < 1:
            raise ValueError("repetitions must be at least 1")
        self.target = target
        self.metrics = list(metrics)
        self.repetitions = repetitions
        self.pricing = pricing
        self._field_pairs = build_field_map(field_metrics)

    def run(self, dataset: Dataset | list[dict] | str) -> Experiment:
        """Run the target over every Case and apply the metrics.

        Args:
            dataset: A Dataset, a list of dictionaries or the path to a JSON file.
                The last two are validated against what the metrics require.

        Returns:
            The Experiment, with the Trajectories, Scores and evaluation failures.

        Raises:
            ValueError: If there is no target, or a loaded entry lacks `input` or a
                field a metric requires.
        """
        if self.target is None:
            raise ValueError("run needs a target; use score for collected outputs")
        if not isinstance(dataset, Dataset):
            dataset = load_cases(dataset, self._all_metrics())

        experiment = Experiment(name=dataset.name, pricing=self.pricing)
        pairs: list[tuple[Trajectory, Case]] = []
        for position, case in enumerate(dataset.cases):
            case_id = case.id if case.id is not None else str(position)
            experiment.cases.append(dataclasses.replace(case, id=case_id))
            for repetition in range(self.repetitions):
                trajectory = self._execute(case, case_id, repetition)
                experiment.trajectories.append(trajectory)
                pairs.append((trajectory, case))

        self._apply_all(experiment, pairs)
        return experiment

    def score(self, dataset: Dataset | list[dict] | str, outputs: Sequence[Any]) -> Experiment:
        """Score outputs collected beforehand, without calling the target.

        Args:
            dataset: A Dataset, a list of dictionaries or the path to a JSON file.
            outputs: One per Case, in order: a Trajectory, or a plain value that is
                wrapped in one model Step. Each becomes the Case's only repetition.

        Returns:
            The Experiment, with the Trajectories, Scores and evaluation failures.

        Raises:
            ValueError: If outputs does not have one entry per Case, or a loaded
                entry lacks `input` or a field a metric requires.
        """
        if not isinstance(dataset, Dataset):
            dataset = load_cases(dataset, self._all_metrics())
        if len(outputs) != len(dataset.cases):
            raise ValueError(
                f"outputs must have one entry per Case: {len(outputs)} outputs "
                f"for {len(dataset.cases)} Cases"
            )

        experiment = Experiment(name=dataset.name, pricing=self.pricing)
        pairs: list[tuple[Trajectory, Case]] = []
        for position, (case, output) in enumerate(zip(dataset.cases, outputs, strict=True)):
            case_id = case.id if case.id is not None else str(position)
            experiment.cases.append(dataclasses.replace(case, id=case_id))
            trajectory = self._tag(output, case, case_id, 0)
            experiment.trajectories.append(trajectory)
            pairs.append((trajectory, case))

        self._apply_all(experiment, pairs)
        return experiment

    def _all_metrics(self) -> list[Metric]:
        return [*self.metrics, *metrics_of(self._field_pairs)]

    def _apply_all(self, experiment: Experiment, pairs: list[tuple[Trajectory, Case]]) -> None:
        for metric in self.metrics:
            self._apply(metric, experiment, pairs)
        for entry in self._field_pairs:
            if isinstance(entry, FieldMetric) and entry.metric.level == "experiment":
                outcomes = [score_experiment_field(entry, experiment)]
            else:
                outcomes = [score_field(entry, t, c) for t, c in pairs]
            for outcome in outcomes:
                experiment.scores.extend(outcome.scores)
                experiment.failures.extend(outcome.failures)

    def _execute(self, case: Case, case_id: str, repetition: int) -> Trajectory:
        assert self.target is not None  # run checks it
        try:
            result = self.target(case.input)
        except Exception as exc:
            result = Trajectory(
                steps=[Step(kind="model", input=case.input, error=f"{type(exc).__name__}: {exc}")]
            )
        return self._tag(result, case, case_id, repetition)

    def _tag(self, result: Any, case: Case, case_id: str, repetition: int) -> Trajectory:
        if not isinstance(result, Trajectory):
            result = Trajectory(
                steps=[Step(kind="model", input=case.input, output=result)],
                final_output=result,
            )
        result = copy.deepcopy(result)  # a target may hand back the same object each call
        result.case_id = case_id
        result.repetition = repetition
        for index, step in enumerate(result.steps):
            if step.id is None:
                step.id = f"{case_id}/{repetition}/{index}"
        return result

    def _apply(
        self, metric: Metric, experiment: Experiment, pairs: list[tuple[Trajectory, Case]]
    ) -> None:
        if metric.level == "experiment":
            subjects = [(experiment, None)]
        elif metric.level == "trajectory":
            subjects = pairs
        else:  # "step", the only level left (Metric validates it)
            subjects = [(step, case) for trajectory, case in pairs for step in trajectory.steps]
        for subject, case in subjects:
            outcome = metric.evaluate(subject, case)
            experiment.scores.extend(outcome.scores)
            experiment.failures.extend(outcome.failures)

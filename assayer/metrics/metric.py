"""The public metric contract.

A `Metric` declares what it scores (`level`), what it needs (`requires`) and
whether it needs a Judge (`kind`). Built-in and custom metrics share this one
shape, so they run, skip and fail the same way.
"""

from collections.abc import Callable
from dataclasses import dataclass, field, fields
from typing import Any, Literal, get_args

from assayer.models import Case, EvaluationFailure, Score, Step, Trajectory

MetricLevel = Literal["step", "trajectory", "experiment"]
METRIC_LEVELS = get_args(MetricLevel)
MetricKind = Literal["deterministic", "judge"]
METRIC_KINDS = get_args(MetricKind)

_REQUIRABLE = {f.name for cls in (Case, Trajectory, Step) for f in fields(cls)}


@dataclass
class MetricOutcome:
    """What applying a metric once produced.

    Args:
        scores: The Scores computed; empty when the metric could not be computed.
        failures: Evaluation failures; empty when a Score was computed.
    """

    scores: list[Score] = field(default_factory=list)
    failures: list[EvaluationFailure] = field(default_factory=list)


@dataclass
class Metric:
    """A named way of scoring a Step, a Trajectory or an Experiment.

    Args:
        name: Name of the metric; becomes the name of its Scores.
        level: What the metric scores: "step", "trajectory" or "experiment".
        fn: Called as `fn(subject, case)`, where subject is a Step, Trajectory or
            Experiment according to `level`. Returns a number in [0, 1] or a
            boolean. A missing answer is scored 0 by the metric itself; an
            input the metric cannot work without is declared in `requires`.
        requires: Names of the Case fields (such as "expected_output") and of
            the subject fields (such as "final_state") the metric needs. An
            input that is None makes the metric emit no Score and an
            evaluation failure instead.
        kind: "deterministic", or "judge" when a Judge scores the output.

    Raises:
        ValueError: If name is blank, level or kind is unknown, or requires
            names a field of no Case, Trajectory or Step.
        TypeError: If fn is not callable.
    """

    name: str
    level: MetricLevel
    fn: Callable[[Any, Case | None], float | bool]
    requires: tuple[str, ...] = ()
    kind: MetricKind = "deterministic"

    def __post_init__(self) -> None:
        """Validate the declaration.

        Raises:
            ValueError: If name is blank, level or kind is unknown, or requires
                names an unknown field.
            TypeError: If fn is not callable.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Metric name cannot be empty or contain only whitespace")
        if self.level not in METRIC_LEVELS:
            raise ValueError(f"level must be one of {METRIC_LEVELS}")
        if self.kind not in METRIC_KINDS:
            raise ValueError(f"kind must be one of {METRIC_KINDS}")
        if not callable(self.fn):
            raise TypeError("Metric function must be callable")
        unknown = set(self.requires) - _REQUIRABLE
        if unknown:
            raise ValueError(f"requires names unknown fields: {sorted(unknown)}")

    def evaluate(self, subject: Any, case: Case | None = None) -> MetricOutcome:
        """Apply the metric once.

        Args:
            subject: The Step, Trajectory or Experiment, according to `level`.
            case: The Case the subject was produced for, if any.

        Returns:
            One Score, or one evaluation failure when a required input is
            missing or the metric raised. Never raises and never scores a
            missing input as 0.
        """
        target_id = None
        try:
            target_id = self._target_id(subject)
            missing = [name for name in self.requires if _lookup(name, case, subject) is None]
            if missing:
                error = f"missing required input: {', '.join(missing)}"
                return MetricOutcome(failures=[EvaluationFailure(self.name, error, target_id)])
            value = self.fn(subject, case)
            score = Score(name=self.name, value=value, target=self.level, target_id=target_id)
        except Exception as exc:
            return MetricOutcome(failures=[EvaluationFailure(self.name, str(exc), target_id)])
        return MetricOutcome(scores=[score])

    def _target_id(self, subject: Any) -> str | None:
        if self.level == "step":
            return subject.id
        if self.level == "trajectory":
            return subject.case_id
        return None


def _lookup(name: str, case: Case | None, subject: Any) -> Any:
    """Find a required input on the Case, then on the subject."""
    for source in (case, subject):
        value = getattr(source, name, None)
        if value is not None:
            return value
    return None

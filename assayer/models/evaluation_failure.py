from dataclasses import dataclass


@dataclass
class EvaluationFailure:
    """A metric that could not be computed, kept as data instead of raised.

    Args:
        metric: Name of the metric that failed.
        error: Error message.
        target_id: Id of the Step or Trajectory being scored, if any.
        field: Dotted path of the output Field being scored, if any.
    """

    metric: str
    error: str
    target_id: str | None = None
    field: str | None = None

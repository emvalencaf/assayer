"""A metric applied to one Field of the output."""

from dataclasses import dataclass, field
from typing import Any

from assayer.metrics import Metric


@dataclass(frozen=True)
class FieldMetric:
    """One metric applied to one Field, with the parameters of that pair.

    Args:
        path: Dotted path of the Field, such as "address.city".
        metric: The metric that scores it.
        params: Keyword parameters passed to the metric's function.
    """

    path: str
    metric: Metric
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def similarity_name(self) -> str:
        """Name of the Score that stands for this entry when items are compared."""
        return self.metric.name

    def metrics(self) -> list[Metric]:
        """The metrics this entry applies."""
        return [self.metric]

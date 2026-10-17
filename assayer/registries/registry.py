"""Registry of metrics on the public metric contract.

Built-in and custom metrics are registered the same way and looked up by name.
"""

# Inner-module import: `assayer.metrics` imports the legacy registries, so going
# through its `__init__` would be circular.
from assayer.metrics.metric import Metric


class Registry:
    """Registry for storing and retrieving `Metric` objects.

    Each instance keeps its own metrics; there is no shared state.

    Example:
        >>> registry = Registry()
        >>> registry.register(Metric(name="m", level="trajectory", fn=lambda t, c: 1.0))
        >>> registry.list_metrics()
        ['m']
    """

    def __init__(self) -> None:
        """Initialize an empty Registry."""
        self._metrics: dict[str, Metric] = {}

    def register(self, metric: Metric) -> None:
        """Register a metric under its own name.

        Args:
            metric: The metric to register.

        Raises:
            TypeError: If metric is not a Metric.
            KeyError: If a metric with that name is already registered.
        """
        if not isinstance(metric, Metric):
            raise TypeError("register() takes a Metric")
        if metric.name in self._metrics:
            raise KeyError(f"Metric '{metric.name}' is already registered")
        self._metrics[metric.name] = metric

    def get(self, name: str) -> Metric:
        """Retrieve a registered metric by name.

        Args:
            name: The name of the metric.

        Returns:
            The registered metric.

        Raises:
            KeyError: If no metric is registered under the name.
        """
        if name not in self._metrics:
            raise KeyError(f"Metric '{name}' is not registered")
        return self._metrics[name]

    def list_metrics(self) -> list[str]:
        """List the registered metric names in sorted order.

        Returns:
            The sorted names; empty if none is registered.
        """
        return sorted(self._metrics)

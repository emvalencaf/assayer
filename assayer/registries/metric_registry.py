"""MetricRegistry for storing and retrieving metric functions.

This module provides the MetricRegistry class for managing metric functions
in an isolated, instance-based registry system.
"""

from typing import Any, Callable


class MetricRegistry:
    """Registry for storing and retrieving metric functions.

    Each MetricRegistry instance maintains its own isolated registry of metric
    functions. This allows for independent metric collections without shared
    global state.

    Example:
        >>> registry = MetricRegistry()
        >>> def accuracy(predictions, references):
        ...     return sum(p == r for p, r in zip(predictions, references)) / len(predictions)
        >>> registry.register("accuracy", accuracy)
        >>> metric_fn = registry.get("accuracy")
        >>> registry.list_metrics()
        ['accuracy']
    """

    def __init__(self) -> None:
        """Initialize a new MetricRegistry with an empty registry.

        Each instance maintains its own independent registry state.
        """
        self._registry: dict[str, Callable[[list[Any], list[Any]], float]] = {}

    def register(self, name: str, fn: Callable[[list[Any], list[Any]], float]) -> None:
        """Register a metric function with the given name.

        Args:
            name: The name to register the metric under. Must be non-empty
                and contain non-whitespace characters.
            fn: The metric function to register. Must be callable and accept
                two list parameters (predictions and references) returning a float.

        Raises:
            ValueError: If name is empty or contains only whitespace.
            TypeError: If fn is not callable.
            KeyError: If name is already registered in this registry.
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Metric name cannot be empty or contain only whitespace")

        # Validate function is callable
        if not callable(fn):
            raise TypeError("Metric function must be callable")

        # Check for duplicate registration
        if name in self._registry:
            raise KeyError(f"Metric '{name}' is already registered")

        self._registry[name] = fn

    def get(self, name: str) -> Callable[[list[Any], list[Any]], float]:
        """Retrieve a registered metric function by name.

        Args:
            name: The name of the metric to retrieve.

        Returns:
            The metric function registered under the given name.

        Raises:
            KeyError: If no metric is registered under the given name.
        """
        if name not in self._registry:
            raise KeyError(f"Metric '{name}' is not registered")

        return self._registry[name]

    def list_metrics(self) -> list[str]:
        """List all registered metric names in sorted order.

        Returns:
            A sorted list of all registered metric names. Returns an empty
            list if no metrics are registered.
        """
        return sorted(self._registry.keys())
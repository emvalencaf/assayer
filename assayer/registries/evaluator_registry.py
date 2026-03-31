"""EvaluatorRegistry for storing and retrieving evaluator classes.

This module provides the EvaluatorRegistry class for managing evaluator classes
in an isolated, instance-based registry system.
"""

from assayer.evaluators.base import BaseEvaluator


class EvaluatorRegistry:
    """Registry for storing and retrieving evaluator classes.

    Each EvaluatorRegistry instance maintains its own isolated registry of
    evaluator classes. This allows for independent evaluator collections
    without shared global state.

    Example:
        >>> registry = EvaluatorRegistry()
        >>> class MyEvaluator(BaseEvaluator):
        ...     def evaluate(self, prediction, reference, **kwargs):
        ...         return FieldEvaluation(...)
        >>> registry.register("my_evaluator", MyEvaluator)
        >>> evaluator_cls = registry.get("my_evaluator")
        >>> registry.list_evaluators()
        ['my_evaluator']
    """

    def __init__(self) -> None:
        """Initialize a new EvaluatorRegistry with an empty registry.

        Each instance maintains its own independent registry state.
        """
        self._registry: dict[str, type[BaseEvaluator]] = {}

    def register(self, name: str, cls: type[BaseEvaluator]) -> None:
        """Register an evaluator class with the given name.

        Args:
            name: The name to register the evaluator class under. Must be
                non-empty and contain non-whitespace characters.
            cls: The evaluator class to register. Must be a concrete subclass
                of BaseEvaluator (not BaseEvaluator itself).

        Raises:
            ValueError: If name is empty or contains only whitespace.
            TypeError: If cls is not a subclass of BaseEvaluator, or is
                BaseEvaluator itself (abstract class cannot be instantiated).
            KeyError: If name is already registered in this registry.
        """
        # Validate name
        if not name or not name.strip():
            raise ValueError("Evaluator name cannot be empty or contain only whitespace")

        # Validate class is a BaseEvaluator subclass but not BaseEvaluator itself
        if cls is None:
            raise TypeError("Evaluator class cannot be None")

        # Check if cls is a proper subclass of BaseEvaluator (not BaseEvaluator itself)
        if not isinstance(cls, type) or not issubclass(cls, BaseEvaluator):
            raise TypeError("Evaluator class must be a subclass of BaseEvaluator")

        if cls is BaseEvaluator:
            raise TypeError("Cannot register BaseEvaluator itself - it is abstract")

        # Check for duplicate registration
        if name in self._registry:
            raise KeyError(f"Evaluator '{name}' is already registered")

        self._registry[name] = cls

    def get(self, name: str) -> type[BaseEvaluator]:
        """Retrieve a registered evaluator class by name.

        Args:
            name: The name of the evaluator class to retrieve.

        Returns:
            The evaluator class registered under the given name.

        Raises:
            KeyError: If no evaluator class is registered under the given name.
        """
        if name not in self._registry:
            raise KeyError(f"Evaluator '{name}' is not registered")

        return self._registry[name]

    def list_evaluators(self) -> list[str]:
        """List all registered evaluator names in sorted order.

        Returns:
            A sorted list of all registered evaluator names. Returns an empty
            list if no evaluators are registered.
        """
        return sorted(self._registry.keys())
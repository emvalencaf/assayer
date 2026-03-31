"""Abstract base class for all evaluators.

This module defines BaseEvaluator, the abstract base class that all evaluator
implementations must inherit from to be compatible with the assayer framework.
"""

from abc import ABC, abstractmethod
from typing import Any

from assayer.models import FieldEvaluation


class BaseEvaluator(ABC):
    """Abstract base class for all evaluators.

    All evaluators in the assayer framework must inherit from this class and
    implement the abstract evaluate method. This ensures a consistent interface
    for evaluation operations and allows for type-safe registration in the
    evaluator registry.

    Args:
        name: A non-empty string identifier for this evaluator. Leading and
            trailing whitespace is automatically stripped.

    Raises:
        ValueError: If name is empty or whitespace-only after stripping.
    """

    def __init__(self, name: str) -> None:
        """Initialize the evaluator with a name.

        Args:
            name: A non-empty string identifier for this evaluator.

        Raises:
            ValueError: If name is empty or whitespace-only after stripping.
        """
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("name must not be empty")
        self._name = stripped_name

    @property
    def name(self) -> str:
        """Get the evaluator name.

        Returns:
            The evaluator's name as provided during initialization.
        """
        return self._name

    @abstractmethod
    def evaluate(
        self,
        prediction: Any,
        reference: Any,
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Evaluate a prediction against a reference value.

        This method must be implemented by all concrete evaluator subclasses.
        It compares a predicted value against a reference (ground truth) value
        and returns a FieldEvaluation containing the comparison results.

        Args:
            prediction: The predicted/obtained value to evaluate.
            reference: The reference/expected value for comparison.
            **kwargs: Additional keyword arguments that specific evaluator
                implementations may require (e.g., thresholds, prompts).

        Returns:
            A FieldEvaluation object containing the evaluation results,
            including the score, input values, and evaluation metadata.
        """
        pass
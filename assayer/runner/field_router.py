"""FieldRouter implementation for routing outputs to evaluators.

This module contains the FieldRouter class that maps output field names to
lists of evaluator instances and handles the routing of prediction/reference
pairs to appropriate evaluators.
"""

from typing import Any

from assayer.models import FieldEvaluation
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.evaluators.base import BaseEvaluator


class FieldRouter:
    """Maps output field names to lists of instantiated BaseEvaluator objects.

    The FieldRouter class is responsible for:
    - Validating evaluator names against the registry at construction time
    - Instantiating evaluators with appropriate field names
    - Routing prediction/reference pairs to the correct evaluators
    - Handling both scalar and dict-structured outputs

    Args:
        field_evaluators: A mapping from field names to lists of evaluator names.
            Each evaluator name must be registered in the evaluator registry.
        evaluator_registry: The registry instance used to look up evaluator classes.

    Raises:
        KeyError: If any evaluator name in field_evaluators is not registered
            in the evaluator_registry.
    """

    def __init__(
        self,
        field_evaluators: dict[str, list[str]],
        evaluator_registry: EvaluatorRegistry,
    ) -> None:
        """Initialize FieldRouter with field-to-evaluator mappings.

        Eagerly validates all evaluator names at construction time to fail fast
        if any evaluator names are not registered.

        Args:
            field_evaluators: Mapping from field names to evaluator name lists.
            evaluator_registry: Registry to look up evaluator classes.

        Raises:
            KeyError: If any evaluator name is not found in the registry.
        """
        # Eagerly validate all evaluator names at construction time
        self._routes: dict[str, list[BaseEvaluator]] = {}
        for field, names in field_evaluators.items():
            self._routes[field] = [evaluator_registry.get(n)(n, field_name=field) for n in names]

    def route(
        self,
        output: Any,
        expected_output: Any,
    ) -> list[FieldEvaluation]:
        """Run all evaluators for each declared output field.

        For each field configured in field_evaluators, extracts the corresponding
        values from output and expected_output, then runs all evaluators for that
        field. Handles both scalar and dict-structured inputs appropriately.

        Args:
            output: The target function's return value (structured or scalar).
            expected_output: The reference value from the dataset example.

        Returns:
            A flat list of FieldEvaluation records, one per (field, evaluator) pair.

        Raises:
            KeyError: If a configured field is missing from dict-structured input.
        """
        results: list[FieldEvaluation] = []
        for field, evaluators in self._routes.items():
            pred = output[field] if isinstance(output, dict) else output
            ref = expected_output[field] if isinstance(expected_output, dict) else expected_output
            for evaluator in evaluators:
                results.append(evaluator.evaluate(pred, ref))
        return results
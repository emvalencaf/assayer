"""Consistency evaluator for measuring response consistency."""

from assayer.evaluators.base import BaseEvaluator


class ConsistencyEvaluator:
    """Evaluator that measures consistency by running evaluations multiple times.

    ConsistencyEvaluator wraps any BaseEvaluator and runs it multiple times
    on the same input to measure consistency of responses. It can operate in
    two modes:

    - Historical mode: analyze pre-computed predictions from a dataset
    - Live mode: make multiple calls to a target function and evaluate consistency

    Args:
        evaluator: The base evaluator to wrap for consistency measurement.
        k: Number of evaluations to perform per input (default: 5).
        min_k: Minimum number of evaluations required to include a group
            in historical mode analysis. Only applies to evaluate_dataset.
            If None, no filtering is applied (default: None).

    Raises:
        ValueError: If k < 1 or if min_k is provided and min_k < 1.
    """

    def __init__(
        self,
        evaluator: BaseEvaluator,
        k: int = 5,
        min_k: int | None = None,
    ) -> None:
        """Initialize the ConsistencyEvaluator.

        Args:
            evaluator: The base evaluator to wrap for consistency measurement.
            k: Number of evaluations to perform per input (default: 5).
            min_k: Minimum number of evaluations required to include a group
                in historical mode analysis. Only applies to evaluate_dataset.
                If None, no filtering is applied (default: None).

        Raises:
            ValueError: If k < 1 or if min_k is provided and min_k < 1.
        """
        if k < 1:
            raise ValueError("k must be >= 1")

        if min_k is not None and min_k < 1:
            raise ValueError("min_k must be >= 1")

        self._evaluator = evaluator
        self._k = k
        self._min_k = min_k
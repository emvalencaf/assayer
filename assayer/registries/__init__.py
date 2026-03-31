"""Registries for metrics and evaluators.

This module provides registry classes for metrics and evaluators, along with
default shared instances for convenience. Each registry is instantiable as
independent objects, ensuring no shared state between instances.

The default instances are provided for ergonomic use but are not the only
access path - users can instantiate their own registries at any time.
"""

from assayer.registries.metric_registry import MetricRegistry
from assayer.registries.evaluator_registry import EvaluatorRegistry

# Default shared instances for convenience
default_metric_registry = MetricRegistry()
default_evaluator_registry = EvaluatorRegistry()

__all__ = [
    "MetricRegistry",
    "EvaluatorRegistry",
    "default_metric_registry",
    "default_evaluator_registry"
]
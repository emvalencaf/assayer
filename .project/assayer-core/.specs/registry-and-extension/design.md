---
spec: registry-and-extension
created: 2026-03-30
---

# Design: Registry and Extension

## Class Hierarchy

```
abc.ABC
  |
  +-- BaseEvaluator (abstract)
        |
        +-- ConcreteEvaluatorA (user-defined)
        +-- ConcreteEvaluatorB (built-in, future specs)
```

Both `MetricRegistry` and `EvaluatorRegistry` are plain classes (no inheritance). They follow the same structural pattern but are not related by a common base, because their stored types differ (`Callable` vs `type[BaseEvaluator]`) and the validation logic diverges.

## API Contracts

### BaseEvaluator

```python
# assayer/evaluators/base.py

from abc import ABC, abstractmethod
from typing import Any
from assayer.models import FieldEvaluation


class BaseEvaluator(ABC):
    """Abstract base class for all evaluators.

    Args:
        name: A non-empty string identifier for this evaluator.

    Raises:
        ValueError: If name is empty or whitespace-only.
    """

    def __init__(self, name: str) -> None: ...

    @property
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(
        self,
        prediction: Any,
        reference: Any,
        **kwargs: Any,
    ) -> FieldEvaluation: ...
```

**Design decisions:**

- `name` is stored in a private attribute `_name` and exposed via a read-only `@property`. There is no setter. This prevents accidental mutation after construction.
- The constructor calls `name.strip()` and checks the result. This normalizes whitespace-padded names while rejecting empty/whitespace-only strings.
- `**kwargs` in `evaluate()` allows subclasses to accept extra parameters (e.g., a judge prompt, thresholds) without breaking the base contract.

### MetricRegistry

```python
# assayer/registries/metric_registry.py

from typing import Any, Callable


class MetricRegistry:
    """Registry for dataset-level metric functions.

    Each instance maintains its own independent mapping of names to callables.
    """

    def __init__(self) -> None: ...

    def register(
        self,
        name: str,
        fn: Callable[[list[Any], list[Any]], float],
    ) -> None:
        """Register a metric function under the given name.

        Args:
            name: Non-empty string identifier for the metric.
            fn: A callable accepting (predictions, references) and returning float.

        Raises:
            ValueError: If name is empty or whitespace-only.
            TypeError: If fn is not callable.
            KeyError: If name is already registered.
        """

    def get(self, name: str) -> Callable[[list[Any], list[Any]], float]:
        """Retrieve a registered metric by name.

        Args:
            name: The metric name.

        Returns:
            The registered callable.

        Raises:
            KeyError: If name is not registered.
        """

    def list_metrics(self) -> list[str]:
        """Return a sorted list of all registered metric names.

        Returns:
            Sorted list of metric name strings. Empty list if no metrics registered.
        """
```

**Internal state:** `self._registry: dict[str, Callable[[list[Any], list[Any]], float]]` initialized to `{}` in `__init__`.

### EvaluatorRegistry

```python
# assayer/registries/evaluator_registry.py

from assayer.evaluators.base import BaseEvaluator


class EvaluatorRegistry:
    """Registry for evaluator classes.

    Each instance maintains its own independent mapping of names to
    BaseEvaluator subclasses.
    """

    def __init__(self) -> None: ...

    def register(
        self,
        name: str,
        cls: type[BaseEvaluator],
    ) -> None:
        """Register an evaluator class under the given name.

        Args:
            name: Non-empty string identifier for the evaluator.
            cls: A concrete subclass of BaseEvaluator.

        Raises:
            ValueError: If name is empty or whitespace-only.
            TypeError: If cls is not a subclass of BaseEvaluator, or is
                BaseEvaluator itself.
            KeyError: If name is already registered.
        """

    def get(self, name: str) -> type[BaseEvaluator]:
        """Retrieve a registered evaluator class by name.

        Args:
            name: The evaluator name.

        Returns:
            The registered BaseEvaluator subclass.

        Raises:
            KeyError: If name is not registered.
        """

    def list_evaluators(self) -> list[str]:
        """Return a sorted list of all registered evaluator names.

        Returns:
            Sorted list of evaluator name strings. Empty list if none registered.
        """
```

**Internal state:** `self._registry: dict[str, type[BaseEvaluator]]` initialized to `{}` in `__init__`.

**Validation in `register`:** Uses `issubclass(cls, BaseEvaluator)` with an explicit check that `cls is not BaseEvaluator`. This prevents registering the abstract class itself, which cannot be instantiated.

### Default Instances

```python
# assayer/registries/__init__.py

from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry

default_metric_registry = MetricRegistry()
default_evaluator_registry = EvaluatorRegistry()
```

These module-level instances are created once at import time. They are convenience shortcuts, not singletons -- any code can create a fresh `MetricRegistry()` or `EvaluatorRegistry()` at any time.

## Package Structure

```
assayer/
  __init__.py
  models.py                          # from core-models spec
  evaluators/
    __init__.py                      # re-exports BaseEvaluator
    base.py                          # BaseEvaluator ABC
  registries/
    __init__.py                      # default instances + re-exports
    metric_registry.py               # MetricRegistry
    evaluator_registry.py            # EvaluatorRegistry
```

## Validation Summary

| Method | Condition | Exception |
|--------|-----------|-----------|
| `BaseEvaluator.__init__` | `name.strip() == ""` | `ValueError` |
| `MetricRegistry.register` | `name.strip() == ""` | `ValueError` |
| `MetricRegistry.register` | `not callable(fn)` | `TypeError` |
| `MetricRegistry.register` | `name in self._registry` | `KeyError` |
| `MetricRegistry.get` | `name not in self._registry` | `KeyError` |
| `EvaluatorRegistry.register` | `name.strip() == ""` | `ValueError` |
| `EvaluatorRegistry.register` | `not issubclass(cls, BaseEvaluator)` or `cls is BaseEvaluator` | `TypeError` |
| `EvaluatorRegistry.register` | `name in self._registry` | `KeyError` |
| `EvaluatorRegistry.get` | `name not in self._registry` | `KeyError` |

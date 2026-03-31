---
prd: assayer-core
id: registry-and-extension
status: done
depends-on: [core-models]
created: 2026-03-30
---

# Spec: Registry and Extension

## Context

This spec addresses **AC-012** and **AC-013** from the assayer-core PRD.

Assayer must allow users to extend the framework with custom metrics and custom evaluator types without modifying core library code. This is the primary Open/Closed Principle mechanism in the system. Every built-in evaluator and metric will eventually be registered through these same registries, ensuring a single discovery path for all evaluation logic.

This spec depends on **core-models** because `BaseEvaluator.evaluate()` returns `FieldEvaluation`, defined in `assayer/models.py`.

## Scope

### In scope

- `BaseEvaluator` abstract base class in `assayer/evaluators/base.py`.
- `MetricRegistry` class in `assayer/registries/metric_registry.py`.
- `EvaluatorRegistry` class in `assayer/registries/evaluator_registry.py`.
- A convenience module `assayer/registries/__init__.py` that exposes default shared instances of both registries while keeping them fully instantiable as independent objects.
- Package init files: `assayer/evaluators/__init__.py`, `assayer/registries/__init__.py`.

### Out of scope

- Built-in evaluator implementations (chat, classification, NER, hallucination, LLM-as-Judge). Those belong to their own specs.
- Built-in metric implementations (accuracy, precision, recall, F1, BLEU, ROUGE-L). Those belong to their own specs.
- Runner integration (how the runner looks up evaluators/metrics by name).
- Serialization or persistence of registry state.
- Decorator-based registration syntax (may be added later; registries expose only imperative `register()` for now).

## Technical Design

### BaseEvaluator

An abstract base class using Python's `abc.ABC` and `abc.abstractmethod`. All evaluators -- built-in and user-defined -- must subclass it.

**Module:** `assayer/evaluators/base.py`

**Contract:**
- Constructor accepts `name: str`. Raises `ValueError` if `name` is empty or whitespace-only.
- `name` is stored as a read-only property (set once at construction, no setter).
- Abstract method: `evaluate(self, prediction: Any, reference: Any, **kwargs) -> FieldEvaluation`.
- No other abstract methods. Subclasses may add any additional methods or attributes they need.

**Why a class instead of a protocol:** ADR-003 explicitly mandates a base class with a registry. A protocol would not enforce the `name` attribute contract or allow `isinstance` checks that the `EvaluatorRegistry` uses for validation.

### MetricRegistry

A registry that maps string names to metric callables. A metric callable has the signature `(predictions: list[Any], references: list[Any]) -> float`.

**Module:** `assayer/registries/metric_registry.py`

**API:**
- `register(name: str, fn: Callable[[list[Any], list[Any]], float]) -> None` -- registers a metric function under the given name. Raises `ValueError` if `name` is empty or whitespace-only. Raises `TypeError` if `fn` is not callable. Raises `KeyError` if `name` is already registered (prevents silent overwrites).
- `get(name: str) -> Callable[[list[Any], list[Any]], float]` -- returns the registered callable. Raises `KeyError` if `name` is not found.
- `list_metrics() -> list[str]` -- returns a sorted list of all registered metric names.

**Internal state:** A plain `dict[str, Callable]` instance attribute (not a class variable, not module-level). Each `MetricRegistry()` call creates an independent registry.

### EvaluatorRegistry

A registry that maps string names to evaluator classes (not instances).

**Module:** `assayer/registries/evaluator_registry.py`

**API:**
- `register(name: str, cls: type[BaseEvaluator]) -> None` -- registers an evaluator class under the given name. Raises `ValueError` if `name` is empty or whitespace-only. Raises `TypeError` if `cls` is not a subclass of `BaseEvaluator`. Raises `KeyError` if `name` is already registered.
- `get(name: str) -> type[BaseEvaluator]` -- returns the registered class. Raises `KeyError` if `name` is not found.
- `list_evaluators() -> list[str]` -- returns a sorted list of all registered evaluator names.

**Internal state:** A plain `dict[str, type[BaseEvaluator]]` instance attribute. Each `EvaluatorRegistry()` call creates an independent registry.

### Default shared instances

The `assayer/registries/__init__.py` module creates one default instance of each registry for convenience:

```
default_metric_registry = MetricRegistry()
default_evaluator_registry = EvaluatorRegistry()
```

These are provided for ergonomic use but are not the only access path. Users can instantiate their own registries at any time.

## Acceptance Criteria

- [ ] AC-SPEC-001: A concrete subclass of `BaseEvaluator` that implements `evaluate()` can be instantiated with a `name` and its `name` property returns the provided value.
- [ ] AC-SPEC-002: `BaseEvaluator` cannot be instantiated directly (raises `TypeError` because `evaluate` is abstract).
- [ ] AC-SPEC-003: A subclass of `BaseEvaluator` that does not implement `evaluate()` cannot be instantiated (raises `TypeError`).
- [ ] AC-SPEC-004: `BaseEvaluator.__init__` raises `ValueError` when `name` is empty or whitespace-only.
- [ ] AC-SPEC-005: `MetricRegistry.register(name, fn)` stores the function; `MetricRegistry.get(name)` returns the same function.
- [ ] AC-SPEC-006: `MetricRegistry.register` raises `ValueError` for empty/whitespace name, `TypeError` for non-callable `fn`, and `KeyError` for duplicate name.
- [ ] AC-SPEC-007: `MetricRegistry.get` raises `KeyError` for an unregistered name.
- [ ] AC-SPEC-008: `MetricRegistry.list_metrics()` returns a sorted list of all registered metric names.
- [ ] AC-SPEC-009: `EvaluatorRegistry.register(name, cls)` stores the class; `EvaluatorRegistry.get(name)` returns the same class.
- [ ] AC-SPEC-010: `EvaluatorRegistry.register` raises `ValueError` for empty/whitespace name, `TypeError` when `cls` is not a subclass of `BaseEvaluator`, and `KeyError` for duplicate name.
- [ ] AC-SPEC-011: `EvaluatorRegistry.get` raises `KeyError` for an unregistered name.
- [ ] AC-SPEC-012: `EvaluatorRegistry.list_evaluators()` returns a sorted list of all registered evaluator names.
- [ ] AC-SPEC-013: Two independently instantiated `MetricRegistry` objects do not share state.
- [ ] AC-SPEC-014: Two independently instantiated `EvaluatorRegistry` objects do not share state.
- [ ] AC-SPEC-015: Default shared instances (`default_metric_registry`, `default_evaluator_registry`) are importable from `assayer.registries` and are functional.

## Edge Cases

- Registering with a name that is only whitespace (e.g., `"   "`) must be rejected as empty.
- Registering a class that is `BaseEvaluator` itself (not a subclass) must be rejected by `EvaluatorRegistry` since it is abstract and cannot be instantiated.
- Calling `list_metrics()` or `list_evaluators()` on an empty registry must return an empty list, not raise.
- Passing `None` as `fn` to `MetricRegistry.register` must raise `TypeError`.
- Passing a regular class (not a `BaseEvaluator` subclass) to `EvaluatorRegistry.register` must raise `TypeError`.

## Risks

- **Risk**: Future specs may need decorator-based registration (e.g., `@register_metric("name")`).
  **Mitigation**: The imperative `register()` API is the foundation; a decorator is a thin wrapper that can be added without changing the registry internals.
- **Risk**: Thread-safety may become a concern if registries are written to concurrently.
  **Mitigation**: The PRD explicitly states no concurrent writes for this version. The instance-based design avoids mutable global state. A lock can be added later without API changes.

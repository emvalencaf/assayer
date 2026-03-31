---
id: TASK-003
spec: registry-and-extension
status: done
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-003: Implement MetricRegistry

## What to do

Implement the `MetricRegistry` class in `assayer/registries/metric_registry.py` as specified in the design.md "MetricRegistry" section.

- `__init__` initializes `self._registry: dict[str, Callable[[list[Any], list[Any]], float]]` to `{}`.
- `register(name, fn)` with full validation: `ValueError` for empty/whitespace name, `TypeError` for non-callable, `KeyError` for duplicate.
- `get(name)` returns the callable or raises `KeyError`.
- `list_metrics()` returns a sorted list of names, or empty list if none registered.
- Google-style docstrings and full type hints.

## Acceptance Criteria

- [x] AC-SPEC-005: `register(name, fn)` stores the function; `get(name)` returns the same function.
- [x] AC-SPEC-006: `register` raises `ValueError` for empty/whitespace name, `TypeError` for non-callable, `KeyError` for duplicate name.
- [x] AC-SPEC-007: `get` raises `KeyError` for an unregistered name.
- [x] AC-SPEC-008: `list_metrics()` returns a sorted list of registered names.
- [x] AC-SPEC-013: Two independently instantiated `MetricRegistry` objects do not share state.

## Dependencies

- TASK-001

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_metric_registry.py`

Comprehensive tests covering all acceptance criteria:
- Registration and retrieval functionality (AC-SPEC-005)
- Input validation with proper error handling (AC-SPEC-006, AC-SPEC-007)
- Sorted listing of registered metrics (AC-SPEC-008)
- State isolation between registry instances (AC-SPEC-013)
- Edge cases: empty registry, None values, whitespace-only names

## Implementation Notes

Implemented `MetricRegistry` class with the following key design decisions:

- **Instance-based state**: Each `MetricRegistry()` instantiation creates an independent `_registry` dict, ensuring complete state isolation between registry instances as required by AC-SPEC-013.
- **Comprehensive validation**: 
  - Empty/whitespace names checked with `not name or not name.strip()`
  - Non-callable functions detected with `callable()` check
  - Duplicate registration prevented by checking `name in self._registry`
- **Error handling**: Used appropriate exception types (ValueError, TypeError, KeyError) with descriptive error messages.
- **Sorted listing**: `list_metrics()` returns `sorted(self._registry.keys())` for consistent ordering.
- **Full type annotations**: Used `dict[str, Callable[[list[Any], list[Any]], float]]` for the registry and proper typing for all method signatures.
- **Google-style docstrings**: Complete documentation with Args, Returns, Raises sections and usage examples.

## Commit

Hash: aee9e42

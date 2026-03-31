---
id: TASK-004
spec: registry-and-extension
status: done
depends-on: [TASK-001, TASK-002]
created: 2026-03-30
---

# TASK-004: Implement EvaluatorRegistry

## What to do

Implement the `EvaluatorRegistry` class in `assayer/registries/evaluator_registry.py` as specified in the design.md "EvaluatorRegistry" section.

- `__init__` initializes `self._registry: dict[str, type[BaseEvaluator]]` to `{}`.
- `register(name, cls)` with full validation: `ValueError` for empty/whitespace name, `TypeError` if `cls` is not a subclass of `BaseEvaluator` or is `BaseEvaluator` itself, `KeyError` for duplicate.
- `get(name)` returns the class or raises `KeyError`.
- `list_evaluators()` returns a sorted list of names, or empty list if none registered.
- Google-style docstrings and full type hints.

## Acceptance Criteria

- [ ] AC-SPEC-009: `register(name, cls)` stores the class; `get(name)` returns the same class.
- [ ] AC-SPEC-010: `register` raises `ValueError` for empty/whitespace name, `TypeError` when cls is not a BaseEvaluator subclass or is BaseEvaluator itself, `KeyError` for duplicate.
- [ ] AC-SPEC-011: `get` raises `KeyError` for an unregistered name.
- [ ] AC-SPEC-012: `list_evaluators()` returns a sorted list of registered names.
- [ ] AC-SPEC-014: Two independently instantiated `EvaluatorRegistry` objects do not share state.

## Dependencies

- TASK-001
- TASK-002

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_evaluator_registry.py`

Comprehensive test coverage for EvaluatorRegistry including:
- Registration and retrieval of evaluator classes
- Validation of names, class types, and duplicate handling
- State isolation between independent registry instances  
- Edge cases like unicode names, special characters, and boundary conditions

## Implementation Notes

Implemented the `EvaluatorRegistry` class in `assayer/registries/evaluator_registry.py` following the design specification. Key implementation details:

- **Internal state**: Instance attribute `self._registry: dict[str, type[BaseEvaluator]]` initialized to empty dict in `__init__`
- **Name validation**: `register()` checks for empty/whitespace-only names using `name.strip()`
- **Class validation**: Validates that `cls` is a subclass of `BaseEvaluator` using `issubclass()` and explicitly rejects `BaseEvaluator` itself since it's abstract
- **Type safety**: Added `isinstance(cls, type)` check to handle `None` and non-type objects gracefully 
- **Duplicate prevention**: Raises `KeyError` if attempting to register the same name twice
- **State isolation**: Each instance maintains independent registry state (no class variables)
- **Return types**: All methods follow the exact signatures specified in design.md
- **Sorting**: `list_evaluators()` returns `sorted()` list of keys for deterministic ordering

All 22 test cases pass, covering registration, retrieval, validation, state isolation, and edge cases including unicode names and special characters.

## Commit

Hash: 44c1afc

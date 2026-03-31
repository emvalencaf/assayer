---
id: TASK-002
spec: registry-and-extension
status: done
depends-on: [TASK-001]
created: 2026-03-30
---

# TASK-002: Implement BaseEvaluator abstract class

## What to do

Implement the `BaseEvaluator` abstract base class in `assayer/evaluators/base.py` as specified in the design.md "BaseEvaluator" section.

- Inherit from `abc.ABC`.
- `__init__(self, name: str)` stores the stripped name in `_name`. Raises `ValueError` if empty/whitespace-only.
- Read-only `name` property returning `_name`.
- Abstract method `evaluate(self, prediction: Any, reference: Any, **kwargs: Any) -> FieldEvaluation`.
- Google-style docstrings and full type hints.
- Re-export `BaseEvaluator` from `assayer/evaluators/__init__.py`.

## Acceptance Criteria

- [x] AC-SPEC-001: A concrete subclass that implements `evaluate()` can be instantiated with a name, and `name` property returns the provided value.
- [x] AC-SPEC-002: `BaseEvaluator` cannot be instantiated directly (raises `TypeError`).
- [x] AC-SPEC-003: A subclass that does not implement `evaluate()` cannot be instantiated (raises `TypeError`).
- [x] AC-SPEC-004: `BaseEvaluator.__init__` raises `ValueError` when name is empty or whitespace-only.

## Dependencies

- TASK-001

## Tests

Test file: `/home/emvalenca/personal_projects/assayer/tests/test_base_evaluator.py`

Tests cover all acceptance criteria:
- AC-SPEC-001: Concrete subclass instantiation and name property
- AC-SPEC-002: BaseEvaluator direct instantiation prevention 
- AC-SPEC-003: Incomplete subclass instantiation prevention
- AC-SPEC-004: Empty/whitespace name validation

## Implementation Notes

Successfully implemented the `BaseEvaluator` abstract base class with the following key decisions:

- Used `abc.ABC` and `abc.abstractmethod` for proper abstract class behavior
- Implemented name validation using `strip()` to normalize whitespace before checking for empty strings
- Stored the name in a private `_name` attribute and exposed it via a read-only property
- Added comprehensive Google-style docstrings with full type hints as required by ADR-006
- Properly imported `FieldEvaluation` from `assayer.models` as specified in the dependency requirements
- Re-exported `BaseEvaluator` from the evaluators package `__init__.py`

The implementation follows the Open/Closed Principle (ADR-003) by providing a clear extension point for custom evaluators without modifying core library code. All acceptance criteria have been verified through the existing test suite.

## Commit

Hash: 1bc7412

---
id: TASK-001
spec: registry-and-extension
status: done
depends-on: []
created: 2026-03-30
---

# TASK-001: Create package structure for evaluators and registries

## What to do

Create the package directories and `__init__.py` files for `assayer/evaluators/` and `assayer/registries/`. The init files should be empty placeholders at this stage (they will be populated by later tasks). Also ensure `assayer/__init__.py` exists if it does not already.

This task establishes the file structure described in the design.md "Package Structure" section.

## Acceptance Criteria

- [x] `assayer/evaluators/__init__.py` exists and is a valid Python file.
- [x] `assayer/registries/__init__.py` exists and is a valid Python file.
- [x] `assayer/__init__.py` exists.
- [x] Importing `assayer.evaluators` and `assayer.registries` does not raise errors.

## Dependencies

- none

## Tests

Test file: `tests/test_registry_package_structure.py`

Tests validate that:
- `assayer/evaluators/` and `assayer/registries/` directories exist
- Each directory contains a valid `__init__.py` file
- Both modules can be imported without errors
- `assayer/__init__.py` exists (already present)

## Implementation Notes

Created the basic package structure for evaluators and registries:

- Created `assayer/evaluators/` directory with `__init__.py` containing docstring "Evaluators package."
- Created `assayer/registries/` directory with `__init__.py` containing docstring "Registries package."
- Verified `assayer/__init__.py` already existed from previous tasks
- Both new packages can be imported without errors as empty placeholders
- All acceptance criteria met, ready for population in subsequent tasks

## Commit

Hash:

---
id: TASK-001
spec: langsmith-integration
status: pending
depends-on: []
created: 2026-03-31
---

# TASK-001: Implement make_langsmith_publisher factory

## What to do
Create `assayer/integrations/langsmith.py` and implement `make_langsmith_publisher() -> LangSmithPublisher`.

Reads `LANGCHAIN_API_KEY` from the environment and instantiates a `langsmith.Client`. Raises `EnvironmentError` if the variable is not set.

## Acceptance Criteria
- [ ] Raises `EnvironmentError` when `LANGCHAIN_API_KEY` is not in the environment
- [ ] Returns a `LangSmithPublisher` wrapping a `langsmith.Client` when the key is set
- [ ] Google-style docstring and full type hints

## Dependencies
- none

## Tests
Test file:

## Implementation Notes

## Commit
Hash:

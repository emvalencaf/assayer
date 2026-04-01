# Project Constitution

## Overview
Read `.project/PROJECT.md` for the high-level description of this project.
Read `.project/ADR.md` for global technical decisions before making new ones.

## Mandatory Workflow
Every feature follows this gate sequence — no skipping, no reordering:

```
/project:prd <feature>           → PRD (requires human approval)
      ↓
/project:spec-plan <prd>         → Spec plan (requires human approval)
      ↓
/project:spec-create <prd/spec>  → Spec + tasks (requires human approval)
      ↓
/project:implement <prd/spec>    → Test → Code → Commit (per task)
```

## Agents
| Agent            | When to use                                      |
|------------------|--------------------------------------------------|
| @agent-research  | Exploring requirements, writing PRDs             |
| @agent-spec      | Decomposing PRDs into specs and tasks            |
| @agent-tester    | Writing tests from acceptance criteria           |
| @agent-coder     | Implementing code to make tests pass             |
| @agent-docs      | Creating and validating Mermaid diagrams         |

## Decision Hierarchy
```
.project/ADR.md                          → global technical decisions
.project/{prd}/architecture.md           → decisions scoped to a PRD
.project/{prd}/.specs/{spec}/design.md   → decisions scoped to a spec
```

## Project Structure
```
.project/
├── PROJECT.md
├── ADR.md
└── {prd-name}/
    ├── prd.md
    ├── architecture.md
    ├── diagrams/
    └── .specs/
        └── {spec-name}/
            ├── spec.md
            ├── design.md         (optional)
            └── tasks/
                ├── INDEX.md      (generated, never edited manually)
                └── TASK-NNN.md
```

## Commit Format
```
type(TASK-ID): short imperative description

- acceptance criterion ✓
- acceptance criterion ✓

Refs: {spec-name}
```
Valid types: `feat` | `fix` | `refactor` | `test` | `docs` | `chore`
**One task per commit. No exceptions.**

## Code Conventions
- **Language:** Python 3.11.13 minimum.
- All public functions, methods, and classes must have **Google-style docstrings** (description, Args, Returns, Raises) and full **type hints**.
- No global mutable state — evaluators and runners must be instantiable as independent objects.
- Custom metrics and evaluators must be registerable without modifying core library files (Open/Closed Principle).
- Test files follow `test_*.py` naming; fixtures go in `conftest.py`.
- No `unittest` subclassing — use pytest exclusively.

## Test Commands
```bash
source venv/bin/activate
pytest                        # run all tests
pytest --cov=assayer          # with coverage (target: ≥ 90%)
```

## Build & Run
```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

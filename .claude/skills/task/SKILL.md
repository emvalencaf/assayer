# Skill: Task Writing

## Atomicity rules

A task is atomic when:
- It maps to a single, well-defined concern
- It can be implemented in one focused session
- It produces exactly one meaningful commit
- Its success or failure is independently verifiable

If a task requires touching more than 2–3 distinct system boundaries,
or if it would produce more than one logical commit, split it further.

## Task ID format

`TASK-NNN` — zero-padded, sequential within the spec.
Examples: `TASK-001`, `TASK-002`, `TASK-013`

## Status lifecycle

```
pending → tests-written → done
                        ↘ blocked
```

- `@agent-tester` transitions: `pending` → `tests-written`
- `@agent-coder` transitions: `tests-written` → `done` | `blocked`
- `blocked` must include a description of the blocker in the task file

## Templates

- `templates/task.md` — individual task file
- `templates/index.md` — INDEX.md (generated, never edited manually)

## Writing Standards

**What to do** — be precise. Reference the spec section this task
addresses. A task description should leave no ambiguity about what
"done" looks like.

**Acceptance Criteria** — derive directly from the parent spec.
Each criterion maps to at least one test written by @agent-tester.

**Dependencies** — declare them explicitly. The `depends-on` field
controls execution order in `/project:implement`.

**Implementation Notes** — filled by @agent-coder after implementation.
Captures decisions made during coding that are not obvious from the spec.

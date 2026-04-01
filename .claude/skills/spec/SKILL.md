# Skill: Spec Writing

## Spec boundary rules

A spec is independently deliverable when it can be merged and deployed
without depending on unfinished sibling specs. Use these checks:

- Single cohesive responsibility (one domain concept)
- Generates no more than 5–8 tasks
- Has explicit, enumerable dependencies on other specs
- Can be reviewed and approved independently

If in doubt, split the spec.

## Templates

- `templates/spec.md` — the spec itself
- `templates/architecture.md` — PRD-level architectural decisions
- `templates/design.md` — spec-level design decisions (optional)

## Writing Standards

**Context** — always reference the PRD acceptance criteria this spec
addresses (e.g., "Addresses AC-001, AC-003 from the PRD").
Every spec must trace back to a PRD.

**Technical Design** — write for someone who has not read the PRD.
Define data shapes, API signatures, state transitions. This is narrative,
not code. If you are writing implementation code, stop — that belongs to
@agent-coder.

**Acceptance Criteria** — these are consumed verbatim by @agent-tester.
Write them as precise, testable statements. Ambiguous criteria produce
ambiguous tests, which produce ambiguous implementations.

**Edge Cases** — enumerate them explicitly. Tester agents use these to
write tests beyond the happy path.

**design.md** — create it only when the spec has complexity that would
clutter `spec.md`: non-trivial API contracts, multi-step state machines,
complex UI flows, or significant data transformation logic.

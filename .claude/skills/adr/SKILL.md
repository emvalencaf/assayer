# Skill: Architecture Decision Records

## When to write an ADR

Write an ADR when a decision:
- Is difficult or costly to reverse
- Affects multiple specs or PRDs
- Involves a meaningful trade-off between competing valid approaches
- Will likely be questioned by future contributors

Do NOT write an ADR for:
- Obvious implementation details with no real alternatives
- Decisions already enforced by the stack or framework
- Decisions scoped entirely to one spec — use `design.md` instead

## Where each decision belongs

| Scope          | File                                              |
|----------------|---------------------------------------------------|
| Entire project | `.project/ADR.md`                                 |
| One PRD        | `.project/{prd}/architecture.md` → Key Decisions  |
| One spec       | `.project/{prd}/.specs/{spec}/design.md`          |

## Template

See `templates/adr-entry.md` for the entry block to append to `ADR.md`.

## Writing Standards

**Context** — describe the situation that made the decision necessary.
Include alternatives considered and why they were rejected. A reader
unfamiliar with the project must understand the problem from context alone.

**Decision** — one clear, direct statement of what was decided.
Avoid narrating the deliberation — state the outcome.

**Consequences** — be honest about trade-offs. If the decision has known
downsides, document them. This prevents the same debate from recurring
in future sessions.

**Superseding** — when reversing a past decision, do not delete the old
ADR entry. Mark it `superseded by ADR-NNN` and create a new entry that
references what changed and why. The history is the value.

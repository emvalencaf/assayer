# Skill: PRD Writing

## When to create a new PRD

- A new user-facing feature or capability
- A significant change to existing behavior
- A new integration or external dependency
- A non-trivial technical initiative with product impact

One PRD per cohesive user capability.
If a PRD would require more than 5–7 specs, split it.

## Template

See `templates/prd.md` for the full template to copy.

## Writing Standards

**Problem Statement** — describe the problem, not the solution.
If you are describing UI or code, you have gone too far.

**Acceptance Criteria** — must be binary (pass/fail), specific, and testable
by someone who did not write the spec. Avoid vague qualifiers like "fast"
or "user-friendly". Write measurable thresholds instead.

Bad:  "The page should load quickly"
Good: "The page must load in under 1.5s for 95% of requests"

**Assumptions** — if an assumption is wrong, the PRD is invalid.
Write them explicitly so they can be challenged early.

**Non-Goals** — the absence of a non-goals section implies everything
not mentioned is in scope. Always write it.

**Scenarios** — describe real situations, not feature lists.
Use the format: "As a {user type}, I want to {action} so that {outcome}."

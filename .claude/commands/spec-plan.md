# /project:spec-plan

Decompose an approved PRD into a spec plan for human review.

Usage: `/project:spec-plan <prd-name>`

## Steps

1. Set Relay pipeline state:
   ```bash
   bash .claude/hooks/relay-state.sh set-phase spec-plan
   bash .claude/hooks/relay-state.sh set-agent agent-spec
   ```
2. Read `.project/$ARGUMENTS/prd.md`
3. Use @agent-spec to identify spec boundaries and dependency order
4. Output a structured plan:
   ```
   Spec 1: {name} — {one-line description}
   Spec 2: {name} — {one-line description} (depends on: Spec 1)
   ```
5. Clear state and wait for human approval:
   ```bash
   bash .claude/hooks/relay-state.sh clear
   ```
6. Do not create spec files here — use `/project:spec-create` for that

# /project:spec-create

Create a single spec and its tasks from an approved spec plan.

Usage: `/project:spec-create <prd-name>/<spec-name>`

## Steps

1. Parse input: `prd-name` and `spec-name` from $ARGUMENTS
2. Set Relay pipeline state:
   ```bash
   bash .claude/hooks/relay-state.sh set-phase spec-create
   bash .claude/hooks/relay-state.sh set-agent agent-spec
   bash .claude/hooks/relay-state.sh set-task <prd-name> <spec-name> none
   ```
3. Read `.project/{prd-name}/prd.md` for business context
4. Read `.project/ADR.md` and `.project/{prd-name}/architecture.md`
   for constraints — do not contradict existing decisions
5. Use @agent-spec for this session
6. Create the spec directory: `.project/{prd-name}/.specs/{spec-name}/`
7. Write `spec.md` using `.claude/skills/spec/SKILL.md`
8. Write `design.md` only if the spec has meaningful design complexity
9. Create one `TASK-NNN.md` per task using `.claude/skills/task/SKILL.md`
10. Generate `tasks/INDEX.md` as a read-only summary
11. If any architectural decision was made, append to `.project/ADR.md`
    using `.claude/skills/adr/SKILL.md`
12. Clear state, present the spec summary, wait for explicit human approval:
    ```bash
    bash .claude/hooks/relay-state.sh clear
    ```

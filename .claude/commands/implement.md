# /project:implement

Implement all pending tasks for a spec using isolated subagent contexts.

Usage: `/project:implement <prd-name>/<spec-name>`

## Steps

1. Parse input: extract `prd-name` and `spec-name` from $ARGUMENTS
2. Set Relay pipeline state:
   ```bash
   bash .claude/hooks/relay-state.sh set-phase implement
   bash .claude/hooks/relay-state.sh set-agent orchestrator
   ```
3. Read `.project/{prd}/.specs/{spec}/tasks/INDEX.md` for the task list
4. Filter tasks with status `pending` or `tests-written`
5. Respect the dependency order declared in each task's `depends-on` field
6. For each eligible task — one subagent per task, in sequence:

   **a. Test phase** — skip if status is already `tests-written`

   Update state before delegating:
   ```bash
   bash .claude/hooks/relay-state.sh set-agent agent-tester
   bash .claude/hooks/relay-state.sh set-task <prd> <spec> <TASK-ID>
   ```
   - Use @agent-tester with the task file path
   - Confirm task status updated to `tests-written` before continuing
   - Do not proceed if tester reports a blocker

   **b. Implementation phase**

   Update state before delegating:
   ```bash
   bash .claude/hooks/relay-state.sh set-agent agent-coder
   bash .claude/hooks/relay-state.sh set-task <prd> <spec> <TASK-ID>
   ```
   - Use @agent-coder with the task file path
   - Confirm all tests pass before continuing

   **c. Commit phase**

   Update state before committing:
   ```bash
   bash .claude/hooks/relay-state.sh set-phase commit
   bash .claude/hooks/relay-state.sh set-agent orchestrator
   ```
   - Run `/project:commit .project/{prd}/.specs/{spec}/tasks/TASK-NNN.md`
   - Confirm the commit hash is recorded in the task file

7. After all tasks complete, clear pipeline state:
   ```bash
   bash .claude/hooks/relay-state.sh clear
   ```
8. Report: tasks completed, commits made (with hashes), blocked tasks.

**Never advance to the next task if the current one has failing tests
or an uncommitted implementation.**

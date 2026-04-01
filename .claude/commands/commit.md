# /project:commit

Create an atomic commit for a completed task.

Usage: `/project:commit <path/to/TASK-NNN.md>`

## Steps

1. Read the task file — confirm `status` is `done`
2. Run the full test suite — abort if anything fails
3. Stage only the files related to this task
   If staging is ambiguous, list the files and ask for confirmation
4. Commit using this exact format:

   ```
   type(TASK-ID): short imperative description

   - acceptance criterion ✓
   - acceptance criterion ✓

   Refs: {spec-name}
   ```

   Valid types: `feat` | `fix` | `refactor` | `test` | `docs` | `chore`

5. Record the commit hash in the task file under `## Commit`
6. Confirm the commit was created before returning

## Hard Rules

- One task per commit — never group multiple tasks
- Never commit with failing tests
- Never commit without recording the hash in the task file
- Never commit if task status is not `done`

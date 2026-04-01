# /project:prd

Conduct a requirements refinement session and produce a PRD.

Usage: `/project:prd <prd-name>`

## Steps

1. Set Relay pipeline state:
   ```bash
   bash .claude/hooks/relay-state.sh set-phase prd
   bash .claude/hooks/relay-state.sh set-agent agent-research
   ```
2. Read `.project/PROJECT.md` to align with existing project vision
3. Use @agent-research for the entire session
4. Ask clarifying questions — do not skip this step
5. Produce the PRD at `.project/$ARGUMENTS/prd.md`
6. Clear state and present a summary — wait for explicit human approval:
   ```bash
   bash .claude/hooks/relay-state.sh clear
   ```
7. Do not proceed to spec planning until approval is given

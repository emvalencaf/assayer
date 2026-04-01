#!/bin/bash
# .claude/hooks/relay-state.sh
#
# Helper called by Relay commands to update the current pipeline state.
# This state is read by pre-tool and post-tool hooks to tag every
# tool call with the correct agent, phase, and task context.
#
# Usage:
#   bash .claude/hooks/relay-state.sh set-phase <phase>
#   bash .claude/hooks/relay-state.sh set-agent <agent>
#   bash .claude/hooks/relay-state.sh set-task  <prd> <spec> <task-id>
#   bash .claude/hooks/relay-state.sh clear
#
# Phases: research | prd | architecture | spec | test-writing | implementation | documentation | main | idle

set -euo pipefail

RELAY_DIR=".relay"
mkdir -p "$RELAY_DIR"

COMMAND="${1:-}"

case "$COMMAND" in
  set-phase)
    echo "${2:-idle}" > "$RELAY_DIR/current-phase"
    ;;

  set-agent)
    echo "${2:-none}" > "$RELAY_DIR/current-agent"
    ;;

  set-task)
    # Args: <prd> <spec> <task-id>
    echo "${2:-none}" > "$RELAY_DIR/current-prd"
    echo "${3:-none}" > "$RELAY_DIR/current-spec"
    echo "${4:-none}" > "$RELAY_DIR/current-task"
    ;;

  clear)
    echo "idle"  > "$RELAY_DIR/current-phase"
    echo "none"  > "$RELAY_DIR/current-agent"
    echo "none"  > "$RELAY_DIR/current-task"
    echo "none"  > "$RELAY_DIR/current-spec"
    echo "none"  > "$RELAY_DIR/current-prd"
    ;;

  status)
    echo "Phase : $(cat $RELAY_DIR/current-phase 2>/dev/null || echo 'idle')"
    echo "Agent : $(cat $RELAY_DIR/current-agent 2>/dev/null || echo 'none')"
    echo "PRD   : $(cat $RELAY_DIR/current-prd   2>/dev/null || echo 'none')"
    echo "Spec  : $(cat $RELAY_DIR/current-spec  2>/dev/null || echo 'none')"
    echo "Task  : $(cat $RELAY_DIR/current-task  2>/dev/null || echo 'none')"
    ;;

  *)
    echo "Usage: relay-state.sh <set-phase|set-agent|set-task|clear|status>" >&2
    exit 1
    ;;
esac

exit 0

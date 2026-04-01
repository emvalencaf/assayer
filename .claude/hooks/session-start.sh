#!/bin/bash
# .claude/hooks/session-start.sh
#
# Fires on every user prompt submission.
# Resets Relay state if no active phase is detected,
# ensuring stale state from a previous session does not pollute metrics.

set -euo pipefail

RELAY_DIR=".relay"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Ensure the .relay directory exists
mkdir -p "$RELAY_DIR" "$RELAY_DIR/logs" "$RELAY_DIR/timings"

# If no current phase is set, initialize to idle
if [ ! -f "$RELAY_DIR/current-phase" ]; then
  echo "idle" > "$RELAY_DIR/current-phase"
  echo "none" > "$RELAY_DIR/current-agent"
  echo "none" > "$RELAY_DIR/current-task"
  echo "none" > "$RELAY_DIR/current-spec"
  echo "none" > "$RELAY_DIR/current-prd"
fi

# Log session start
LOG_FILE="$RELAY_DIR/logs/$(date +%Y-%m-%d).jsonl"
SESSION_ID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen 2>/dev/null || echo "unknown")
echo "{\"timestamp\":\"$TIMESTAMP\",\"event\":\"session_start\",\"session\":\"$SESSION_ID\"}" >> "$LOG_FILE"

exit 0

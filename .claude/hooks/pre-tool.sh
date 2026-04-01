#!/bin/bash
# .claude/hooks/pre-tool.sh
#
# Fires before every tool call.
# Receives a JSON payload on stdin with tool context.
# Reads Relay state files to tag events with agent/phase/task.
#
# Relay state files (auto-written when Agent tool fires, or via relay-state.sh):
#   .relay/current-agent   — active agent name
#   .relay/current-phase   — current pipeline phase
#   .relay/current-task    — current TASK-NNN id
#   .relay/current-spec    — current spec name
#   .relay/current-prd     — current PRD name

set -euo pipefail

OTEL_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4317}"
RELAY_DIR=".relay"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EPOCH_NS=$(date +%s%N 2>/dev/null || echo "0")

# Read stdin payload from Claude Code
INPUT=$(cat)

# Extract tool info from payload
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")

# Auto-detect active agent when the Agent tool fires.
# Reads subagent_type from the tool input and updates state files so that
# all subsequent tool calls from the subagent are tagged correctly.
if [ "$TOOL_NAME" = "Agent" ]; then
  SUBAGENT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
name = (d.get('tool_input') or {}).get('subagent_type') or ''
print(name.strip() if name.strip() else 'unknown')
" 2>/dev/null || echo "unknown")

  if [ "$SUBAGENT" != "unknown" ] && [ -n "$SUBAGENT" ]; then
    mkdir -p "$RELAY_DIR"
    echo "$SUBAGENT" > "$RELAY_DIR/current-agent"
    case "$SUBAGENT" in
      research)     echo "research"       > "$RELAY_DIR/current-phase" ;;
      prd)          echo "prd"            > "$RELAY_DIR/current-phase" ;;
      architecture) echo "architecture"   > "$RELAY_DIR/current-phase" ;;
      spec)         echo "spec"           > "$RELAY_DIR/current-phase" ;;
      tester)       echo "test-writing"   > "$RELAY_DIR/current-phase" ;;
      coder)        echo "implementation" > "$RELAY_DIR/current-phase" ;;
      docs)         echo "documentation"  > "$RELAY_DIR/current-phase" ;;
      *)            echo "agent"          > "$RELAY_DIR/current-phase" ;;
    esac
  fi
fi

# Read Relay context state
AGENT=$(cat "$RELAY_DIR/current-agent" 2>/dev/null || echo "unknown")
PHASE=$(cat "$RELAY_DIR/current-phase" 2>/dev/null || echo "unknown")
TASK=$(cat "$RELAY_DIR/current-task" 2>/dev/null || echo "none")
SPEC=$(cat "$RELAY_DIR/current-spec" 2>/dev/null || echo "none")
PRD=$(cat "$RELAY_DIR/current-prd" 2>/dev/null || echo "none")

# Record tool start time for duration tracking in post-tool
mkdir -p "$RELAY_DIR/timings"
echo "$EPOCH_NS" > "$RELAY_DIR/timings/${TOOL_NAME}_start"

# Emit log event to OTEL collector
# Silently skip if collector is not reachable
curl -sf -X POST "${OTEL_ENDPOINT}/v1/logs" \
  -H "Content-Type: application/json" \
  -d "{
    \"resourceLogs\": [{
      \"resource\": {
        \"attributes\": [
          {\"key\": \"service.name\", \"value\": {\"stringValue\": \"relay\"}},
          {\"key\": \"relay.agent\", \"value\": {\"stringValue\": \"$AGENT\"}},
          {\"key\": \"relay.phase\", \"value\": {\"stringValue\": \"$PHASE\"}},
          {\"key\": \"relay.prd\", \"value\": {\"stringValue\": \"$PRD\"}},
          {\"key\": \"relay.spec\", \"value\": {\"stringValue\": \"$SPEC\"}},
          {\"key\": \"relay.task\", \"value\": {\"stringValue\": \"$TASK\"}}
        ]
      },
      \"scopeLogs\": [{
        \"logRecords\": [{
          \"timeUnixNano\": \"$EPOCH_NS\",
          \"severityText\": \"INFO\",
          \"body\": {\"stringValue\": \"pre_tool_use\"},
          \"attributes\": [
            {\"key\": \"tool.name\", \"value\": {\"stringValue\": \"$TOOL_NAME\"}},
            {\"key\": \"session.id\", \"value\": {\"stringValue\": \"$SESSION_ID\"}},
            {\"key\": \"event.type\", \"value\": {\"stringValue\": \"pre_tool_use\"}},
            {\"key\": \"timestamp\", \"value\": {\"stringValue\": \"$TIMESTAMP\"}}
          ]
        }]
      }]
    }]
  }" > /dev/null 2>&1 || true

exit 0

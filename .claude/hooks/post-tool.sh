#!/bin/bash
# .claude/hooks/post-tool.sh
#
# Fires after every tool call completes.
# Emits a rich event with Relay context tags and duration.
# This is the primary source for token observability in Relay.

set -euo pipefail

OTEL_ENDPOINT="${OTEL_EXPORTER_OTLP_ENDPOINT:-http://localhost:4317}"
RELAY_DIR=".relay"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EPOCH_NS=$(date +%s%N 2>/dev/null || echo "0")

# Read stdin payload from Claude Code
INPUT=$(cat)

# Extract fields from payload
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name','unknown'))" 2>/dev/null || echo "unknown")
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")
EXIT_CODE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('exit_code',0))" 2>/dev/null || echo "0")

# Read Relay context state
AGENT=$(cat "$RELAY_DIR/current-agent" 2>/dev/null || echo "unknown")
PHASE=$(cat "$RELAY_DIR/current-phase" 2>/dev/null || echo "unknown")
TASK=$(cat "$RELAY_DIR/current-task" 2>/dev/null || echo "none")
SPEC=$(cat "$RELAY_DIR/current-spec" 2>/dev/null || echo "none")
PRD=$(cat "$RELAY_DIR/current-prd" 2>/dev/null || echo "none")

# Calculate duration from pre-tool timestamp
DURATION_MS=0
START_FILE="$RELAY_DIR/timings/${TOOL_NAME}_start"
if [ -f "$START_FILE" ]; then
  START_NS=$(cat "$START_FILE")
  DURATION_MS=$(( (EPOCH_NS - START_NS) / 1000000 ))
  rm -f "$START_FILE"
fi

# Determine success/failure
STATUS="success"
if [ "$EXIT_CODE" != "0" ]; then
  STATUS="failure"
fi

# Reset agent/phase to main after Agent tool completes.
# The subagent is done; subsequent tool calls belong to the main thread.
if [ "$TOOL_NAME" = "Agent" ]; then
  echo "main" > "$RELAY_DIR/current-agent"
  echo "main" > "$RELAY_DIR/current-phase"
fi

# Append to local JSONL log (always works, even without collector)
mkdir -p "$RELAY_DIR/logs"
LOG_FILE="$RELAY_DIR/logs/$(date +%Y-%m-%d).jsonl"
echo "{\"timestamp\":\"$TIMESTAMP\",\"event\":\"post_tool_use\",\"agent\":\"$AGENT\",\"phase\":\"$PHASE\",\"prd\":\"$PRD\",\"spec\":\"$SPEC\",\"task\":\"$TASK\",\"tool\":\"$TOOL_NAME\",\"duration_ms\":$DURATION_MS,\"status\":\"$STATUS\",\"session\":\"$SESSION_ID\"}" >> "$LOG_FILE"

# Emit to OTEL collector (silently skip if not reachable)
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
          \"body\": {\"stringValue\": \"post_tool_use\"},
          \"attributes\": [
            {\"key\": \"tool.name\", \"value\": {\"stringValue\": \"$TOOL_NAME\"}},
            {\"key\": \"tool.status\", \"value\": {\"stringValue\": \"$STATUS\"}},
            {\"key\": \"tool.duration_ms\", \"value\": {\"intValue\": $DURATION_MS}},
            {\"key\": \"session.id\", \"value\": {\"stringValue\": \"$SESSION_ID\"}},
            {\"key\": \"event.type\", \"value\": {\"stringValue\": \"post_tool_use\"}},
            {\"key\": \"timestamp\", \"value\": {\"stringValue\": \"$TIMESTAMP\"}}
          ]
        }]
      }]
    }]
  }" > /dev/null 2>&1 || true

exit 0

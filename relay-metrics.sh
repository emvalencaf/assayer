#!/bin/bash
# relay-metrics.sh
#
# Analyzes Relay observability logs from .relay/logs/*.jsonl
# and prints a token efficiency report by agent, phase, and task.
#
# Usage:
#   bash relay-metrics.sh               # today's log
#   bash relay-metrics.sh 2025-01-15    # specific date
#   bash relay-metrics.sh --all         # all logs
#   bash relay-metrics.sh --agent spec  # filter by agent
#
# Prerequisites: python3 (standard install)

set -euo pipefail

RELAY_DIR=".relay/logs"
DATE="${1:-$(date +%Y-%m-%d)}"
FILTER_AGENT="${2:-}"

if [ ! -d "$RELAY_DIR" ]; then
  echo "No Relay logs found at $RELAY_DIR"
  echo "Start using /project:prd to generate observability data."
  exit 0
fi

# Collect log files
if [ "$DATE" = "--all" ]; then
  LOG_FILES=$(ls "$RELAY_DIR"/*.jsonl 2>/dev/null || true)
else
  LOG_FILES="$RELAY_DIR/$DATE.jsonl"
fi

if [ -z "$LOG_FILES" ] || [ ! -f "$LOG_FILES" ]; then
  echo "No logs found for: $DATE"
  exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Relay Observability Report"
echo "  Period: $DATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << PYEOF
import json
import sys
from collections import defaultdict

log_files = """$LOG_FILES""".strip().split()
filter_agent = """$FILTER_AGENT""".strip()

events = []
for f in log_files:
    try:
        with open(f) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass

if not events:
    print("No events found.")
    sys.exit(0)

# Filter by agent if requested
if filter_agent:
    events = [e for e in events if e.get("agent") == filter_agent]

# --- Tool call count by agent ---
agent_tool_counts = defaultdict(lambda: defaultdict(int))
agent_durations   = defaultdict(lambda: defaultdict(list))
phase_tool_counts = defaultdict(int)
task_tool_counts  = defaultdict(lambda: defaultdict(int))
failures          = []

for e in events:
    if e.get("event") != "post_tool_use":
        continue
    agent   = e.get("agent", "unknown")
    tool    = e.get("tool", "unknown")
    phase   = e.get("phase", "unknown")
    task    = e.get("task", "none")
    dur     = e.get("duration_ms", 0)
    status  = e.get("status", "success")

    agent_tool_counts[agent][tool] += 1
    agent_durations[agent][tool].append(dur)
    phase_tool_counts[phase] += 1
    task_tool_counts[task][agent] += 1

    if status == "failure":
        failures.append({"agent": agent, "tool": tool, "task": task,
                         "ts": e.get("timestamp", "")})

# --- Report: Tool calls by agent ---
print("\n## Tool Calls by Agent")
print(f"{'Agent':<20} {'Tool':<20} {'Calls':>6} {'Avg ms':>8}")
print("-" * 58)
for agent in sorted(agent_tool_counts):
    for tool in sorted(agent_tool_counts[agent]):
        count = agent_tool_counts[agent][tool]
        durs  = agent_durations[agent][tool]
        avg   = int(sum(durs) / len(durs)) if durs else 0
        print(f"{agent:<20} {tool:<20} {count:>6} {avg:>7}ms")

# --- Report: Tool calls by phase ---
print("\n## Tool Calls by Pipeline Phase")
print(f"{'Phase':<20} {'Calls':>6}")
print("-" * 28)
for phase in sorted(phase_tool_counts):
    print(f"{phase:<20} {phase_tool_counts[phase]:>6}")

# --- Report: Tool calls per task ---
print("\n## Tool Calls per Task")
print(f"{'Task':<20} {'Agent':<20} {'Calls':>6}")
print("-" * 48)
for task in sorted(task_tool_counts):
    if task == "none":
        continue
    for agent in sorted(task_tool_counts[task]):
        print(f"{task:<20} {agent:<20} {task_tool_counts[task][agent]:>6}")

# --- Report: Context isolation signal ---
print("\n## Context Isolation Signal")
print("Ratio of Read calls to Write/Edit calls per agent.")
print("A healthy tester has 0 Write calls. A healthy coder has high Read.")
print()
print(f"{'Agent':<20} {'Reads':>6} {'Writes':>7} {'Edits':>6} {'R/(W+E)':>9}")
print("-" * 52)
for agent in sorted(agent_tool_counts):
    reads  = agent_tool_counts[agent].get("Read", 0)
    writes = agent_tool_counts[agent].get("Write", 0)
    edits  = agent_tool_counts[agent].get("Edit", 0)
    denom  = writes + edits
    ratio  = f"{reads/denom:.1f}x" if denom > 0 else "inf"
    print(f"{agent:<20} {reads:>6} {writes:>7} {edits:>6} {ratio:>9}")

# --- Report: Failures ---
if failures:
    print(f"\n## Tool Failures ({len(failures)} total)")
    print(f"{'Timestamp':<22} {'Agent':<20} {'Tool':<20} {'Task':<15}")
    print("-" * 80)
    for f in failures[:20]:
        print(f"{f['ts']:<22} {f['agent']:<20} {f['tool']:<20} {f['task']:<15}")
else:
    print("\n## Tool Failures: none ✓")

# --- Summary ---
total_calls = sum(phase_tool_counts.values())
total_tasks = len([t for t in task_tool_counts if t != "none"])
print(f"\n## Summary")
print(f"  Total tool calls : {total_calls}")
print(f"  Tasks observed   : {total_tasks}")
print(f"  Agents active    : {len(agent_tool_counts)}")
print(f"  Phases covered   : {', '.join(sorted(phase_tool_counts.keys()))}")
print()
PYEOF

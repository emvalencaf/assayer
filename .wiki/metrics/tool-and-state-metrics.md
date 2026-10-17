---
type: Metric
title: Tool and end-state metrics
description: Deterministic agent metrics scoring the tools a Trajectory called, their arguments and the state the run left behind.
resource: assayer/metrics/agent.py
tags: [metrics, agent, trajectory, tools, state]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-18T12:30:00Z }
sources:
  - id: agent-metrics
    resource: assayer/metrics/agent.py
    title: tool_correctness, tool_argument_match, end_state_match
  - id: alignment
    resource: assayer/alignment.py
    title: align_by_key
  - id: agent-tests
    resource: tests/metrics/test_agent.py
    title: Agent metric tests
---

# Overview

Three deterministic, `trajectory`-level metrics (#32) join
[step efficiency](step-efficiency.md). `register_agent_metrics(registry)`
registers all four.[^agent-metrics] They return `Detailed` or `None` where
useful, see the [metric contract](metric-contract.md).

| Metric | Requires | Compares |
|---|---|---|
| `tool_correctness` | `expected_tool_calls` | Names of the `tool` Steps against the expected names. |
| `tool_argument_match` | `expected_tool_calls` | Arguments of each matched call against the Step `input`. |
| `end_state_match` | none declared | `Trajectory.final_state` against `Case.expected_state`. |

Each expected call in `Case.expected_tool_calls` is a name or a
`{"name", "arguments"}` dictionary.

# tool_correctness

F1 over the multiset of tool names: a tool called twice must be expected twice.
Arguments are left to `tool_argument_match`. Non-`tool` Steps are ignored.

* `ordered=True` counts only the names in the expected order (longest common subsequence).
* Two empty sequences score 1.0; tools called when none were expected, or the reverse, score 0.0.[^agent-tests]

# tool_argument_match

Each expected call is paired with the earliest unpaired `tool` Step of the same
name, using `align_by_key` from `assayer/alignment.py`.[^alignment] A pair scores
the share of its expected argument leaves (dotted paths, exact equality) that the
Step's `input` holds with the same value. Extra arguments are not penalised and a
call expecting none scores 1.0.

* The Trajectory Score is the mean over the matched calls: 0.0 when calls were expected and none matched, 1.0 when none were expected.
* One further Score per matched Step, with `target="step"` and the Step `id` (a Step without an `id` gets none).
* Expected calls with no Step are left to `tool_correctness`.[^agent-tests]

# end_state_match

Compares `final_state` with `expected_state` leaf by leaf at dotted paths, with
exact equality, whatever path the agent took. A tool that was called but changed
nothing leaves its leaf wrong.

* The Trajectory value is the mean over the leaves, plus one Score per leaf with `field` set to its dotted path.
* Leaves are paired internally by a tuple of keys and indexes, and the dotted string is built only for the Score `field`. So a key containing a dot (`{"a.b": 1}`) never collides with a nested path (`{"a": {"b": 1}}`), nor a key `"0"` with the list index 0; each leaf is missing on the other side and scores 0.0.[^agent-tests]
* Lists are compared by index; an emptied container is a leaf and so differs from a full one.
* A missing leaf scores 0.0. The expected state is a subset by default; `strict=True` also scores each extra leaf 0.0.
* An `expected_state` with no `final_state` is an `EvaluationFailure`; a Case without `expected_state` is skipped (no Score, no failure).[^agent-tests]

[^agent-metrics]: tool_correctness, tool_argument_match, end_state_match
[^alignment]: align_by_key
[^agent-tests]: Agent metric tests

---
type: Metric
title: Step efficiency
description: Agent metric scoring how close a Trajectory stayed to the expected number of Steps, as min(1, expected / actual).
resource: assayer/metrics/agent.py
tags: [metrics, agent, trajectory]
status: draft
generated: { by: claude-code/pre-commit, at: 2026-10-17T20:00:00Z }
sources:
  - id: agent-metrics
    resource: assayer/metrics/agent.py
    title: step_efficiency and register_agent_metrics
  - id: contract-tests
    resource: tests/metrics/test_agent.py
    title: Step efficiency tests
---

# Overview

`step_efficiency(trajectory, case)` in `assayer/metrics/agent.py` is the first
metric on the [metric contract](metric-contract.md). It is a deterministic,
`trajectory`-level metric that requires `expected_steps`;
`register_agent_metrics(registry)` registers it.[^agent-metrics]

# Computation

`min(1, expected_steps / actual_steps)`, where:

* `expected_steps` is the length of `Case.expected_steps` (0 if it is unset, though the contract never calls the metric then).
* `actual_steps` counts only the `model` and `tool` Steps of the Trajectory; `retrieval` and `other` Steps are ignored.

| Situation | Score |
|---|---|
| Actual Steps at or below expected | 1.0 |
| 8 actual against 4 expected | 0.5 |
| No counted Step, none expected | 1.0 |
| No counted Step, some expected | 0.0 |

When `Case.expected_steps` is `None`, the contract emits an `EvaluationFailure`
instead of a Score. Only the `step_efficiency` Score is produced; the raw step
counts never become Scores.[^contract-tests]

[^agent-metrics]: step_efficiency and register_agent_metrics
[^contract-tests]: Step efficiency tests

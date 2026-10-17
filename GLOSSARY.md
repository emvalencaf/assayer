# Assayer

A Python library for evaluating and observing LLM-powered applications and agents, with deterministic metrics and LLM-as-Judge.

## Language

**Trajectory**:
The ordered record of what an agent did for one input: its steps, including model calls and tool calls, up to the final answer.
_Avoid_: Trace, run log

**Score**:
A single named numeric result of applying a metric to one prediction or one trajectory.
_Avoid_: Grade, rating

**Adapter**:
The vendor-neutral boundary through which Assayer exchanges results with an observability backend such as Langfuse or LangSmith.
_Avoid_: Connector, plugin

**Judge**:
The injected language model that scores an output against a rubric when a metric is not deterministic.
_Avoid_: Grader, evaluator model

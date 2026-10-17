# Assayer

A Python library for evaluating and observing LLM-powered applications and agents, with deterministic metrics and LLM-as-Judge.

## Language

**Trajectory**:
The ordered record of what an agent did for one input: its Steps, up to the final answer.
_Avoid_: Trace, run log

**Step**:
One unit of work inside a Trajectory: a model call, a tool call or a retrieval.
_Avoid_: Span, observation, run

**Score**:
A single named result in the range 0 to 1 of applying a metric to one Step or one Trajectory.
_Avoid_: Grade, rating

**Dataset**:
A named collection of Cases.
_Avoid_: Test set, benchmark

**Case**:
One input of a Dataset, with an optional reference to compare against.
_Avoid_: Example, item, sample

**Experiment**:
The Trajectories and Scores produced by running one target over a Dataset, with each repetition of a Case kept as its own Trajectory.
_Avoid_: Run, evaluation run

**Adapter**:
The vendor-neutral boundary through which Assayer exchanges results with an observability backend such as Langfuse or LangSmith.
_Avoid_: Connector, plugin

**Judge**:
The injected language model that scores an output against criteria given in a prompt when a metric is not deterministic.
_Avoid_: Grader, evaluator model

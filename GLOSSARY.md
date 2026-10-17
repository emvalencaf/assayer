# Assayer

A Python library for evaluating and observing LLM-powered applications and agents, with deterministic metrics and LLM-as-Judge.

## Language

**Trajectory**:
The ordered record of what an agent did for one input: its Steps, up to the final answer.
_Avoid_: Trace, run log

**Step**:
One unit of work inside a Trajectory: a model call, a tool call, a retrieval or any other kind of work.
_Avoid_: Span, observation, run

**Score**:
A single named result in the range 0 to 1 of applying a metric to one Step, one Trajectory or a whole Experiment (for aggregates such as pass^k), optionally for one Field of the output.
_Avoid_: Grade, rating

**Field**:
A named part of the structured output of a target, measured on its own with its own metrics.
_Avoid_: Column, attribute, key

**End state**:
The condition of the world an agent leaves behind after running, observed by the target and compared with the expected one, regardless of the path taken.
_Avoid_: Final output, outcome

**Alignment**:
The pairing of each predicted item of a list Field with an expected item, so the items can be compared property by property; items left without a pair are missing or extra.
_Avoid_: Matching, mapping

**Dataset**:
A named collection of Cases.
_Avoid_: Test set, benchmark

**Case**:
One input of a Dataset, with an optional reference to compare against.
_Avoid_: Example, item, sample

**Experiment**:
The Trajectories and Scores produced by running one target over a Dataset, with each repetition of a Case kept as its own Trajectory.
_Avoid_: Run, evaluation run

**Metric**:
A named way of computing Scores for a Step, a Trajectory or an Experiment, declaring the inputs it requires and whether it is deterministic or uses a Judge.
_Avoid_: Evaluator, scorer

**Evaluation failure**:
A metric that could not be computed for a Step or Trajectory, kept as data in the Experiment instead of aborting it.
_Avoid_: Exception, crash

**Adapter**:
The vendor-neutral boundary through which Assayer exchanges results with an observability backend such as Langfuse or LangSmith.
_Avoid_: Connector, plugin

**Judge**:
The injected language model that scores an output against criteria given in a prompt when a metric is not deterministic.
_Avoid_: Grader, evaluator model

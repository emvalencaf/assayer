---
type: Reference
title: Judge metrics
description: The Judge Protocol, Assayer-owned prompts, tolerant parsing, Judge accounting and the criteria judge.
resource: assayer/metrics/judge.py
tags: [metrics, judge]
status: stable
generated: { by: claude-code/pre-commit, at: 2026-10-17T21:00:00Z }
sources:
  - id: judges
    resource: assayer/judges/__init__.py
    title: Public API of the judges subpackage
  - id: criteria
    resource: assayer/metrics/judge.py
    title: make_criteria_judge
  - id: tests
    resource: tests/metrics/test_judge.py
    title: Criteria judge tests through the Runner
---

# Overview

A Judge-based metric has `kind="judge"` and asks an injected language model to
score an output. `assayer.judges` holds the pieces Assayer owns; the first
metric built on them is `make_criteria_judge` in `assayer/metrics/judge.py`.[^judges]

# Judge Protocol

Any object with `complete(messages, schema=None) -> JudgeResponse` is a Judge.
`messages` are `{"role", "content"}` dictionaries; `schema` is the JSON Schema of
the reply, which a provider may ignore. `JudgeResponse(text, usage=None)` carries
the reply and, if known, a `TokenUsage`.

# Criteria judge

`make_criteria_judge(judge, name=, criteria=, evaluation_steps=, rubric=, level=, scale=, prompt=)`
judges the Case input and `final_output` of a Trajectory, or the `input` and
`output` of a Step. The Judge answers `{"score": int, "reason": str}`; the Score
is `(score - low) / (high - low)` for the `scale` (default `(1, 5)`, `(0, 1)` is
binary), the `reason` is its `comment`, and `prompt` (`id@version`) and
`prompt_hash` are in its `metadata`.[^criteria]

| Reply | Outcome |
|---|---|
| Valid, possibly in a code fence or with text around it | Score |
| Invalid JSON, a score that is not an integer within the scale, a missing or blank `reason` | One retry |
| Invalid twice, or the Judge raised | `EvaluationFailure`, never a 0 |

A Trajectory without `final_output` (or a Step without `output`) is an
`EvaluationFailure` before any call is made. A custom `Prompt` may use the
placeholders `$low`, `$high`, `$criteria`, `$evaluation_steps`, `$rubric`,
`$input` and `$output`; an unknown one raises at build time.

# Accounting

Every call goes through `call_judge`, which records it on the ledger that
`Metric.evaluate` opens. The outcome's `judge_calls` and `judge_usage` (retries and
failed attempts included) are added by the Runner to `Experiment.judge_calls` and
`Experiment.judge_usage`, never to the target's totals.[^tests]

[^judges]: Public API of the judges subpackage
[^criteria]: make_criteria_judge
[^tests]: Criteria judge tests through the Runner

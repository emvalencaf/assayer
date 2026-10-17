"""Judge-based metrics: a Judge scores an output against criteria given in a prompt."""

import json
from collections.abc import Mapping, Sequence
from string import Template
from typing import Any

from assayer.judges import (
    Judge,
    JudgeParseError,
    Prompt,
    call_judge,
    parse_verdict,
    verdict_schema,
)
from assayer.metrics.metric import Detailed, Metric, MetricLevel
from assayer.models import Case, Step, Trajectory

CRITERIA_PROMPT = Prompt(
    id="criteria",
    version="1",
    system=(
        "You are a strict, impartial evaluator. You judge one output against the criteria "
        "you are given, and nothing else.\n"
        "Reply with only a JSON object: "
        '{"score": <integer from $low to $high>, "reason": "<why, in one or two sentences>"}.\n'
        "$low is the worst and $high the best. The reason is mandatory."
    ),
    user=(
        "$criteria\n"
        "$evaluation_steps\n"
        "$rubric\n"
        "Input:\n$input\n\n"
        "Output:\n$output\n\n"
        "Score the output from $low to $high and explain why."
    ),
)
_PLACEHOLDERS = {
    "low",
    "high",
    "criteria",
    "evaluation_steps",
    "rubric",
    "input",
    "output",
}
_ATTEMPTS = 2  # one call, and one retry when the reply cannot be parsed


def make_criteria_judge(
    judge: Judge,
    name: str = "criteria",
    criteria: str | None = None,
    evaluation_steps: Sequence[str] | None = None,
    rubric: Mapping[int, str] | None = None,
    level: MetricLevel = "trajectory",
    scale: tuple[int, int] = (1, 5),
    prompt: Prompt | None = None,
) -> Metric:
    """Build a metric in which the Judge scores a Step or Trajectory against criteria.

    The Judge answers `{"score", "reason"}` with an integer within `scale`; the
    Score is that integer normalised to [0, 1], and the reason is its comment.
    A reply that does not parse is asked for once more; if the second one does not
    parse either, the metric emits an evaluation failure, never a 0. The prompt
    reference and hash are recorded in the Score's `metadata`.

    Args:
        judge: The Judge to ask.
        name: Name of the metric; becomes the name of its Scores.
        criteria: What a good output is.
        evaluation_steps: Steps the Judge follows to evaluate, in order.
        rubric: Meaning of each score, such as `{1: "wrong", 5: "right"}`.
        level: "trajectory" (judges the Case input and the final output) or "step"
            (judges the Step's input and output).
        scale: Lowest and highest score the Judge may give; `(0, 1)` is binary.
        prompt: Replaces the default prompt. It may use the placeholders `$low`,
            `$high`, `$criteria`, `$evaluation_steps`, `$rubric` and
            `$input`, `$output`.

    Returns:
        A judge-based Metric.

    Raises:
        ValueError: If neither criteria nor evaluation_steps is given, level is not
            "step" or "trajectory", scale is not an increasing pair, a rubric score is
            outside it, or the prompt uses an unknown placeholder.
    """
    if not (criteria and criteria.strip()) and not evaluation_steps:
        raise ValueError("a criteria judge needs criteria or evaluation_steps")
    if level not in ("step", "trajectory"):
        raise ValueError("a criteria judge scores a 'step' or a 'trajectory'")
    low, high = scale
    if low >= high:
        raise ValueError("scale must be an increasing (low, high) pair")
    if rubric and any(not low <= s <= high for s in rubric):
        raise ValueError(f"rubric scores must be within the scale {scale}")
    prompt = prompt or CRITERIA_PROMPT
    unknown = {
        i for text in (prompt.system, prompt.user) for i in Template(text).get_identifiers()
    } - _PLACEHOLDERS
    if unknown:
        raise ValueError(f"prompt uses unknown placeholders: {sorted(unknown)}")

    fixed = {
        "low": str(low),
        "high": str(high),
        "criteria": f"Criteria: {criteria.strip()}" if criteria and criteria.strip() else "",
        "evaluation_steps": _numbered("Evaluation steps", evaluation_steps),
        "rubric": _rubric(rubric),
    }
    schema = verdict_schema(low, high)

    def score(subject: Step | Trajectory, case: Case | None) -> Detailed:
        if isinstance(subject, Trajectory):
            input_, output = case.input if case else None, subject.final_output
        else:
            input_, output = subject.input, subject.output
        messages = prompt.render(
            **fixed,
            input=_text(input_),
            output=_text(output),
        )
        verdict = None
        for _ in range(_ATTEMPTS):
            response = call_judge(judge, messages, schema)
            try:
                verdict = parse_verdict(response.text, low, high)
                break
            except JudgeParseError as exc:
                error = exc
        if verdict is None:
            raise JudgeParseError(f"invalid Judge reply after {_ATTEMPTS} attempts: {error}")
        return Detailed(
            value=(verdict.score - low) / (high - low),
            comment=verdict.reason,
            metadata={
                "judge_score": verdict.score,
                "prompt": prompt.ref,
                "prompt_hash": prompt.hash,
            },
        )

    return Metric(
        name=name,
        level=level,
        fn=score,
        requires=("final_output",) if level == "trajectory" else ("output",),
        kind="judge",
    )


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def _numbered(title: str, items: Sequence[str] | None) -> str:
    if not items:
        return ""
    return title + ":\n" + "\n".join(f"{n}. {item}" for n, item in enumerate(items, 1))


def _rubric(rubric: Mapping[int, str] | None) -> str:
    if not rubric:
        return ""
    return "Rubric:\n" + "\n".join(f"{score}: {rubric[score]}" for score in sorted(rubric))

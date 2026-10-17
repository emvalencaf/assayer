"""Judge-based metrics: a Judge scores an output against criteria given in a prompt."""

import json
from collections.abc import Callable, Mapping, Sequence
from string import Template
from typing import Any, TypeVar

from assayer.judges import (
    Judge,
    JudgeParseError,
    Prompt,
    call_judge,
    claim_verdicts_schema,
    claims_schema,
    parse_claim_verdicts,
    parse_claims,
    parse_verdict,
    verdict_schema,
)
from assayer.metrics.metric import Detailed, Metric, MetricLevel
from assayer.metrics.retrieved import retrieved_items
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
GOAL_SUCCESS_PROMPT = Prompt(
    id="goal_success",
    version="1",
    system=(
        "You are a strict, impartial evaluator. You decide whether an agent achieved the goal "
        "the user gave it, and nothing else.\n"
        "Reply with only a JSON object: "
        '{"score": <0 or 1>, "reason": "<why, in one or two sentences>"}.\n'
        "1 means the goal was achieved, 0 that it was not. The reason is mandatory."
    ),
    user=(
        "Goal (the user's request):\n$input\n\n"
        "${expected_outcome}"
        "Agent's final answer:\n$output\n\n"
        "Was the goal achieved? Score 1 or 0 and explain why."
    ),
)
CLAIMS_PROMPT = Prompt(
    id="faithfulness_claims",
    version="1",
    system=(
        "You split an answer into its atomic factual claims: short, self-contained statements, "
        "each stating one fact, with pronouns replaced by what they refer to.\n"
        'Reply with only a JSON object: {"claims": ["<claim>", ...]}.'
    ),
    user="Question:\n$input\n\nAnswer:\n$output\n\nList the claims of the answer.",
)
CLAIM_VERDICTS_PROMPT = Prompt(
    id="faithfulness_verdicts",
    version="1",
    system=(
        "You are a strict, impartial evaluator. For each claim you decide whether the context "
        "supports it: a claim is supported only when the context states it or it follows "
        "directly from it. Use nothing but the context.\n"
        'Reply with only a JSON object: {"verdicts": [{"supported": <true or false>, '
        '"reason": "<why, in one sentence>"}, ...]}, one verdict per claim, in the same order.'
    ),
    user="Context:\n$context\n\nClaims:\n$claims\n\nGive one verdict per claim.",
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
T = TypeVar("T")
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
        verdict = _ask(judge, messages, schema, lambda text: parse_verdict(text, low, high))
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


def _ask(
    judge: Judge, messages: list[dict[str, str]], schema: dict, parse: Callable[[str], T]
) -> T:
    """Call the Judge and parse the reply, asking once more when it does not parse.

    Raises:
        JudgeParseError: If neither reply parses.
    """
    for _ in range(_ATTEMPTS):
        response = call_judge(judge, messages, schema)
        try:
            return parse(response.text)
        except JudgeParseError as exc:
            error = exc
    raise JudgeParseError(f"invalid Judge reply after {_ATTEMPTS} attempts: {error}")


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


def make_goal_success(judge: Judge, name: str = "goal_success") -> Metric:
    """Build the metric for whether the agent achieved the goal it was given.

    The Judge answers 1 (achieved) or 0 (not), so the Score is binary, with its reason
    as the comment. It judges the Case input and the Trajectory's `final_output`; when
    the Case has an `expected_outcome` the Judge compares the answer to it (reference-based),
    otherwise it decides from the request alone. Which one was used is in the Score's
    `metadata["reference"]`, with the prompt reference and hash. A reply that does not
    parse is asked for once more, then it is an evaluation failure, never a 0.

    Args:
        judge: The Judge to ask.
        name: Name of the metric; becomes the name of its Scores.

    Returns:
        A judge-based trajectory-level Metric.
    """

    def goal_success(trajectory: Trajectory, case: Case | None) -> Detailed:
        expected = case.expected_outcome if case else None
        messages = GOAL_SUCCESS_PROMPT.render(
            input=_text(case.input if case else None),
            output=_text(trajectory.final_output),
            expected_outcome=(
                "" if expected is None else f"Expected outcome:\n{_text(expected)}\n\n"
            ),
        )
        verdict = _ask(judge, messages, verdict_schema(0, 1), lambda t: parse_verdict(t, 0, 1))
        return Detailed(
            value=verdict.score,
            comment=verdict.reason,
            metadata={
                "reference": expected is not None,
                "prompt": GOAL_SUCCESS_PROMPT.ref,
                "prompt_hash": GOAL_SUCCESS_PROMPT.hash,
            },
        )

    return Metric(
        name=name, level="trajectory", fn=goal_success, requires=("final_output",), kind="judge"
    )


def make_faithfulness(judge: Judge, name: str = "faithfulness") -> Metric:
    """Build the metric for the share of the answer's claims the retrieved context supports.

    Two Judge calls: the first splits the Trajectory's `final_output` into claims, the
    second says for each whether the retrieved context supports it. The Score is the
    supported claims over all of them; both counts, each claim's verdict and the prompts
    are in the Score's `metadata`. The context is the items of the Trajectory's
    `retrieval` Steps. No retrieved context, or an answer with no claim, is an
    evaluation failure, never a 0 or a 1. Each reply that does not parse is asked
    for once more.

    Args:
        judge: The Judge to ask.
        name: Name of the metric; becomes the name of its Scores.

    Returns:
        A judge-based trajectory-level Metric.
    """

    def faithfulness(trajectory: Trajectory, case: Case | None) -> Detailed:
        texts = [item.text for item in retrieved_items(trajectory) if item.text]
        if not texts:
            raise ValueError("no retrieved context to check the claims against")
        input_, output = _text(case.input if case else None), _text(trajectory.final_output)
        claims = _ask(
            judge,
            CLAIMS_PROMPT.render(input=input_, output=output),
            claims_schema(),
            parse_claims,
        )
        if not claims:
            raise ValueError("the output has no claims to check")
        verdicts = _ask(
            judge,
            CLAIM_VERDICTS_PROMPT.render(
                context="\n\n".join(f"[{n}] {text}" for n, text in enumerate(texts, 1)),
                claims="\n".join(f"{n}. {claim}" for n, claim in enumerate(claims, 1)),
            ),
            claim_verdicts_schema(),
            lambda text: parse_claim_verdicts(text, claims),
        )
        supported = sum(v.supported for v in verdicts)
        return Detailed(
            value=supported / len(claims),
            comment=f"{supported} of {len(claims)} claims supported",
            metadata={
                "supported_claims": supported,
                "total_claims": len(claims),
                "claims": [
                    {"claim": v.claim, "supported": v.supported, "reason": v.reason}
                    for v in verdicts
                ],
                "prompts": {p.ref: p.hash for p in (CLAIMS_PROMPT, CLAIM_VERDICTS_PROMPT)},
            },
        )

    return Metric(
        name=name, level="trajectory", fn=faithfulness, requires=("final_output",), kind="judge"
    )

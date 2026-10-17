"""Tolerant parsing of the Judge's `score` + `reason` reply."""

import json
import re
from dataclasses import dataclass
from typing import Any

_FENCE = re.compile(r"^```[\w-]*\s*\n?(.*?)\n?```\s*$", re.DOTALL)


class JudgeParseError(ValueError):
    """The Judge's reply was not a valid verdict."""


@dataclass(frozen=True)
class Verdict:
    """A parsed Judge verdict.

    Args:
        score: The Judge's integer score, within its scale.
        reason: Why the Judge gave it; never empty.
    """

    score: int
    reason: str


def verdict_schema(low: int, high: int) -> dict[str, Any]:
    """JSON Schema of the reply Assayer asks for.

    Args:
        low: Lowest allowed score.
        high: Highest allowed score.

    Returns:
        A JSON Schema with an integer `score` and a mandatory `reason`.
    """
    return {
        "type": "object",
        "properties": {
            "score": {"type": "integer", "minimum": low, "maximum": high},
            "reason": {"type": "string", "minLength": 1},
        },
        "required": ["score", "reason"],
    }


def parse_verdict(text: str, low: int, high: int) -> Verdict:
    """Parse the Judge's reply.

    Code fences around the JSON are stripped, and text around a single JSON
    object is ignored.

    Args:
        text: The raw reply.
        low: Lowest allowed score.
        high: Highest allowed score.

    Returns:
        The verdict.

    Raises:
        JudgeParseError: If the reply is not JSON, lacks an integer `score`
            within [low, high] or a non-blank `reason`.
    """
    body = text.strip()
    if match := _FENCE.match(body):
        body = match.group(1).strip()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        start, end = body.find("{"), body.rfind("}")
        try:
            data = json.loads(body[start : end + 1]) if 0 <= start < end else None
        except json.JSONDecodeError:
            data = None
        if data is None:
            raise JudgeParseError(f"reply is not valid JSON: {text[:200]!r}") from None
    if not isinstance(data, dict):
        raise JudgeParseError("reply must be a JSON object with 'score' and 'reason'")
    score, reason = data.get("score"), data.get("reason")
    if isinstance(score, float) and score.is_integer():
        score = int(score)
    if isinstance(score, bool) or not isinstance(score, int):
        raise JudgeParseError(f"'score' must be an integer, got {score!r}")
    if not low <= score <= high:
        raise JudgeParseError(f"'score' must be between {low} and {high}, got {score}")
    if not isinstance(reason, str) or not reason.strip():
        raise JudgeParseError("'reason' is mandatory and must be a non-empty string")
    return Verdict(score=score, reason=reason.strip())

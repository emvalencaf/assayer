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
    data = _load_object(text, "a JSON object with 'score' and 'reason'")
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


@dataclass(frozen=True)
class ClaimVerdict:
    """The Judge's verdict on one claim.

    Args:
        claim: The claim that was checked.
        supported: Whether the context supports it.
        reason: Why, when the Judge said.
    """

    claim: str
    supported: bool
    reason: str | None = None


def claims_schema() -> dict[str, Any]:
    """JSON Schema of the reply that lists the claims of a text.

    Returns:
        A JSON Schema with an array of strings `claims`.
    """
    return {
        "type": "object",
        "properties": {"claims": {"type": "array", "items": {"type": "string"}}},
        "required": ["claims"],
    }


def parse_claims(text: str) -> list[str]:
    """Parse the Judge's list of claims.

    Args:
        text: The raw reply, `{"claims": ["...", ...]}`.

    Returns:
        The non-blank claims, trimmed.

    Raises:
        JudgeParseError: If the reply is not JSON or `claims` is not a list of strings.
    """
    data = _load_object(text, "a JSON object with 'claims'")
    claims = data.get("claims")
    if not isinstance(claims, list) or not all(isinstance(c, str) for c in claims):
        raise JudgeParseError("'claims' must be a list of strings")
    return [c.strip() for c in claims if c.strip()]


def claim_verdicts_schema() -> dict[str, Any]:
    """JSON Schema of the reply that checks each claim against a context.

    Returns:
        A JSON Schema with an array `verdicts` of `{"supported", "reason"}`.
    """
    return {
        "type": "object",
        "properties": {
            "verdicts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "supported": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "required": ["supported"],
                },
            }
        },
        "required": ["verdicts"],
    }


def parse_claim_verdicts(text: str, claims: list[str]) -> list[ClaimVerdict]:
    """Parse the Judge's verdict on each claim, in the order the claims were given.

    Args:
        text: The raw reply, `{"verdicts": [{"supported": true, "reason": "..."}, ...]}`.
        claims: The claims that were checked.

    Returns:
        One verdict per claim.

    Raises:
        JudgeParseError: If the reply is not JSON, has not exactly one verdict per
            claim, or a `supported` is not a boolean.
    """
    data = _load_object(text, "a JSON object with 'verdicts'")
    verdicts = data.get("verdicts")
    if not isinstance(verdicts, list) or len(verdicts) != len(claims):
        raise JudgeParseError(
            f"'verdicts' must be a list with one verdict per claim ({len(claims)})"
        )
    parsed = []
    for claim, item in zip(claims, verdicts, strict=True):
        if not isinstance(item, dict) or not isinstance(item.get("supported"), bool):
            raise JudgeParseError("each verdict must be an object with a boolean 'supported'")
        reason = item.get("reason")
        reason = reason.strip() if isinstance(reason, str) else None
        parsed.append(ClaimVerdict(claim, item["supported"], reason))
    return parsed


def _load_object(text: str, expected: str) -> dict[str, Any]:
    """The JSON object in a reply, tolerating code fences and text around it."""
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
        raise JudgeParseError(f"reply must be {expected}")
    return data

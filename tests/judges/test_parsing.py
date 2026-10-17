"""Tests for the Judge reply parser, the Prompt and the ledger."""

import pytest

from assayer.judges import (
    ClaimVerdict,
    JudgeParseError,
    JudgeResponse,
    Prompt,
    call_judge,
    parse_claim_verdicts,
    parse_claims,
    parse_verdict,
    track_judge,
)
from assayer.models import TokenUsage


def test_parse_verdict_strips_fences_and_trims_the_reason():
    verdict = parse_verdict('```json\n{"score": 2, "reason": " why "}\n```', 1, 5)

    assert (verdict.score, verdict.reason) == (2, "why")


@pytest.mark.parametrize("text", ["", "{", '{"score": 0, "reason": "x"}', '{"reason": "x"}'])
def test_parse_verdict_rejects_invalid_replies(text):
    with pytest.raises(JudgeParseError):
        parse_verdict(text, 1, 5)


def test_prompt_ref_and_hash():
    prompt = Prompt("p", "2", "s $low", "u $input")

    assert prompt.ref == "p@2"
    assert prompt.hash == Prompt("p", "2", "s $low", "u $input").hash
    assert prompt.hash != Prompt("p", "2", "s $high", "u $input").hash


def test_prompt_render_fills_placeholders():
    messages = Prompt("p", "1", "s $low", "u $input").render(low="1", input="q")

    assert [m["content"] for m in messages] == ["s 1", "u q"]


def test_prompt_rejects_blank_identity():
    with pytest.raises(ValueError):
        Prompt(" ", "1", "s", "u")


def test_ledger_counts_calls_and_sums_usage_only_inside_the_block():
    class Judge:
        def complete(self, messages, schema=None):
            return JudgeResponse("x", TokenUsage(3, 1, None))

    call_judge(Judge(), [])  # outside any block: not recorded
    with track_judge() as ledger:
        call_judge(Judge(), [])
        call_judge(Judge(), [])

    assert ledger.calls == 2
    assert ledger.usage == TokenUsage(6, 2, None)


def test_parse_claims_trims_and_drops_blank_claims():
    assert parse_claims('```json\n{"claims": [" a ", "", "b"]}\n```') == ["a", "b"]


@pytest.mark.parametrize("text", ["", '{"claims": "a"}', '{"claims": [1]}', "[]"])
def test_parse_claims_rejects_invalid_replies(text):
    with pytest.raises(JudgeParseError):
        parse_claims(text)


def test_parse_claim_verdicts_pairs_each_claim_with_its_verdict():
    verdicts = parse_claim_verdicts(
        '{"verdicts": [{"supported": true, "reason": " ok "}, {"supported": false}]}', ["a", "b"]
    )

    assert verdicts == [ClaimVerdict("a", True, "ok"), ClaimVerdict("b", False, None)]


@pytest.mark.parametrize(
    "text",
    [
        '{"verdicts": [{"supported": true}]}',  # one verdict short
        '{"verdicts": [{"supported": "yes"}, {"supported": true}]}',
        '{"verdicts": [{"reason": "x"}, {"supported": true}]}',
        '{"verdicts": "no"}',
    ],
)
def test_parse_claim_verdicts_rejects_invalid_replies(text):
    with pytest.raises(JudgeParseError):
        parse_claim_verdicts(text, ["a", "b"])

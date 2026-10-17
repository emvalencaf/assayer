"""The Judge: the injected language model behind judge-based metrics.

`LangChainJudge` is importable from here too; it is loaded on first access and needs
`assayer[langchain]`.
"""

import importlib

from assayer.judges.judge import Judge, JudgeResponse
from assayer.judges.ledger import JudgeLedger, call_judge, track_judge
from assayer.judges.parsing import (
    ClaimVerdict,
    JudgeParseError,
    Verdict,
    claim_verdicts_schema,
    claims_schema,
    parse_claim_verdicts,
    parse_claims,
    parse_verdict,
    verdict_schema,
)
from assayer.judges.prompt import Prompt


def __getattr__(name: str) -> object:
    """Load `LangChainJudge` on first use, so that the core imports without its extra."""
    if name == "LangChainJudge":
        return importlib.import_module("assayer.judges.langchain_judge").LangChainJudge
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), "LangChainJudge"])


__all__ = [
    "ClaimVerdict",
    "Judge",
    "JudgeLedger",
    "JudgeParseError",
    "JudgeResponse",
    "Prompt",
    "Verdict",
    "call_judge",
    "claim_verdicts_schema",
    "claims_schema",
    "parse_claim_verdicts",
    "parse_claims",
    "parse_verdict",
    "track_judge",
    "verdict_schema",
]

"""The Judge: the injected language model behind judge-based metrics.

`LangChainJudge` is importable from here too; it is loaded on first access and needs
`llm-assayer-eval[langchain]`.
"""

from assayer._extras import lazy_exports
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

__getattr__, __dir__ = lazy_exports(__name__, {"LangChainJudge": "assayer.judges.langchain_judge"})

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

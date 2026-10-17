"""Accounting of the Judge's calls and tokens, kept apart from the target's cost."""

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any

from assayer.judges.judge import Judge, JudgeResponse
from assayer.models import TokenUsage, add_usage


@dataclass
class JudgeLedger:
    """The Judge calls made, and their tokens, while it was the current ledger.

    Args:
        calls: Number of Judge calls that returned.
        usage: Summed token usage of those calls; None until one reports usage.
    """

    calls: int = 0
    usage: TokenUsage | None = None

    def record(self, response: JudgeResponse) -> None:
        """Count one call and add its usage.

        Args:
            response: What the Judge returned.
        """
        self.calls += 1
        self.usage = add_usage(self.usage, response.usage)


_current: ContextVar[JudgeLedger | None] = ContextVar("assayer_judge_ledger", default=None)


@contextmanager
def track_judge() -> Iterator[JudgeLedger]:
    """Collect every `call_judge` made inside the block, failures included.

    Yields:
        The ledger the calls are recorded on.
    """
    ledger = JudgeLedger()
    token = _current.set(ledger)
    try:
        yield ledger
    finally:
        _current.reset(token)


def call_judge(
    judge: Judge, messages: list[dict[str, str]], schema: dict[str, Any] | None = None
) -> JudgeResponse:
    """Call the Judge and record the call on the current ledger, if any.

    Args:
        judge: The Judge to ask.
        messages: Chat messages to send.
        schema: JSON Schema of the reply, if any.

    Returns:
        The Judge's response.
    """
    response = judge.complete(messages, schema)
    ledger = _current.get()
    if ledger is not None:
        ledger.record(response)
    return response

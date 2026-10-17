"""The Judge contract: the minimal, provider-neutral way to ask a language model."""

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from assayer.models import TokenUsage


@dataclass
class JudgeResponse:
    """What a Judge answered to one call.

    Args:
        text: The raw text of the reply.
        usage: Tokens the call consumed, when the provider reports them.
    """

    text: str
    usage: TokenUsage | None = None


@runtime_checkable
class Judge(Protocol):
    """A language model that answers a list of chat messages, synchronously.

    Any object with this method is a Judge; Assayer is not tied to a provider.
    """

    def complete(
        self, messages: list[dict[str, str]], schema: dict[str, Any] | None = None
    ) -> JudgeResponse:
        """Answer one request.

        Args:
            messages: Chat messages, each a `{"role", "content"}` dictionary.
            schema: JSON Schema of the reply, for providers that can enforce it;
                a Judge may ignore it, since Assayer parses the text anyway.

        Returns:
            The reply text and, if known, its token usage.
        """
        ...

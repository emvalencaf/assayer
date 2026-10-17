"""LangChainJudge: any LangChain chat model, injected as the Judge."""

from typing import Any

from assayer._extras import missing_extra
from assayer.judges.judge import JudgeResponse
from assayer.models import TokenUsage

try:
    from langchain_core.language_models.chat_models import BaseChatModel
except ImportError as exc:
    raise missing_extra("langchain", "LangChainJudge") from exc


class LangChainJudge:
    """A Judge backed by a LangChain chat model.

    The model's reply text becomes the `JudgeResponse` text, and its `usage_metadata`, when the
    provider reports it, becomes the usage (with no cost: LangChain does not price calls). The
    `schema` is ignored, since Assayer parses the text anyway.

    Args:
        model: The LangChain chat model to ask, such as `ChatOpenAI()` or `ChatAnthropic()`.
    """

    def __init__(self, model: BaseChatModel) -> None:
        self._model = model

    def complete(
        self, messages: list[dict[str, str]], schema: dict[str, Any] | None = None
    ) -> JudgeResponse:
        """Ask the model.

        Args:
            messages: Chat messages, each a `{"role", "content"}` dictionary.
            schema: Ignored.

        Returns:
            The reply text and, if the model reports it, its token usage.
        """
        reply = self._model.invoke([(m["role"], m["content"]) for m in messages])
        return JudgeResponse(text=_text(reply.content), usage=_usage(reply.usage_metadata))


def _text(content: str | list[str | dict[str, Any]]) -> str:
    """Join the text of a reply that may come as content blocks."""
    if isinstance(content, str):
        return content
    parts = [
        block if isinstance(block, str) else block.get("text", "")
        for block in content
        if isinstance(block, str) or block.get("type", "text") == "text"
    ]
    return "".join(parts)


def _usage(metadata: Any) -> TokenUsage | None:
    """Read the token counts LangChain reports, if any."""
    if not metadata:
        return None
    return TokenUsage(
        input_tokens=metadata.get("input_tokens", 0),
        output_tokens=metadata.get("output_tokens", 0),
        cost_usd=None,
    )

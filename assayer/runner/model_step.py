"""Building a model Step from the reply of a LangChain-style chat model."""

from typing import Any

from assayer.models import Step, TokenUsage


def model_step(
    response: Any, *, model: str | None = None, input: Any = None, name: str | None = None
) -> Step:
    """Wrap a chat model's reply into a model Step that carries its token usage.

    Reads `content` as the output and `usage_metadata` (`input_tokens`, `output_tokens`), as
    LangChain messages expose them, by attribute, so no extra is needed. A reply without
    `usage_metadata` gives a Step with no usage, which differs from zero tokens. The cost is
    left to `Runner(pricing=...)`.

    Args:
        response: The reply, such as a LangChain `AIMessage`.
        model: Name of the model, recorded on the Step.
        input: What the model received, recorded on the Step.
        name: Name of the Step.

    Returns:
        A model Step; put it in a `Trajectory` returned by the target.
    """
    metadata = getattr(response, "usage_metadata", None)
    usage = (
        TokenUsage(
            input_tokens=int(metadata.get("input_tokens", 0)),
            output_tokens=int(metadata.get("output_tokens", 0)),
            cost_usd=None,
        )
        if metadata
        else None
    )
    return Step(
        kind="model",
        name=name,
        model=model,
        input=input,
        output=getattr(response, "content", response),
        usage=usage,
    )

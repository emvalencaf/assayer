from dataclasses import dataclass
from typing import Any


@dataclass
class Case:
    """One input of a Dataset, with an optional reference to compare against.

    Args:
        input: What the target receives.
        id: Identifier of the Case.
        expected_output: Expected final answer.
        expected_tool_calls: Expected tool calls.
        expected_steps: Expected sequence of Steps.
        expected_outcome: Expected outcome, described in words.
        expected_state: Expected end state.
        reference_contexts: Reference contexts for retrieval metrics.
        reference_context_ids: Ids of the reference contexts.
    """

    input: Any
    id: str | None = None
    expected_output: Any = None
    expected_tool_calls: list[Any] | None = None
    expected_steps: list[Any] | None = None
    expected_outcome: Any = None
    expected_state: Any = None
    reference_contexts: list[str] | None = None
    reference_context_ids: list[str] | None = None

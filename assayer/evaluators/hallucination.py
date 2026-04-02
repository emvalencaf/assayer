"""Hallucination evaluator components."""

import hashlib


DEFAULT_JUDGE_SYSTEM_PROMPT: str = """\
You are an expert evaluator assessing the quality and faithfulness of an AI assistant's response.

Given the following:
- Context (source material the assistant had access to)
- Question or input
- Assistant's response

Rate the response on a scale from 0.0 to 1.0, where:
  1.0 = fully faithful, accurate, and relevant
  0.0 = completely unfaithful, hallucinated, or irrelevant

Respond with ONLY a single float number between 0.0 and 1.0. No explanation.
"""


def hash_prompt(prompt: str) -> str:
    """Compute the SHA-256 hex digest of a prompt string.

    Args:
        prompt: The prompt text to hash.

    Returns:
        A 64-character lowercase hex string.

    Raises:
        ValueError: If prompt is empty or contains only whitespace.
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty or whitespace-only")

    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
---
prd: assayer-core
spec: hallucination-evaluator
created: 2026-03-30
---

# Design: Hallucination Evaluator

## Prompt hashing

All prompts (default and custom) are hashed using SHA-256 on the UTF-8 encoded string:

```python
import hashlib

def hash_prompt(prompt: str) -> str:
    """Compute the SHA-256 hex digest of a prompt string.

    Args:
        prompt: The prompt text to hash.

    Returns:
        A 64-character lowercase hex string.
    """
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()
```

The default system prompt constant must be stored in the module so its hash is stable across runs:

```python
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
```

## FaithfulnessEvaluator

```python
class FaithfulnessEvaluator(BaseEvaluator):
    def __init__(
        self,
        field_name: str,
        threshold: float = 0.5,
        model_name: str = "cross-encoder/nli-deberta-v3-small",
    ) -> None: ...

    def evaluate(
        self,
        prediction: str,
        reference: str,
        **kwargs: Any,
    ) -> FieldEvaluation: ...
```

**Score computation:**
Uses the NLI model in entailment mode:
- `score = P(entailment | premise=reference, hypothesis=prediction)`
- Values in [0, 1] from the model softmax

Fallback (when model unavailable): normalized token overlap (Jaccard similarity on word sets).

**FieldEvaluation output:**
```python
FieldEvaluation(
    field_name=self.field_name,
    evaluator_method="faithfulness",
    expected_value=reference,
    obtained_value=prediction,
    score=faithfulness_score,
    prompt_hash=None,
    metadata={
        "is_hallucination": faithfulness_score < self.threshold,
        "method": "faithfulness",
        "threshold": self.threshold,
    }
)
```

## LLMJudgeEvaluator

```python
class LLMJudgeEvaluator(BaseEvaluator):
    def __init__(
        self,
        field_name: str,
        judge_model: BaseChatModel,          # LangChain ChatModel
        system_prompt: str | None = None,    # None → use DEFAULT_JUDGE_SYSTEM_PROMPT
    ) -> None:
        self._prompt = system_prompt or DEFAULT_JUDGE_SYSTEM_PROMPT
        self._prompt_hash = hash_prompt(self._prompt)
        ...

    def evaluate(
        self,
        prediction: str,
        reference: str | None = None,
        **kwargs: Any,
    ) -> FieldEvaluation: ...
```

**Score parsing:**
The judge LLM is expected to return a single float in its response text.
```python
def _parse_score(response_text: str) -> float:
    """Extract a float score from the judge's response.

    Args:
        response_text: Raw text returned by the judge LLM.

    Returns:
        A float in [0, 1].

    Raises:
        ValueError: If no valid float can be extracted.
    """
    import re
    matches = re.findall(r"\b(0(?:\.\d+)?|1(?:\.0+)?)\b", response_text.strip())
    if not matches:
        raise ValueError(f"Could not parse score from judge response: {response_text!r}")
    return float(matches[0])
```

**FieldEvaluation output:**
```python
FieldEvaluation(
    field_name=self.field_name,
    evaluator_method="llm_judge",
    expected_value=reference,
    obtained_value=prediction,
    score=parsed_score,
    prompt_hash=self._prompt_hash,
    metadata={
        "judge_model": judge_model.__class__.__name__,
        "prompt_hash": self._prompt_hash,
    }
)
```

## File layout

```
assayer/
  evaluators/
    hallucination.py   # FaithfulnessEvaluator, LLMJudgeEvaluator, hash_prompt,
                       # DEFAULT_JUDGE_SYSTEM_PROMPT, register_hallucination_evaluators()
```

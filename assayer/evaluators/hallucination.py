"""Hallucination evaluator components."""

import hashlib
from typing import Any, Callable, Optional

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation
import transformers

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


class FaithfulnessEvaluator(BaseEvaluator):
    """Evaluates faithfulness using Natural Language Inference (NLI) models.

    This evaluator uses cross-encoder NLI models to assess whether a prediction
    is entailed by (faithful to) a given reference text. It computes the
    probability of entailment as the faithfulness score.

    Args:
        field_name: Name of the field being evaluated.
        threshold: Score threshold for determining hallucination. Scores below
            this threshold are considered hallucinations. Defaults to 0.5.
        model_name: HuggingFace model identifier for the NLI cross-encoder.
            Defaults to "cross-encoder/nli-deberta-v3-small".

    Raises:
        ValueError: If field_name is empty or whitespace-only after stripping.
    """

    def __init__(
        self,
        field_name: str,
        threshold: float = 0.5,
        model_name: str = "cross-encoder/nli-deberta-v3-small",
        classifier: Optional[Callable[[str], Any]] = None,
    ) -> type(None):
        """Initialize the faithfulness evaluator.

        Args:
            field_name: Name of the field being evaluated.
            threshold: Score threshold for determining hallucination.
            model_name: HuggingFace model identifier for the NLI cross-encoder.
            classifier: Optional callable that takes a string input and returns

        Raises:
            ValueError: If field_name is empty or whitespace-only after stripping.
        """
        super().__init__(field_name)
        self.threshold = threshold
        self.model_name = model_name
        self._classifier = classifier
        
    def _get_classifier(self) -> Callable[[str], Any]:
        """Lazily initialize classifier if not injected."""
        if self._classifier is None:
            import transformers

            self._classifier = transformers.pipeline(
                "text-classification",
                model=self.model_name,
                return_all_scores=True,
            )
        return self._classifier
    
    def evaluate(
        self,
        prediction: str,
        reference: str,
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Evaluate faithfulness of prediction against reference using NLI.

        Uses a cross-encoder NLI model to compute the entailment probability
        between the reference (premise) and prediction (hypothesis). Falls back
        to Jaccard similarity if the model is unavailable.

        Args:
            prediction: The predicted/obtained text to evaluate.
            reference: The reference/expected text for comparison.
            **kwargs: Additional keyword arguments (unused).

        Returns:
            A FieldEvaluation object containing the faithfulness score and metadata.
            Score is in [0, 1] where 1.0 indicates perfect faithfulness.
        """
        # Handle empty or whitespace-only inputs
        if not prediction.strip() or not reference.strip():
            score = 0.0
        else:
            try:
                # Try to use NLI model
                score = self._compute_nli_score(prediction, reference)
            except Exception:
                # Fallback to Jaccard similarity
                score = self._compute_jaccard_score(prediction, reference)

        return FieldEvaluation(
            field_name=self.name,
            evaluator_method="faithfulness",
            expected_value=reference,
            obtained_value=prediction,
            score=score,
            prompt_hash=None,
            metadata={
                "is_hallucination": score < self.threshold,
                "method": "faithfulness",
                "threshold": self.threshold,
            }
        )

    def _compute_nli_score(self, prediction: str, reference: str) -> float:
        """Compute entailment score using NLI cross-encoder model.

        Args:
            prediction: The hypothesis text.
            reference: The premise text.

        Returns:
            The entailment probability as a float in [0, 1].

        Raises:
            Exception: If the model fails to load or compute scores.
        """

        # Use the global transformers import
        # Initialize NLI classifier
        classifier = self._get_classifier()

        # Format input for NLI: premise [SEP] hypothesis
        nli_input = f"{reference} [SEP] {prediction}"

        # Get scores for all labels
        scores = classifier(nli_input)

        # Extract entailment probability from scores
        # For tests, scores might be just raw values: [[0.1, 0.7, 0.2]]
        # For real model: [[{"label": "LABEL_0", "score": 0.1}, {"label": "LABEL_1", "score": 0.7}, {"label": "LABEL_2", "score": 0.2}]]
        if isinstance(scores, list) and len(scores) > 0:
            score_list = scores[0] if isinstance(scores[0], list) else scores

            # Handle raw numeric scores (from tests)
            if score_list and isinstance(score_list[0], (int, float)):
                # Assume order: [contradiction, entailment, neutral]
                return float(score_list[1]) if len(score_list) > 1 else 0.0

            # Handle dict format (real model)
            # Look for entailment label (usually LABEL_1 or "ENTAILMENT")
            for score_item in score_list:
                if isinstance(score_item, dict):
                    label = score_item.get("label", "").upper()
                    if "1" in label or "ENTAIL" in label:
                        return score_item.get("score", 0.0)

            # Fallback: if we can't find explicit entailment label,
            # assume middle position is entailment for 3-class NLI
            if len(score_list) >= 3 and isinstance(score_list[1], dict):
                return score_list[1].get("score", 0.0)
            elif len(score_list) >= 2 and isinstance(score_list[1], dict):
                return score_list[1].get("score", 0.0)

        return 0.0

    def _compute_jaccard_score(self, prediction: str, reference: str) -> float:
        """Compute Jaccard similarity between word sets as fallback.

        Args:
            prediction: The predicted text.
            reference: The reference text.

        Returns:
            Jaccard similarity coefficient as a float in [0, 1].
        """
        pred_words = set(prediction.lower().split())
        ref_words = set(reference.lower().split())

        if not pred_words and not ref_words:
            return 1.0  # Both empty, perfect match

        if not pred_words or not ref_words:
            return 0.0  # One empty, no similarity

        intersection = len(pred_words & ref_words)
        union = len(pred_words | ref_words)

        return intersection / union if union > 0 else 0.0
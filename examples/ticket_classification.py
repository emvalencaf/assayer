"""Example 2: Structured output evaluation with a custom evaluator and custom metric.

Scenario: An LLM classifies customer support tickets and returns structured JSON:
    {"category": "billing" | "technical" | "general", "confidence": float}

We define:
- CategoryEvaluator  — a custom BaseEvaluator that checks per-example category match.
- category_accuracy  — a custom metric that aggregates accuracy across all examples.

Both are registered in their respective registries and wired into EvaluationPipeline.

Run:
    python examples/ticket_classification.py
"""

from typing import Any

from assayer.evaluators.base import BaseEvaluator
from assayer.models import FieldEvaluation
from assayer.registries.evaluator_registry import EvaluatorRegistry
from assayer.registries.metric_registry import MetricRegistry
from assayer.runner.pipeline import EvaluationPipeline

# Custom evaluator: exact match on the "category" field


class CategoryEvaluator(BaseEvaluator):
    """Evaluates whether the predicted category matches the expected category exactly.

    Args:
        name: Evaluator name used for registration.
        field_name: Output field name being evaluated (unused here, inherited by convention).
    """

    def __init__(self, name: str, field_name: str = "") -> None:
        """Initialize the CategoryEvaluator.

        Args:
            name: Evaluator name.
            field_name: Field name (accepted for registry compatibility, not used).
        """
        super().__init__(name)

    def evaluate(
        self,
        prediction: Any,
        reference: Any,
        **kwargs: Any,
    ) -> FieldEvaluation:
        """Score prediction as 1.0 if it exactly matches reference, else 0.0.

        Args:
            prediction: Predicted category string.
            reference: Expected category string.
            **kwargs: Unused.

        Returns:
            FieldEvaluation with score 1.0 (match) or 0.0 (mismatch).
        """
        score = 1.0 if prediction == reference else 0.0
        return FieldEvaluation(
            field_name=self.name,
            evaluator_method="exact_match",
            expected_value=reference,
            obtained_value=prediction,
            score=score,
            prompt_hash=None,
        )


# Custom metric: accuracy over the "category" field across all examples


def category_accuracy(predictions: list[Any], references: list[Any]) -> float:
    """Compute the fraction of examples where predicted category matches expected.

    Args:
        predictions: List of dicts returned by the target function, each containing
            at least a "category" key.
        references: List of expected output dicts, each containing a "category" key.

    Returns:
        Accuracy as a float in [0.0, 1.0]. Returns 0.0 for empty inputs.
    """
    if not predictions:
        return 0.0
    correct = sum(
        p["category"] == r["category"] for p, r in zip(predictions, references, strict=False)
    )
    return correct / len(predictions)


# Registry setup

evaluator_registry = EvaluatorRegistry()
evaluator_registry.register("category_match", CategoryEvaluator)

metric_registry = MetricRegistry()
metric_registry.register("category_accuracy", category_accuracy)


# Target function — simulates an LLM returning structured output


def classify_ticket(ticket_text: str) -> dict[str, Any]:
    """Classify a support ticket into a category with a confidence score.

    In production this would call an LLM and parse its JSON response.
    Here the responses are hardcoded for demonstration purposes.

    Args:
        ticket_text: The raw ticket message from the customer.

    Returns:
        A dict with "category" (str) and "confidence" (float).
    """
    responses: dict[str, dict[str, Any]] = {
        "My invoice shows the wrong amount": {"category": "billing", "confidence": 0.95},
        "The app crashes when I try to log in": {"category": "technical", "confidence": 0.88},
        "How do I reset my password?": {
            "category": "general",
            "confidence": 0.72,
        },  # wrong: should be "technical"
        "What are your business hours?": {"category": "general", "confidence": 0.91},
    }
    return responses.get(ticket_text, {"category": "general", "confidence": 0.50})


# Dataset


dataset = [
    {
        "input": "My invoice shows the wrong amount",
        "expected_output": {"category": "billing"},
    },
    {
        "input": "The app crashes when I try to log in",
        "expected_output": {"category": "technical"},
    },
    {
        "input": "How do I reset my password?",
        "expected_output": {"category": "technical"},
    },
    {
        "input": "What are your business hours?",
        "expected_output": {"category": "general"},
    },
]


# Pipeline


pipeline = EvaluationPipeline(
    target_fn=classify_ticket,
    dataset=dataset,
    field_evaluators={"category": ["category_match"]},
    metrics=["category_accuracy"],
    evaluator_registry=evaluator_registry,
    metric_registry=metric_registry,
    experiment_name="ticket-classification-eval",
)

result = pipeline.run()


# Results


print(f"=== {result.experiment_name} ===\n")

for run in result.runs:
    evaluation = run.evaluations[0]
    status = "✓" if evaluation.score == 1.0 else "✗"
    print(
        f'  {status}  "{run.input}"\n'
        f"       predicted: {run.output['category']!r}  "
        f"(confidence: {run.output['confidence']:.0%})\n"
        f"       expected:  {evaluation.expected_value!r}\n"
    )
print(result)
accuracy = result.metrics["category_accuracy"]
print(
    f"Category Accuracy: {accuracy:.0%}  "
    f"({int(accuracy * len(result.runs))}/{len(result.runs)} correct)"
)

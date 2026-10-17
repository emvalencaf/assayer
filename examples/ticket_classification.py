"""Example 2: Structured output evaluation with a custom metric and per-Field scoring.

Scenario: An LLM classifies customer support tickets and returns structured JSON:
    {"category": "billing" | "technical" | "general", "confidence": float}

We use:
- a built-in field metric (`exact_match`) to score the `category` Field on its own;
- `confidence_is_calibrated`, a custom `Metric` that scores a whole Trajectory;
- `Runner`, which runs the target over the Cases and returns an Experiment.

Run:
    python examples/ticket_classification.py
"""

from typing import Any

from assayer.metrics import Metric, register_field_metrics
from assayer.models import Case, Dataset, Trajectory
from assayer.registries import Registry
from assayer.runner import Runner

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
            "confidence": 0.92,
        },  # wrong: should be "technical"
        "What are your business hours?": {"category": "general", "confidence": 0.91},
    }
    return responses.get(ticket_text, {"category": "general", "confidence": 0.50})


# Custom metric: a wrong answer should not be given with high confidence


def confidence_is_calibrated(trajectory: Trajectory, case: Case) -> float:
    """Score 1 unless the target is wrong while being more than 80% confident.

    Args:
        trajectory: Its `final_output` is the dict the target returned.
        case: Its `expected_output` holds the expected category.

    Returns:
        1.0 when the answer is right or the confidence is at most 0.8, else 0.0.
    """
    output = trajectory.final_output
    right = output["category"] == case.expected_output["category"]
    return float(right or output["confidence"] <= 0.8)


calibrated = Metric(
    name="confidence_is_calibrated",
    level="trajectory",
    fn=confidence_is_calibrated,
    requires=("expected_output",),
)

registry = Registry()
register_field_metrics(registry)

# Dataset

dataset = Dataset(
    name="ticket-classification-eval",
    cases=[
        Case(
            input="My invoice shows the wrong amount",
            id="invoice",
            expected_output={"category": "billing"},
        ),
        Case(
            input="The app crashes when I try to log in",
            id="crash",
            expected_output={"category": "technical"},
        ),
        Case(
            input="How do I reset my password?",
            id="password",
            expected_output={"category": "technical"},
        ),
        Case(
            input="What are your business hours?",
            id="hours",
            expected_output={"category": "general"},
        ),
    ],
)

# Run

runner = Runner(
    target=classify_ticket,
    metrics=[calibrated],
    field_metrics={"category": [registry.get("exact_match")]},
)
experiment = runner.run(dataset)

# Results

print(f"=== {experiment.name} ===\n")

expected = {case.id: case.expected_output["category"] for case in experiment.cases}
for trajectory in experiment.trajectories:
    output = trajectory.final_output
    status = "✓" if output["category"] == expected[trajectory.case_id] else "✗"
    print(
        f"  {status}  {trajectory.case_id}: predicted {output['category']!r}, "
        f"expected {expected[trajectory.case_id]!r} (confidence: {output['confidence']:.0%})"
    )

by_field = experiment.scores_by_field()
category = by_field["category"]
print(f"\nCategory accuracy: {sum(s.value for s in category) / len(category):.0%}")
calibrated_scores = by_field[None]
print(f"Calibrated answers: {sum(s.value for s in calibrated_scores) / len(calibrated_scores):.0%}")

"""Example 4: One structured output scored with NER, classification and text generation.

Scenario: A support assistant reads a ticket and returns one JSON-like answer:
    {"category": str, "entities": [EntitySpan, ...], "reply": str}

Each Field is scored on its own, with the metric that suits its kind:
- `category` (classification): accuracy and macro F1;
- `entities` (NER): entity-level macro F1;
- `reply` (text generation): ROUGE-L against a reference reply.

Run:
    python examples/support_pipeline.py
"""

from assayer.metrics import (
    EntitySpan,
    accuracy,
    corpus_metric,
    make_f1,
    ner_macro_f1,
    rouge_l,
)
from assayer.models import Case, Dataset
from assayer.runner import Runner

ANSWERS = {
    "Acme charged me twice on 3 May": {
        "category": "billing",
        "entities": [EntitySpan("Acme", "ORG", 0, 4)],
        "reply": "We are sorry, we will refund the duplicate charge.",
    },
    "The Orion app crashes on login": {
        "category": "technical",
        "entities": [EntitySpan("Orion", "PRODUCT", 4, 9)],
        "reply": "Please update the app and try again.",
    },
    "Do you ship to Lisbon?": {
        "category": "billing",  # wrong: should be "general"
        "entities": [],  # missed "Lisbon"
        "reply": "Yes, we ship to Lisbon in three days.",
    },
}


def support_assistant(ticket: str) -> dict:
    """Classify a ticket, tag its entities and draft a reply.

    In production this would call an LLM and parse its answer; here it is hardcoded.

    Args:
        ticket: The customer's message.

    Returns:
        A dict with "category", "entities" and "reply".
    """
    return ANSWERS[ticket]


dataset = Dataset(
    "support-eval",
    [
        Case(
            input="Acme charged me twice on 3 May",
            id="double-charge",
            expected_output={
                "category": "billing",
                "entities": [EntitySpan("Acme", "ORG", 0, 4)],
                "reply": "We are sorry, we will refund the duplicate charge.",
            },
        ),
        Case(
            input="The Orion app crashes on login",
            id="crash",
            expected_output={
                "category": "technical",
                "entities": [EntitySpan("Orion", "PRODUCT", 4, 9)],
                "reply": "Please update the app and then try to log in again.",
            },
        ),
        Case(
            input="Do you ship to Lisbon?",
            id="shipping",
            expected_output={
                "category": "general",
                "entities": [EntitySpan("Lisbon", "PLACE", 16, 22)],
                "reply": "Yes, we ship to Lisbon in three business days.",
            },
        ),
    ],
)

runner = Runner(
    support_assistant,
    field_metrics={
        "category": [corpus_metric("accuracy", accuracy), corpus_metric("f1", make_f1("macro"))],
        "entities": [corpus_metric("ner_macro_f1", ner_macro_f1)],
        "reply": [corpus_metric("rouge_l", rouge_l)],
    },
)
experiment = runner.run(dataset)

print(f"=== {experiment.name} ===\n")
for score in experiment.scores:
    print(f"  {score.field:>9} · {score.name:<12} {score.value:.2f}")

"""Example 7: Structured output scored from its JSON Schema.

Scenario: An assistant reads a customer email and returns one JSON object that mixes
three kinds of Fields:
- classification: `category` and `priority` (enums);
- text generation: `summary` (free text);
- information extraction: `customer.name`, `customer.email`, `order_total`, `items`
  (a list of objects) and `tags` (a list of strings).

Instead of writing the field map by hand, we draft it from the output's JSON Schema with
`schema_to_field_map` (a Pydantic model class works too), adjust what the defaults get
wrong, and pass it to `Runner(field_metrics=...)`. Each Field is then scored with the
metric that suits its type.

Run:
    python examples/schema_structured_output.py
"""

from assayer.models import Case, Dataset
from assayer.runner import Runner, parse_field_map, schema_to_field_map

SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"enum": ["billing", "technical", "general"]},
        "priority": {"enum": ["low", "high"]},
        "summary": {"type": "string"},
        "customer": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "maxLength": 40},
                "email": {"type": "string", "format": "email"},
            },
        },
        "order_total": {"type": "number"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sku": {"type": "string", "maxLength": 20},
                    "quantity": {"type": "integer"},
                },
            },
        },
        "tags": {"type": "array", "items": {"type": "string"}},
    },
}

draft = schema_to_field_map(SCHEMA)
# The defaults fit most Fields. Here a total within one cent counts as right.
draft.spec["order_total"] = [{"numeric_tolerance": {"tolerance": 0.01}}]
print("Drafted field map:")
print(draft.to_json(), "\n")

EMAILS = {
    "e1": "Hi, I'm Ana Souza (ana@mail.com). You charged me 59.90 twice for 2 mugs and 1 cap.",
    "e2": "The dashboard of Bruno Lima (bruno@mail.com) is down and we lose sales. Urgent!",
    "e3": "Carla Dias here (carla@mail.com): do you sell gift cards? Order total was 20.",
}

EXPECTED = {
    "e1": {
        "category": "billing",
        "priority": "high",
        "summary": "Customer was charged twice for an order and asks for a refund.",
        "customer": {"name": "Ana Souza", "email": "ana@mail.com"},
        "order_total": 59.90,
        "items": [{"sku": "mug", "quantity": 2}, {"sku": "cap", "quantity": 1}],
        "tags": ["refund", "duplicate-charge"],
    },
    "e2": {
        "category": "technical",
        "priority": "high",
        "summary": "The dashboard is down and the customer is losing sales.",
        "customer": {"name": "Bruno Lima", "email": "bruno@mail.com"},
        "order_total": 0,
        "items": [],
        "tags": ["outage"],
    },
    "e3": {
        "category": "general",
        "priority": "low",
        "summary": "Customer asks whether gift cards are sold.",
        "customer": {"name": "Carla Dias", "email": "carla@mail.com"},
        "order_total": 20,
        "items": [],
        "tags": ["gift-card"],
    },
}

ANSWERS = {
    "e1": {
        **EXPECTED["e1"],
        "summary": "The customer was charged twice and wants a refund.",
        "items": [{"sku": "cap", "quantity": 1}, {"sku": "mug", "quantity": 3}],  # wrong quantity
    },
    "e2": {**EXPECTED["e2"], "priority": "low", "tags": ["outage", "dashboard"]},  # wrong priority
    "e3": {
        **EXPECTED["e3"],
        "category": "billing",  # wrong category
        "customer": {"name": "Carla Dias", "email": "carla@mail.org"},  # wrong email
    },
}


def extract(email_text: str) -> dict:
    """Read an email into the structured answer. In production this calls an LLM."""
    return ANSWERS[next(key for key, text in EMAILS.items() if text == email_text)]


dataset = Dataset(
    "email-extraction",
    [Case(input=text, id=key, expected_output=EXPECTED[key]) for key, text in EMAILS.items()],
)

runner = Runner(extract, field_metrics=parse_field_map(draft.spec))
experiment = runner.run(dataset)

print(f"=== {experiment.name} ===\n")
for field_name, scores in experiment.scores_by_field().items():
    for name in dict.fromkeys(score.name for score in scores):
        values = [score.value for score in scores if score.name == name]
        print(f"  {field_name or '(whole)':<22} {name:<24} {sum(values) / len(values):.2f}")

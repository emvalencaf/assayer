"""Example 3: Named entity recognition scored with the entity-level macro F1.

Scenario: A model finds people, organizations and places in a sentence and returns
`EntitySpan`s (text, type and character offsets). The reference spans live in the
Case; a span counts only if its text, type and offsets all match.

We use:
- `corpus_metric` to lift `ner_macro_f1` into an Experiment-level Metric;
- `Runner`, which runs the target over the Cases and returns an Experiment.

Run:
    python examples/ner_extraction.py
"""

from assayer.metrics import EntitySpan, corpus_metric, ner_macro_f1
from assayer.models import Case, Dataset
from assayer.runner import Runner

SENTENCES = {
    "Ada Lovelace joined Acme in London": [
        EntitySpan("Ada Lovelace", "PERSON", 0, 12),
        EntitySpan("Acme", "ORG", 20, 24),
        EntitySpan("London", "PLACE", 28, 34),
    ],
    "Alan Turing left Bletchley Park": [
        EntitySpan("Alan Turing", "PERSON", 0, 11),
        EntitySpan("Bletchley Park", "PLACE", 17, 31),
    ],
    "Grace Hopper visited Paris": [
        EntitySpan("Grace Hopper", "PERSON", 0, 12),
        EntitySpan("Paris", "PLACE", 21, 26),
    ],
}


def extract_entities(sentence: str) -> list[EntitySpan]:
    """Find the entities of a sentence.

    In production this would call an NER model or an LLM and turn its answer into
    spans. Here the answers are hardcoded, with two mistakes: the type of "Acme" and
    the missing "Paris".

    Args:
        sentence: The text to tag.

    Returns:
        The predicted spans.
    """
    spans = list(SENTENCES[sentence])
    if sentence.startswith("Ada"):
        spans[1] = EntitySpan("Acme", "PLACE", 20, 24)  # wrong type
    if sentence.startswith("Grace"):
        spans.pop()  # missed entity
    return spans


dataset = Dataset(
    "ner-eval",
    [
        Case(input=text, id=text.split()[0].lower(), expected_output=spans)
        for text, spans in SENTENCES.items()
    ],
)

experiment = Runner(extract_entities, [corpus_metric("ner_macro_f1", ner_macro_f1)]).run(dataset)

print(f"=== {experiment.name} ===\n")
for case, trajectory in zip(experiment.cases, experiment.trajectories, strict=True):
    found = {(s.text, s.entity_type) for s in trajectory.final_output}
    wanted = {(s.text, s.entity_type) for s in case.expected_output}
    print(f"  {case.id}: missed {sorted(wanted - found)}, spurious {sorted(found - wanted)}")

print(f"\nNER macro F1: {experiment.scores[0].value:.2f}")

"""Example 1: Standalone faithfulness evaluation using a built-in evaluator.

Scenario: A Q&A bot answers questions based on a source context. We use
FaithfulnessEvaluator to check whether each generated answer is grounded
in the provided context — without setting up a full pipeline.

Run:
    python examples/faithfulness_check.py
"""

from assayer.evaluators.hallucination import FaithfulnessEvaluator

evaluator = FaithfulnessEvaluator(field_name="answer")

samples = [
    {
        "context": (
            "The Eiffel Tower was built between 1887 and 1889 as the entrance arch "
            "for the 1889 World's Fair. It was designed by the engineer Gustave Eiffel."
        ),
        "answer": "The Eiffel Tower was designed by Gustave Eiffel and completed in 1889.",
    },
    {
        "context": (
            "The Eiffel Tower was built between 1887 and 1889 as the entrance arch "
            "for the 1889 World's Fair. It was designed by the engineer Gustave Eiffel."
        ),
        # Hallucinated answer — the tower is not in London
        "answer": "The Eiffel Tower is located in London and was built in the 19th century.",
    },
]

print("=== Faithfulness Evaluation ===\n")

for i, sample in enumerate(samples, start=1):
    result = evaluator.evaluate(
        prediction=sample["answer"],
        reference=sample["context"],
    )
    label = "HALLUCINATION" if result.metadata["is_hallucination"] else "FAITHFUL"
    print(f"[{i}] {label}  (score: {result.score:.2f})")
    print(f"     Answer : {sample['answer']}")
    print()

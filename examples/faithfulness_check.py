"""Example 1: Faithfulness of answers to the context they were retrieved from.

Scenario: A Q&A bot retrieves a passage and answers from it. `make_faithfulness` asks a
Judge to split each answer into claims and to check every claim against the retrieved
context; the Score is the share of supported claims.

The Judge here is a scripted stand-in so the example runs offline. In production, wrap a
LangChain chat model (needs `assayer[langchain]`):

    from langchain_openai import ChatOpenAI
    from assayer.judges import LangChainJudge

    judge = LangChainJudge(ChatOpenAI(model="gpt-4o-mini"))

Run:
    python examples/faithfulness_check.py
"""

import json
from typing import Any

from assayer.judges import JudgeResponse
from assayer.metrics import make_faithfulness
from assayer.models import Case, Dataset, Step, Trajectory
from assayer.runner import Runner

CONTEXT = (
    "The Eiffel Tower was built between 1887 and 1889 as the entrance arch "
    "for the 1889 World's Fair. It was designed by the engineer Gustave Eiffel."
)

ANSWERS = {
    "Who designed the Eiffel Tower?": (
        "The Eiffel Tower was designed by Gustave Eiffel and completed in 1889."
    ),
    # Hallucinated answer — the tower is not in London
    "Where is the Eiffel Tower?": "The Eiffel Tower is located in London.",
}

# What the scripted Judge says: the claims of each answer, then a verdict for each claim.
CLAIMS = {
    ANSWERS["Who designed the Eiffel Tower?"]: [
        "Gustave Eiffel designed the tower.",
        "It was completed in 1889.",
    ],
    ANSWERS["Where is the Eiffel Tower?"]: ["The Eiffel Tower is located in London."],
}
SUPPORTED = {
    "Gustave Eiffel designed the tower.": True,
    "It was completed in 1889.": True,
    "The Eiffel Tower is located in London.": False,
}


class ScriptedJudge:
    """Answers the two faithfulness prompts from the tables above."""

    def complete(
        self, messages: list[dict[str, str]], schema: dict[str, Any] | None = None
    ) -> JudgeResponse:
        prompt = messages[-1]["content"]
        if "claims" in (schema or {}).get("properties", {}):
            answer = next(a for a in CLAIMS if a in prompt)
            return JudgeResponse(json.dumps({"claims": CLAIMS[answer]}))
        claims = [c for c in SUPPORTED if c in prompt]
        verdicts = [{"supported": SUPPORTED[c], "reason": "checked"} for c in claims]
        return JudgeResponse(json.dumps({"verdicts": verdicts}))


def answer(question: str) -> Trajectory:
    """A RAG target: one retrieval Step and one model Step that answers from it."""
    return Trajectory(
        steps=[
            Step(kind="retrieval", name="search", input=question, output=[CONTEXT]),
            Step(kind="model", input=question, output=ANSWERS[question]),
        ],
        final_output=ANSWERS[question],
    )


dataset = Dataset("faithfulness-check", [Case(input=q, id=q) for q in ANSWERS])
experiment = Runner(answer, [make_faithfulness(ScriptedJudge())]).run(dataset)

print("=== Faithfulness Evaluation ===\n")

for trajectory, score in zip(experiment.trajectories, experiment.scores, strict=True):
    label = "FAITHFUL" if score.value == 1.0 else "HALLUCINATION"
    print(f"{label}  (score: {score.value:.2f}, {score.comment})")
    print(f"     Answer: {trajectory.final_output}")
print(f"\nJudge calls: {experiment.judge_calls}")

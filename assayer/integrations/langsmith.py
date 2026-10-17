"""LangSmith integration for publishing experiment results.

This module provides a publisher class that wraps the LangSmith SDK to push
experiment results, including per-evaluator scores, token counts, cost, and
field-level audit records to LangSmith for tracking and visualization.
"""

import json
import os
from typing import TYPE_CHECKING

import langsmith

if TYPE_CHECKING:
    from assayer.models import ExperimentResult


class LangSmithPublisher:
    """Publisher for sending experiment results to LangSmith.

    Wraps a langsmith.Client to publish ExperimentResult data including
    per-evaluator scores, token usage, cost, and field-level evaluations
    in a format queryable in the LangSmith UI.

    Args:
        client: A configured langsmith.Client instance.
    """

    def __init__(self, client: langsmith.Client) -> None:
        """Initialize the publisher with a LangSmith client.

        Args:
            client: A configured langsmith.Client instance.
        """
        self._client = client

    def publish(self, result: "ExperimentResult", dataset_name: str) -> None:
        """Publish experiment results to LangSmith.

        For each RunResult in result.runs:
        1. Creates a run record under result.experiment_name with token usage metadata
        2. Creates feedback entries for each FieldEvaluation in the run

        Args:
            result: The experiment result containing runs and evaluations to publish.
            dataset_name: Name of the dataset to associate with the published runs.

        Raises:
            Exception: Any exceptions from the LangSmith SDK are allowed to propagate.
        """
        # Handle zero runs case - return early without making any SDK calls
        if not result.runs:
            return

        for run_result in result.runs:
            # Create metadata for the run with token usage information
            metadata = {
                "input_tokens": run_result.token_usage.input_tokens,
                "output_tokens": run_result.token_usage.output_tokens,
                "cost_usd": run_result.token_usage.cost_usd,  # Include even if None
            }

            # Create the run record - any SDK exceptions will propagate
            run = self._client.create_run(
                name=result.experiment_name,
                inputs=run_result.input,
                outputs=run_result.output,
                metadata=metadata,
            )

            # Create feedback entries for each field evaluation
            for field_evaluation in run_result.evaluations:
                # Prepare metadata for feedback comment, omitting prompt_hash if None
                feedback_metadata = dict(field_evaluation.metadata)
                if field_evaluation.prompt_hash is not None:
                    feedback_metadata["prompt_hash"] = field_evaluation.prompt_hash
                elif (
                    "prompt_hash" in feedback_metadata and feedback_metadata["prompt_hash"] is None
                ):
                    # Remove prompt_hash key if it exists and is None
                    del feedback_metadata["prompt_hash"]

                # Create feedback entry - any SDK exceptions will propagate
                self._client.create_feedback(
                    run_id=run.id,
                    key=f"{field_evaluation.field_name}/{field_evaluation.evaluator_method}",
                    score=field_evaluation.score,
                    comment=json.dumps(feedback_metadata),
                )


def make_langsmith_publisher() -> LangSmithPublisher:
    """Create a LangSmithPublisher using the LANGCHAIN_API_KEY environment variable.

    Reads the LANGCHAIN_API_KEY from the environment and instantiates a
    langsmith.Client. The client is then wrapped in a LangSmithPublisher.

    Returns:
        A configured LangSmithPublisher instance.

    Raises:
        EnvironmentError: If LANGCHAIN_API_KEY is not set in the environment.
    """
    api_key = os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        raise OSError("LANGCHAIN_API_KEY environment variable is not set")

    client = langsmith.Client()
    return LangSmithPublisher(client)

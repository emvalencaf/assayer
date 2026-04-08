"""LangSmith integration for publishing experiment results.

This module provides a publisher class that wraps the LangSmith SDK to push
experiment results, including per-evaluator scores, token counts, cost, and
field-level audit records to LangSmith for tracking and visualization.
"""

import os
import langsmith


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
        raise EnvironmentError("LANGCHAIN_API_KEY environment variable is not set")

    client = langsmith.Client()
    return LangSmithPublisher(client)
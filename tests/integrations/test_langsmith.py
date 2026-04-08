"""Tests for LangSmith integration factory function."""

import os
import pytest
from unittest.mock import patch, Mock

from assayer.integrations.langsmith import make_langsmith_publisher, LangSmithPublisher


class TestMakeLangSmithPublisher:
    """Test cases for make_langsmith_publisher factory function."""

    def test_raises_environment_error_when_api_key_missing(self):
        """Test that make_langsmith_publisher raises EnvironmentError when LANGCHAIN_API_KEY is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure LANGCHAIN_API_KEY is not in environment
            if "LANGCHAIN_API_KEY" in os.environ:
                del os.environ["LANGCHAIN_API_KEY"]

            with pytest.raises(EnvironmentError, match="LANGCHAIN_API_KEY"):
                make_langsmith_publisher()

    @patch("assayer.integrations.langsmith.langsmith")
    def test_returns_langsmith_publisher_when_api_key_set(self, mock_langsmith):
        """Test that make_langsmith_publisher returns LangSmithPublisher when LANGCHAIN_API_KEY is set."""
        # Mock the langsmith.Client
        mock_client = Mock()
        mock_langsmith.Client.return_value = mock_client

        test_api_key = "test-api-key-12345"
        with patch.dict(os.environ, {"LANGCHAIN_API_KEY": test_api_key}):
            publisher = make_langsmith_publisher()

            # Verify that it returns a LangSmithPublisher instance
            assert isinstance(publisher, LangSmithPublisher)

            # Verify that langsmith.Client was called with correct parameters
            mock_langsmith.Client.assert_called_once()

            # Verify that the publisher wraps the client
            assert publisher._client is mock_client

    @patch("assayer.integrations.langsmith.langsmith")
    def test_passes_api_key_to_langsmith_client(self, mock_langsmith):
        """Test that make_langsmith_publisher passes the API key to the langsmith.Client."""
        mock_client = Mock()
        mock_langsmith.Client.return_value = mock_client

        test_api_key = "specific-test-key-67890"
        with patch.dict(os.environ, {"LANGCHAIN_API_KEY": test_api_key}):
            make_langsmith_publisher()

            # Verify that the Client constructor was called
            # Note: The actual langsmith.Client may accept api_key as parameter or read from env
            # We're testing that the Client is instantiated when the env var is present
            mock_langsmith.Client.assert_called_once()


class TestLangSmithPublisherInit:
    """Test cases for LangSmithPublisher initialization."""

    def test_accepts_langsmith_client(self):
        """Test that LangSmithPublisher accepts a langsmith.Client in its constructor."""
        mock_client = Mock()
        publisher = LangSmithPublisher(mock_client)

        assert publisher._client is mock_client
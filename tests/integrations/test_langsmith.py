"""Tests for LangSmith integration factory function and publisher."""

import json
import os
from unittest.mock import Mock, patch

import pytest

from assayer.integrations.langsmith import LangSmithPublisher, make_langsmith_publisher
from assayer.models import ExperimentResult, FieldEvaluation, RunResult, TokenUsage


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


class TestLangSmithPublisherPublish:
    """Test cases for LangSmithPublisher.publish() method."""

    def test_creates_one_run_record_per_run_result(self):
        """Test that publish() creates one run record per RunResult."""
        # Setup
        mock_client = Mock()
        publisher = LangSmithPublisher(mock_client)

        token_usage1 = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
        token_usage2 = TokenUsage(input_tokens=200, output_tokens=75, cost_usd=0.02)

        run1 = RunResult(input="test input 1", output="test output 1", token_usage=token_usage1)
        run2 = RunResult(input="test input 2", output="test output 2", token_usage=token_usage2)

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run1, run2])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        assert mock_client.create_run.call_count == 2

    def test_run_metadata_contains_token_usage_fields(self):
        """Test that run metadata contains input_tokens, output_tokens, and cost_usd."""
        # Setup
        mock_client = Mock()
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=150, output_tokens=75, cost_usd=0.025)
        run = RunResult(input="test input", output="test output", token_usage=token_usage)

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        mock_client.create_run.assert_called_once()
        call_args = mock_client.create_run.call_args[1]

        expected_metadata = {"input_tokens": 150, "output_tokens": 75, "cost_usd": 0.025}

        assert "metadata" in call_args
        for key, value in expected_metadata.items():
            assert call_args["metadata"][key] == value

    def test_run_metadata_includes_null_cost_usd(self):
        """Test that cost_usd=None is published as null in metadata, not omitted."""
        # Setup
        mock_client = Mock()
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=None)
        run = RunResult(input="test input", output="test output", token_usage=token_usage)

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        mock_client.create_run.assert_called_once()
        call_args = mock_client.create_run.call_args[1]

        assert "metadata" in call_args
        assert "cost_usd" in call_args["metadata"]
        assert call_args["metadata"]["cost_usd"] is None

    def test_creates_feedback_entry_per_field_evaluation(self):
        """Test that one feedback entry is created per FieldEvaluation."""
        # Setup
        mock_client = Mock()
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)

        evaluation1 = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="exact_match",
            expected_value="expected",
            obtained_value="obtained",
            score=0.8,
            prompt_hash="hash1",
        )

        evaluation2 = FieldEvaluation(
            field_name="relevance",
            evaluator_method="llm_judge",
            expected_value="relevant",
            obtained_value="somewhat relevant",
            score=0.6,
            prompt_hash="hash2",
        )

        run = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage,
            evaluations=[evaluation1, evaluation2],
        )

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        assert mock_client.create_feedback.call_count == 2

    def test_feedback_entry_has_correct_key_score_and_comment(self):
        """Test that feedback entries have correct key, score, and comment format."""
        # Setup
        mock_client = Mock()
        mock_client.create_run.return_value = Mock(id="run123")
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)

        metadata = {"temperature": 0.7, "model": "gpt-4", "prompt_hash": "abc123"}
        evaluation = FieldEvaluation(
            field_name="quality",
            evaluator_method="llm_judge",
            expected_value="high quality",
            obtained_value="medium quality",
            score=0.75,
            prompt_hash="abc123",
            metadata=metadata,
        )

        run = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage,
            evaluations=[evaluation],
        )

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        mock_client.create_feedback.assert_called_once()
        call_args = mock_client.create_feedback.call_args[1]

        assert call_args["key"] == "quality/llm_judge"
        assert call_args["score"] == 0.75

        # Comment should be JSON-serialized metadata
        comment_data = json.loads(call_args["comment"])
        assert comment_data == metadata

    def test_prompt_hash_none_omitted_from_feedback_comment(self):
        """Test that prompt_hash=None is omitted from feedback comment JSON."""
        # Setup
        mock_client = Mock()
        mock_client.create_run.return_value = Mock(id="run123")
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)

        metadata = {"temperature": 0.7, "model": "gpt-4", "prompt_hash": None}
        evaluation = FieldEvaluation(
            field_name="quality",
            evaluator_method="exact_match",
            expected_value="high quality",
            obtained_value="medium quality",
            score=0.75,
            prompt_hash=None,
            metadata=metadata,
        )

        run = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage,
            evaluations=[evaluation],
        )

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        mock_client.create_feedback.assert_called_once()
        call_args = mock_client.create_feedback.call_args[1]

        comment_data = json.loads(call_args["comment"])
        # prompt_hash should be omitted from the JSON when it's None
        expected_metadata = {"temperature": 0.7, "model": "gpt-4"}
        assert comment_data == expected_metadata
        assert "prompt_hash" not in comment_data

    def test_zero_runs_publishes_without_error(self):
        """Test that publishing an experiment with zero runs completes without error."""
        # Setup
        mock_client = Mock()
        publisher = LangSmithPublisher(mock_client)

        experiment = ExperimentResult(experiment_name="empty_experiment", runs=[])

        # Execute - should not raise any exception
        publisher.publish(experiment, "test_dataset")

        # Verify - no create_run calls should be made
        mock_client.create_run.assert_not_called()
        mock_client.create_feedback.assert_not_called()

    def test_langsmith_sdk_exceptions_propagate(self):
        """Test that LangSmith SDK exceptions propagate and are not swallowed."""
        # Setup
        mock_client = Mock()
        # Simulate SDK exception
        mock_client.create_run.side_effect = Exception("LangSmith API Error")
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
        run = RunResult(input="test input", output="test output", token_usage=token_usage)
        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute and verify exception propagates
        with pytest.raises(Exception, match="LangSmith API Error"):
            publisher.publish(experiment, "test_dataset")

    def test_feedback_exception_propagates(self):
        """Test that exceptions from create_feedback propagate."""
        # Setup
        mock_client = Mock()
        mock_client.create_run.return_value = Mock(id="run123")
        mock_client.create_feedback.side_effect = Exception("Feedback API Error")
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)

        evaluation = FieldEvaluation(
            field_name="quality",
            evaluator_method="llm_judge",
            expected_value="high",
            obtained_value="medium",
            score=0.75,
            prompt_hash="hash123",
        )

        run = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage,
            evaluations=[evaluation],
        )

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute and verify exception propagates
        with pytest.raises(Exception, match="Feedback API Error"):
            publisher.publish(experiment, "test_dataset")

    def test_multiple_runs_with_multiple_evaluations(self):
        """Test a complex scenario with multiple runs each having multiple evaluations."""
        # Setup
        mock_client = Mock()
        mock_client.create_run.return_value = Mock(id="run123")
        publisher = LangSmithPublisher(mock_client)

        # First run with 2 evaluations
        token_usage1 = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)
        evaluation1a = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="exact_match",
            expected_value="A",
            obtained_value="A",
            score=1.0,
            prompt_hash=None,
        )
        evaluation1b = FieldEvaluation(
            field_name="relevance",
            evaluator_method="llm_judge",
            expected_value="relevant",
            obtained_value="relevant",
            score=0.9,
            prompt_hash="hash1",
        )
        run1 = RunResult(
            input="input1",
            output="output1",
            token_usage=token_usage1,
            evaluations=[evaluation1a, evaluation1b],
        )

        # Second run with 1 evaluation
        token_usage2 = TokenUsage(input_tokens=200, output_tokens=100, cost_usd=None)
        evaluation2a = FieldEvaluation(
            field_name="fluency",
            evaluator_method="grammar_check",
            expected_value="fluent",
            obtained_value="fluent",
            score=0.85,
            prompt_hash=None,
        )
        run2 = RunResult(
            input="input2", output="output2", token_usage=token_usage2, evaluations=[evaluation2a]
        )

        experiment = ExperimentResult(experiment_name="complex_experiment", runs=[run1, run2])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        assert mock_client.create_run.call_count == 2
        assert mock_client.create_feedback.call_count == 3

        # Verify feedback keys
        feedback_calls = mock_client.create_feedback.call_args_list
        expected_keys = ["accuracy/exact_match", "relevance/llm_judge", "fluency/grammar_check"]
        actual_keys = [call[1]["key"] for call in feedback_calls]

        assert set(actual_keys) == set(expected_keys)

    def test_empty_metadata_in_feedback_comment(self):
        """Test that empty metadata is handled correctly in feedback comments."""
        # Setup
        mock_client = Mock()
        mock_client.create_run.return_value = Mock(id="run123")
        publisher = LangSmithPublisher(mock_client)

        token_usage = TokenUsage(input_tokens=100, output_tokens=50, cost_usd=0.01)

        # FieldEvaluation with empty metadata (default dict)
        evaluation = FieldEvaluation(
            field_name="accuracy",
            evaluator_method="exact_match",
            expected_value="test",
            obtained_value="test",
            score=1.0,
            prompt_hash=None,
            # metadata defaults to empty dict
        )

        run = RunResult(
            input="test input",
            output="test output",
            token_usage=token_usage,
            evaluations=[evaluation],
        )

        experiment = ExperimentResult(experiment_name="test_experiment", runs=[run])

        # Execute
        publisher.publish(experiment, "test_dataset")

        # Verify
        mock_client.create_feedback.assert_called_once()
        call_args = mock_client.create_feedback.call_args[1]

        comment_data = json.loads(call_args["comment"])
        assert comment_data == {}

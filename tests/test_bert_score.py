"""Tests for BERTScore metric implementation (TASK-002)."""

import pytest
from unittest.mock import patch, MagicMock
from assayer.metrics.chat import bert_score


class TestBertScore:
    """Test cases for bert_score function."""

    def test_bert_score_within_tolerance_of_library(self):
        """Test that bert_score output is within ±0.01 of bert-score library mean F1."""
        predictions = ["The cat sat on the mat", "Hello world"]
        references = ["A cat was sitting on a mat", "Hi there world"]

        # Mock the bert_score library to return known values
        mock_f1_scores = [0.85, 0.92]  # Example F1 scores for each pair
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)  # 0.885

        with patch('bert_score.score') as mock_score:
            # bert_score.score returns (P, R, F1) tensors
            mock_score.return_value = (
                MagicMock(),  # Precision tensor (not used)
                MagicMock(),  # Recall tensor (not used)
                MagicMock(tolist=lambda: mock_f1_scores)  # F1 tensor with tolist() method
            )

            result = bert_score(predictions, references)

            # Verify the library was called with correct parameters
            mock_score.assert_called_once_with(
                predictions, references, lang="en", rescale_with_baseline=True
            )

            # Verify result is within tolerance of expected mean
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_returns_zero_for_empty_predictions(self):
        """Test that bert_score returns 0.0 for empty predictions list."""
        references = ["Some reference text"]

        result = bert_score([], references)

        assert result == 0.0

    def test_bert_score_returns_zero_for_empty_references(self):
        """Test that bert_score returns 0.0 for empty references list."""
        predictions = ["Some prediction text"]

        result = bert_score(predictions, [])

        assert result == 0.0

    def test_bert_score_returns_zero_for_both_empty(self):
        """Test that bert_score returns 0.0 when both lists are empty."""
        result = bert_score([], [])

        assert result == 0.0

    def test_bert_score_handles_short_strings_without_raising(self):
        """Test that bert_score handles strings with fewer than 3 tokens without raising."""
        # Single token strings
        predictions = ["cat", "hi"]
        references = ["dog", "bye"]

        mock_f1_scores = [0.65, 0.45]  # Example scores for short strings
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)

        with patch('bert_score.score') as mock_score:
            mock_score.return_value = (
                MagicMock(),
                MagicMock(),
                MagicMock(tolist=lambda: mock_f1_scores)
            )

            # Should not raise any exception
            result = bert_score(predictions, references)

            assert isinstance(result, float)
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_handles_two_token_strings(self):
        """Test that bert_score handles two-token strings without raising."""
        predictions = ["hello world", "good bye"]
        references = ["hi there", "see ya"]

        mock_f1_scores = [0.75, 0.55]
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)

        with patch('bert_score.score') as mock_score:
            mock_score.return_value = (
                MagicMock(),
                MagicMock(),
                MagicMock(tolist=lambda: mock_f1_scores)
            )

            result = bert_score(predictions, references)

            assert isinstance(result, float)
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_handles_library_exceptions_gracefully(self):
        """Test that bert_score returns 0.0 when bert-score library raises exceptions."""
        predictions = ["test"]
        references = ["reference"]

        with patch('bert_score.score') as mock_score:
            mock_score.side_effect = Exception("Library error")

            result = bert_score(predictions, references)

            assert result == 0.0

    def test_bert_score_with_mismatched_list_lengths(self):
        """Test that bert_score handles mismatched prediction/reference list lengths."""
        predictions = ["first prediction", "second prediction", "third prediction"]
        references = ["first reference", "second reference"]  # One fewer reference

        # bert-score library should handle this by only processing pairs up to min length
        mock_f1_scores = [0.8, 0.9]  # Only 2 scores for 2 pairs
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)

        with patch('bert_score.score') as mock_score:
            mock_score.return_value = (
                MagicMock(),
                MagicMock(),
                MagicMock(tolist=lambda: mock_f1_scores)
            )

            result = bert_score(predictions, references)

            assert isinstance(result, float)
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_function_signature_and_typing(self):
        """Test that bert_score function has correct signature and type hints."""
        import inspect
        from typing import get_type_hints

        # Check function signature
        sig = inspect.signature(bert_score)
        params = list(sig.parameters.keys())

        assert params == ['predictions', 'references']
        assert sig.return_annotation == float

        # Check type hints
        hints = get_type_hints(bert_score)
        assert hints['predictions'] == list[str]
        assert hints['references'] == list[str]
        assert hints['return'] == float

    def test_bert_score_has_docstring(self):
        """Test that bert_score function has a Google-style docstring."""
        docstring = bert_score.__doc__

        assert docstring is not None
        assert len(docstring.strip()) > 0

        # Check for Google-style docstring components
        assert "Args:" in docstring
        assert "Returns:" in docstring

        # Check that it mentions key aspects of the function
        assert "bert" in docstring.lower() or "bertscore" in docstring.lower()
        assert "f1" in docstring.lower()
        assert "mean" in docstring.lower()

    def test_bert_score_integration_with_real_library_behavior(self):
        """Test bert_score integration mimicking real bert-score library behavior."""
        predictions = ["The quick brown fox jumps over the lazy dog"]
        references = ["A fast brown fox leaps over the sleeping dog"]

        # Mock realistic bert-score behavior where F1 tensor has tolist() method
        mock_f1_tensor = MagicMock()
        mock_f1_tensor.tolist.return_value = [0.873456789]  # Realistic BERTScore F1

        with patch('bert_score.score') as mock_score:
            mock_score.return_value = (
                MagicMock(),  # Precision
                MagicMock(),  # Recall
                mock_f1_tensor  # F1 scores
            )

            result = bert_score(predictions, references)

            # Verify correct library call
            mock_score.assert_called_once_with(
                predictions, references, lang="en", rescale_with_baseline=True
            )

            # Result should be the single F1 score (mean of one value is the value itself)
            expected = 0.873456789
            assert abs(result - expected) <= 0.01
            assert isinstance(result, float)
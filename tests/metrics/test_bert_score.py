"""Tests for BERTScore metric implementation (TASK-002)."""

import sys
import types
from unittest.mock import MagicMock, patch

from assayer.metrics.chat import bert_score


def _make_bert_score_mock(f1_scores):
    """Return a (mock_module, mock_score_fn) pair that injects f1_scores."""
    mock_module = types.ModuleType("bert_score")
    mock_score = MagicMock(
        return_value=(
            MagicMock(),
            MagicMock(),
            MagicMock(tolist=lambda: f1_scores),
        )
    )
    mock_module.score = mock_score
    return mock_module, mock_score


class TestBertScore:
    """Test cases for bert_score function."""

    def test_bert_score_within_tolerance_of_library(self):
        """Test that bert_score output is within ±0.01 of bert-score library mean F1."""
        predictions = ["The cat sat on the mat", "Hello world"]
        references = ["A cat was sitting on a mat", "Hi there world"]

        mock_f1_scores = [0.85, 0.92]
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)  # 0.885

        mock_module, mock_score = _make_bert_score_mock(mock_f1_scores)
        with patch.dict(sys.modules, {"bert_score": mock_module}):
            result = bert_score(predictions, references)

            mock_score.assert_called_once_with(
                predictions, references, lang="en", rescale_with_baseline=True
            )
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_clamps_rescaled_scores_to_unit_interval(self):
        """Test that floating-point overshoot from baseline rescaling stays within [0, 1]."""
        mock_module, _ = _make_bert_score_mock([1.000001, 1.000002])
        with patch.dict(sys.modules, {"bert_score": mock_module}):
            assert bert_score(["a", "b"], ["a", "b"]) == 1.0

        mock_module, _ = _make_bert_score_mock([-0.2, -0.1])
        with patch.dict(sys.modules, {"bert_score": mock_module}):
            assert bert_score(["a", "b"], ["c", "d"]) == 0.0

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
        predictions = ["cat", "hi"]
        references = ["dog", "bye"]

        mock_f1_scores = [0.65, 0.45]
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)

        mock_module, _ = _make_bert_score_mock(mock_f1_scores)
        with patch.dict(sys.modules, {"bert_score": mock_module}):
            result = bert_score(predictions, references)

            assert isinstance(result, float)
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_handles_two_token_strings(self):
        """Test that bert_score handles two-token strings without raising."""
        predictions = ["hello world", "good bye"]
        references = ["hi there", "see ya"]

        mock_f1_scores = [0.75, 0.55]
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)

        mock_module, _ = _make_bert_score_mock(mock_f1_scores)
        with patch.dict(sys.modules, {"bert_score": mock_module}):
            result = bert_score(predictions, references)

            assert isinstance(result, float)
            assert abs(result - expected_mean) <= 0.01

    def test_bert_score_handles_library_exceptions_gracefully(self):
        """Test that bert_score returns 0.0 when bert-score library raises exceptions."""
        predictions = ["test"]
        references = ["reference"]

        mock_module = types.ModuleType("bert_score")
        mock_module.score = MagicMock(side_effect=Exception("Library error"))
        with patch.dict(sys.modules, {"bert_score": mock_module}):
            result = bert_score(predictions, references)

            assert result == 0.0

    def test_bert_score_with_mismatched_list_lengths(self):
        """Test that bert_score handles mismatched prediction/reference list lengths."""
        predictions = ["first prediction", "second prediction", "third prediction"]
        references = ["first reference", "second reference"]  # One fewer reference

        mock_f1_scores = [0.8, 0.9]
        expected_mean = sum(mock_f1_scores) / len(mock_f1_scores)

        mock_module, _ = _make_bert_score_mock(mock_f1_scores)
        with patch.dict(sys.modules, {"bert_score": mock_module}):
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

        assert params == ["predictions", "references"]
        assert sig.return_annotation == float

        # Check type hints
        hints = get_type_hints(bert_score)
        assert hints["predictions"] == list[str]
        assert hints["references"] == list[str]
        assert hints["return"] == float

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

        mock_f1_tensor = MagicMock()
        mock_f1_tensor.tolist.return_value = [0.873456789]

        mock_module = types.ModuleType("bert_score")
        mock_score = MagicMock(return_value=(MagicMock(), MagicMock(), mock_f1_tensor))
        mock_module.score = mock_score

        with patch.dict(sys.modules, {"bert_score": mock_module}):
            result = bert_score(predictions, references)

            mock_score.assert_called_once_with(
                predictions, references, lang="en", rescale_with_baseline=True
            )

            expected = 0.873456789
            assert abs(result - expected) <= 0.01
            assert isinstance(result, float)

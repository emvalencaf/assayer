"""Tests for BLEU and ROUGE-L metrics in assayer.metrics.chat.

This module tests the BLEU and ROUGE-L metric implementations to ensure they
match the reference implementations from NLTK and rouge-score libraries.
"""

from unittest.mock import MagicMock, patch


class TestBLEUMetric:
    """Test cases for the BLEU metric function."""

    def test_bleu_with_perfect_match_single_pair(self):
        """Test BLEU returns 1.0 for identical prediction and reference."""
        from assayer.metrics.chat import bleu

        predictions = ["hello world test"]
        references = ["hello world test"]

        score = bleu(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert abs(score - 1.0) < 0.01  # Should be very close to 1.0

    def test_bleu_with_perfect_mismatch_single_pair(self):
        """Test BLEU returns 0.0 for completely different prediction and reference."""
        from assayer.metrics.chat import bleu

        predictions = ["hello world"]
        references = ["goodbye earth"]

        score = bleu(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score == 0.0  # No matching n-grams

    def test_bleu_with_partial_match_multiple_pairs(self):
        """Test BLEU with multiple prediction-reference pairs with partial overlap."""
        from assayer.metrics.chat import bleu

        predictions = [
            "the cat sat on the mat",
            "hello world from python",
            "this is a test sentence",
        ]
        references = [
            "the cat sat on a mat",
            "hello world from java",
            "this is another test sentence",
        ]

        score = bleu(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should have some overlap

    @patch("nltk.translate.bleu_score.corpus_bleu")
    def test_bleu_matches_nltk_corpus_bleu(self, mock_corpus_bleu):
        """Test BLEU output is within ±0.01 of nltk.translate.bleu_score.corpus_bleu."""
        from assayer.metrics.chat import bleu

        # Mock NLTK to return a known value
        expected_score = 0.42
        mock_corpus_bleu.return_value = expected_score

        predictions = ["hello world", "test sentence"]
        references = ["hello earth", "test phrase"]

        score = bleu(predictions, references)

        # Verify our function called NLTK correctly
        mock_corpus_bleu.assert_called_once()
        call_args = mock_corpus_bleu.call_args

        # Check that references were tokenized and formatted correctly for NLTK
        list_of_references, predictions_tokenized = call_args[0]
        assert len(list_of_references) == 2  # Two reference sets
        assert all(isinstance(ref_set, list) for ref_set in list_of_references)
        assert len(predictions_tokenized) == 2  # Two predictions
        assert all(isinstance(pred, list) for pred in predictions_tokenized)

        # Check uniform 4-gram weights were used
        weights_kwarg = call_args[1].get("weights", None)
        expected_weights = (0.25, 0.25, 0.25, 0.25)
        assert weights_kwarg == expected_weights

        # Check our function returns the NLTK value within tolerance
        assert abs(score - expected_score) <= 0.01

    def test_bleu_with_empty_predictions_list(self):
        """Test BLEU returns 0.0 for empty predictions without raising."""
        from assayer.metrics.chat import bleu

        predictions = []
        references = ["hello world"]

        score = bleu(predictions, references)
        assert score == 0.0
        assert isinstance(score, float)

    def test_bleu_with_empty_references_list(self):
        """Test BLEU returns 0.0 for empty references without raising."""
        from assayer.metrics.chat import bleu

        predictions = ["hello world"]
        references = []

        score = bleu(predictions, references)
        assert score == 0.0
        assert isinstance(score, float)

    def test_bleu_with_both_empty_lists(self):
        """Test BLEU returns 0.0 for both empty lists without raising."""
        from assayer.metrics.chat import bleu

        predictions = []
        references = []

        score = bleu(predictions, references)
        assert score == 0.0
        assert isinstance(score, float)

    def test_bleu_tokenizes_on_whitespace(self):
        """Test BLEU uses whitespace tokenization as specified."""
        from assayer.metrics.chat import bleu

        # Use punctuation and ensure it's treated as separate tokens
        predictions = ["hello, world!"]
        references = ["hello, world!"]

        with patch("nltk.translate.bleu_score.corpus_bleu") as mock_corpus_bleu:
            mock_corpus_bleu.return_value = 1.0

            bleu(predictions, references)

            # Verify tokenization happened on whitespace
            call_args = mock_corpus_bleu.call_args[0]
            predictions_tokenized = call_args[1]
            assert predictions_tokenized[0] == ["hello,", "world!"]

    def test_bleu_has_proper_type_hints_and_docstring(self):
        """Test BLEU function has Google-style docstring and type hints."""
        import inspect

        from assayer.metrics.chat import bleu

        # Check function signature has type hints
        sig = inspect.signature(bleu)
        assert len(sig.parameters) == 2

        predictions_param = sig.parameters["predictions"]
        references_param = sig.parameters["references"]

        # Check parameter type hints (this will fail until implementation exists)
        assert predictions_param.annotation == list[str]
        assert references_param.annotation == list[str]
        assert sig.return_annotation == float

        # Check docstring exists and follows Google style
        assert bleu.__doc__ is not None
        assert "Args:" in bleu.__doc__
        assert "Returns:" in bleu.__doc__


class TestROUGELMetric:
    """Test cases for the ROUGE-L metric function."""

    def test_rouge_l_with_perfect_match_single_pair(self):
        """Test ROUGE-L returns 1.0 for identical prediction and reference."""
        from assayer.metrics.chat import rouge_l

        predictions = ["hello world test"]
        references = ["hello world test"]

        score = rouge_l(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert abs(score - 1.0) < 0.01  # Should be very close to 1.0

    def test_rouge_l_with_complete_mismatch_single_pair(self):
        """Test ROUGE-L returns 0.0 for completely different prediction and reference."""
        from assayer.metrics.chat import rouge_l

        predictions = ["hello world"]
        references = ["goodbye earth"]

        score = rouge_l(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score == 0.0  # No common subsequence

    def test_rouge_l_with_partial_overlap_multiple_pairs(self):
        """Test ROUGE-L with multiple prediction-reference pairs with partial overlap."""
        from assayer.metrics.chat import rouge_l

        predictions = [
            "the cat sat on the mat",
            "hello world from python",
            "this is a test sentence",
        ]
        references = [
            "the cat sat on a mat",
            "hello world from java",
            "this is another test sentence",
        ]

        score = rouge_l(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should have some longest common subsequence overlap

    @patch("rouge_score.rouge_scorer.RougeScorer")
    def test_rouge_l_matches_rouge_score_library(self, mock_rouge_scorer_class):
        """Test ROUGE-L output is within ±0.01 of rouge-score library mean fmeasure."""
        from assayer.metrics.chat import rouge_l

        # Mock the RougeScorer instance and its score method
        mock_scorer = MagicMock()
        mock_rouge_scorer_class.return_value = mock_scorer

        # Mock scores for each prediction-reference pair
        mock_score_1 = MagicMock()
        mock_score_1.fmeasure = 0.8
        mock_score_2 = MagicMock()
        mock_score_2.fmeasure = 0.6

        mock_scorer.score.side_effect = [{"rougeL": mock_score_1}, {"rougeL": mock_score_2}]

        predictions = ["hello world", "test sentence"]
        references = ["hello earth", "test phrase"]

        score = rouge_l(predictions, references)

        # Verify RougeScorer was initialized with ["rougeL"]
        mock_rouge_scorer_class.assert_called_once_with(["rougeL"])

        # Verify score was called for each pair
        assert mock_scorer.score.call_count == 2
        expected_calls = [((references[0], predictions[0]),), ((references[1], predictions[1]),)]
        actual_calls = [call[0] for call in mock_scorer.score.call_args_list]
        assert actual_calls == expected_calls

        # Check that mean fmeasure was computed correctly
        expected_mean = (0.8 + 0.6) / 2  # 0.7
        assert abs(score - expected_mean) <= 0.01

    def test_rouge_l_with_empty_predictions_list(self):
        """Test ROUGE-L returns 0.0 for empty predictions without raising."""
        from assayer.metrics.chat import rouge_l

        predictions = []
        references = ["hello world"]

        score = rouge_l(predictions, references)
        assert score == 0.0
        assert isinstance(score, float)

    def test_rouge_l_with_empty_references_list(self):
        """Test ROUGE-L returns 0.0 for empty references without raising."""
        from assayer.metrics.chat import rouge_l

        predictions = ["hello world"]
        references = []

        score = rouge_l(predictions, references)
        assert score == 0.0
        assert isinstance(score, float)

    def test_rouge_l_with_both_empty_lists(self):
        """Test ROUGE-L returns 0.0 for both empty lists without raising."""
        from assayer.metrics.chat import rouge_l

        predictions = []
        references = []

        score = rouge_l(predictions, references)
        assert score == 0.0
        assert isinstance(score, float)

    def test_rouge_l_with_single_word_strings(self):
        """Test ROUGE-L handles single-word strings gracefully."""
        from assayer.metrics.chat import rouge_l

        predictions = ["hello"]
        references = ["world"]

        score = rouge_l(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        # Single words with no overlap should score 0.0
        assert score == 0.0

    def test_rouge_l_with_different_length_predictions_and_references(self):
        """Test ROUGE-L handles predictions longer/shorter than references."""
        from assayer.metrics.chat import rouge_l

        predictions = ["short", "this is a much longer prediction than reference"]
        references = ["this is a much longer reference than prediction", "ref"]

        score = rouge_l(predictions, references)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_rouge_l_has_proper_type_hints_and_docstring(self):
        """Test ROUGE-L function has Google-style docstring and type hints."""
        import inspect

        from assayer.metrics.chat import rouge_l

        # Check function signature has type hints
        sig = inspect.signature(rouge_l)
        assert len(sig.parameters) == 2

        predictions_param = sig.parameters["predictions"]
        references_param = sig.parameters["references"]

        # Check parameter type hints (this will fail until implementation exists)
        assert predictions_param.annotation == list[str]
        assert references_param.annotation == list[str]
        assert sig.return_annotation == float

        # Check docstring exists and follows Google style
        assert rouge_l.__doc__ is not None
        assert "Args:" in rouge_l.__doc__
        assert "Returns:" in rouge_l.__doc__


class TestCrossMetricCompatibility:
    """Test cases that verify both metrics work together."""

    def test_both_metrics_return_same_type(self):
        """Test both metrics return the same type for same inputs."""
        from assayer.metrics.chat import bleu, rouge_l

        predictions = ["hello world"]
        references = ["hello earth"]

        bleu_score = bleu(predictions, references)
        rouge_score = rouge_l(predictions, references)

        assert type(bleu_score) == type(rouge_score) == float

    def test_both_metrics_handle_empty_inputs_consistently(self):
        """Test both metrics handle empty inputs consistently."""
        from assayer.metrics.chat import bleu, rouge_l

        empty_predictions = []
        empty_references = []

        bleu_score = bleu(empty_predictions, empty_references)
        rouge_score = rouge_l(empty_predictions, empty_references)

        assert bleu_score == rouge_score == 0.0

    def test_both_metrics_handle_perfect_match_consistently(self):
        """Test both metrics return high scores for perfect matches."""
        from assayer.metrics.chat import bleu, rouge_l

        predictions = ["the quick brown fox"]
        references = ["the quick brown fox"]

        bleu_score = bleu(predictions, references)
        rouge_score = rouge_l(predictions, references)

        # Both should be very high for perfect match
        assert bleu_score > 0.95
        assert rouge_score > 0.95

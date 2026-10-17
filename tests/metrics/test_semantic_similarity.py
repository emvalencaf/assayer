"""Tests for semantic_similarity metric factory function."""

from unittest.mock import Mock, patch

import numpy as np

from assayer.metrics.chat import make_semantic_similarity


class TestSemanticSimilarity:
    """Test cases for the make_semantic_similarity factory function."""

    def test_default_model_name(self):
        """Test that default model is sentence-transformers/all-MiniLM-L6-v2."""
        # Mock the SentenceTransformer to capture the model_name passed to it
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            # Create a mock encoder instance
            mock_encoder = Mock()
            mock_encoder.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
            mock_transformer.return_value = mock_encoder

            # Create the metric function
            metric_fn = make_semantic_similarity()

            # Call the metric function to trigger model loading
            predictions = ["hello world"]
            references = ["hello world"]
            metric_fn(predictions, references)

            # Verify the default model was used
            mock_transformer.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")

    def test_custom_model_name(self):
        """Test that custom model_name is used instead of the default when provided."""
        custom_model = "custom-sentence-transformer/model"

        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            # Create a mock encoder instance
            mock_encoder = Mock()
            mock_encoder.encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
            mock_transformer.return_value = mock_encoder

            # Create the metric function with custom model
            metric_fn = make_semantic_similarity(model_name=custom_model)

            # Call the metric function to trigger model loading
            predictions = ["hello world"]
            references = ["hello world"]
            metric_fn(predictions, references)

            # Verify the custom model was used
            mock_transformer.assert_called_once_with(custom_model)

    def test_returns_cosine_similarity_in_range(self):
        """Test that returned metric function returns cosine similarity in [0, 1] for non-empty inputs."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            # Create mock encoder with known embeddings
            mock_encoder = Mock()
            # Create embeddings that will result in known cosine similarities
            # Using normalized vectors for easier calculation
            pred_embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])  # orthogonal vectors
            ref_embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])  # same as first prediction

            mock_encoder.encode.side_effect = [pred_embeddings, ref_embeddings]
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello world", "goodbye world"]
            references = ["hello world", "hello world"]

            score = metric_fn(predictions, references)

            # Score should be between 0 and 1
            assert 0.0 <= score <= 1.0
            assert isinstance(score, float)

    def test_identical_strings_high_similarity(self):
        """Test that identical strings produce high cosine similarity."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            mock_encoder = Mock()
            # Identical embeddings for identical strings
            identical_embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])
            mock_encoder.encode.side_effect = [identical_embeddings, identical_embeddings]
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello world", "hello world"]
            references = ["hello world", "hello world"]

            score = metric_fn(predictions, references)

            # Should be very high similarity (close to 1.0)
            assert score > 0.9
            assert 0.0 <= score <= 1.0

    def test_orthogonal_vectors_low_similarity(self):
        """Test that orthogonal vectors produce low cosine similarity."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            mock_encoder = Mock()
            # Orthogonal normalized vectors (cosine similarity = 0)
            pred_embeddings = np.array([[1.0, 0.0]])
            ref_embeddings = np.array([[0.0, 1.0]])
            mock_encoder.encode.side_effect = [pred_embeddings, ref_embeddings]
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello"]
            references = ["world"]

            score = metric_fn(predictions, references)

            # Should be low similarity (close to 0.0 for orthogonal vectors)
            assert score < 0.1
            assert 0.0 <= score <= 1.0

    def test_empty_predictions_returns_zero(self):
        """Test that empty predictions list returns 0.0."""
        metric_fn = make_semantic_similarity()

        predictions = []
        references = ["hello world"]

        score = metric_fn(predictions, references)

        assert score == 0.0

    def test_empty_references_returns_zero(self):
        """Test that empty references list returns 0.0."""
        metric_fn = make_semantic_similarity()

        predictions = ["hello world"]
        references = []

        score = metric_fn(predictions, references)

        assert score == 0.0

    def test_both_empty_returns_zero(self):
        """Test that both empty lists return 0.0."""
        metric_fn = make_semantic_similarity()

        predictions = []
        references = []

        score = metric_fn(predictions, references)

        assert score == 0.0

    def test_single_word_strings(self):
        """Test that single-word strings are handled gracefully."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            mock_encoder = Mock()
            # Mock embeddings for single words
            mock_encoder.encode.side_effect = [
                np.array([[0.5, 0.5]]),  # predictions
                np.array([[0.7, 0.3]]),  # references
            ]
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello"]
            references = ["hi"]

            score = metric_fn(predictions, references)

            assert 0.0 <= score <= 1.0
            assert isinstance(score, float)

    def test_mismatched_list_lengths(self):
        """Test that mismatched prediction/reference list lengths are handled."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            mock_encoder = Mock()
            # Mock embeddings - will be truncated to shorter list
            pred_embeddings = np.array([[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]])
            ref_embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])
            mock_encoder.encode.side_effect = [pred_embeddings, ref_embeddings]
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello", "world", "extra"]
            references = ["hello", "world"]

            score = metric_fn(predictions, references)

            assert 0.0 <= score <= 1.0
            assert isinstance(score, float)

    def test_mean_computation_multiple_pairs(self):
        """Test that the function correctly computes mean cosine similarity across pairs."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            mock_encoder = Mock()
            # Create embeddings with known cosine similarities
            # Pair 1: identical vectors (similarity = 1.0)
            # Pair 2: orthogonal vectors (similarity = 0.0)
            # Mean should be 0.5
            pred_embeddings = np.array([[1.0, 0.0], [1.0, 0.0]])
            ref_embeddings = np.array([[1.0, 0.0], [0.0, 1.0]])
            mock_encoder.encode.side_effect = [pred_embeddings, ref_embeddings]
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello", "world"]
            references = ["hello", "goodbye"]

            score = metric_fn(predictions, references)

            # Should be approximately 0.5 (mean of 1.0 and 0.0)
            assert abs(score - 0.5) < 0.01
            assert 0.0 <= score <= 1.0

    def test_function_signature_and_docstring(self):
        """Test that make_semantic_similarity has proper signature and docstring."""
        import inspect

        # Check function signature
        sig = inspect.signature(make_semantic_similarity)
        params = sig.parameters

        # Should have model_name parameter with default value
        assert "model_name" in params
        assert params["model_name"].default == "sentence-transformers/all-MiniLM-L6-v2"

        # Should have return type annotation
        assert sig.return_annotation is not None

        # Should have docstring
        assert make_semantic_similarity.__doc__ is not None
        assert len(make_semantic_similarity.__doc__.strip()) > 0

    def test_error_handling_model_loading_failure(self):
        """Test that model loading failures are handled gracefully."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            # Simulate model loading failure
            mock_transformer.side_effect = Exception("Model not found")

            # Should not raise exception when creating the metric function
            metric_fn = make_semantic_similarity()

            predictions = ["hello"]
            references = ["world"]

            # Should return 0.0 when model fails to load
            score = metric_fn(predictions, references)
            assert score == 0.0

    def test_error_handling_encoding_failure(self):
        """Test that encoding failures are handled gracefully."""
        with patch("assayer.metrics.chat.SentenceTransformer") as mock_transformer:
            mock_encoder = Mock()
            # Simulate encoding failure
            mock_encoder.encode.side_effect = Exception("Encoding failed")
            mock_transformer.return_value = mock_encoder

            metric_fn = make_semantic_similarity()

            predictions = ["hello"]
            references = ["world"]

            # Should return 0.0 when encoding fails
            score = metric_fn(predictions, references)
            assert score == 0.0

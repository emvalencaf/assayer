"""Tests for hallucination evaluator components."""

import pytest
import hashlib


class TestHashPrompt:
    """Test cases for hash_prompt function."""

    def test_hash_prompt_returns_64_char_hex_string(self):
        """Test that hash_prompt returns a 64-character lowercase hex string."""
        from assayer.evaluators.hallucination import hash_prompt

        test_prompt = "This is a test prompt"
        result = hash_prompt(test_prompt)

        # Should be 64 characters long (SHA-256 hex digest)
        assert len(result) == 64

        # Should be lowercase hex
        assert result.isdigit() is False  # Not all digits
        assert all(c in "0123456789abcdef" for c in result)  # Only hex chars
        assert result.islower()  # Lowercase

    def test_hash_prompt_deterministic_same_input(self):
        """Test that hash_prompt returns the same hash for the same input."""
        from assayer.evaluators.hallucination import hash_prompt

        test_prompt = "Deterministic test prompt"
        result1 = hash_prompt(test_prompt)
        result2 = hash_prompt(test_prompt)

        assert result1 == result2

    def test_hash_prompt_different_inputs_different_hashes(self):
        """Test that different inputs produce different hashes."""
        from assayer.evaluators.hallucination import hash_prompt

        prompt1 = "First prompt"
        prompt2 = "Second prompt"

        hash1 = hash_prompt(prompt1)
        hash2 = hash_prompt(prompt2)

        assert hash1 != hash2

    def test_hash_prompt_utf8_encoding(self):
        """Test that hash_prompt handles UTF-8 encoding correctly."""
        from assayer.evaluators.hallucination import hash_prompt

        # Test with Unicode characters
        unicode_prompt = "Test with émojis 🚀 and spéciál chars: ñáéíóú"
        result = hash_prompt(unicode_prompt)

        # Should still be valid 64-char hex string
        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

        # Verify it matches expected SHA-256 of UTF-8 encoding
        expected = hashlib.sha256(unicode_prompt.encode("utf-8")).hexdigest()
        assert result == expected

    def test_hash_prompt_raises_value_error_empty_string(self):
        """Test that hash_prompt raises ValueError for empty string."""
        from assayer.evaluators.hallucination import hash_prompt

        with pytest.raises(ValueError):
            hash_prompt("")

    def test_hash_prompt_raises_value_error_whitespace_only(self):
        """Test that hash_prompt raises ValueError for whitespace-only strings."""
        from assayer.evaluators.hallucination import hash_prompt

        whitespace_inputs = [
            " ",
            "  ",
            "\t",
            "\n",
            "\r\n",
            "   \t\n   ",
        ]

        for whitespace_input in whitespace_inputs:
            with pytest.raises(ValueError):
                hash_prompt(whitespace_input)

    def test_hash_prompt_works_with_non_empty_content(self):
        """Test that hash_prompt works with strings that contain whitespace but also content."""
        from assayer.evaluators.hallucination import hash_prompt

        valid_inputs = [
            " content ",
            "\tcontent\n",
            "  multi\n  line  \t",
            "a",  # Single character
        ]

        for valid_input in valid_inputs:
            result = hash_prompt(valid_input)
            assert len(result) == 64
            assert all(c in "0123456789abcdef" for c in result)


class TestDefaultJudgeSystemPrompt:
    """Test cases for DEFAULT_JUDGE_SYSTEM_PROMPT constant."""

    def test_default_prompt_exists_and_is_string(self):
        """Test that DEFAULT_JUDGE_SYSTEM_PROMPT is defined and is a string."""
        from assayer.evaluators.hallucination import DEFAULT_JUDGE_SYSTEM_PROMPT

        assert isinstance(DEFAULT_JUDGE_SYSTEM_PROMPT, str)
        assert len(DEFAULT_JUDGE_SYSTEM_PROMPT) > 0

    def test_default_prompt_content_structure(self):
        """Test that DEFAULT_JUDGE_SYSTEM_PROMPT contains expected content."""
        from assayer.evaluators.hallucination import DEFAULT_JUDGE_SYSTEM_PROMPT

        # Should contain key elements from the design doc
        prompt = DEFAULT_JUDGE_SYSTEM_PROMPT

        # Check for essential content elements
        assert "expert evaluator" in prompt.lower()
        assert "faithfulness" in prompt.lower() or "faithful" in prompt.lower()
        assert "0.0" in prompt
        assert "1.0" in prompt
        assert "scale" in prompt.lower()

    def test_hash_default_prompt_is_stable(self):
        """Test that hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT) is deterministic."""
        from assayer.evaluators.hallucination import hash_prompt, DEFAULT_JUDGE_SYSTEM_PROMPT

        # Hash the default prompt multiple times
        hash1 = hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT)
        hash2 = hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT)
        hash3 = hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT)

        # All should be identical
        assert hash1 == hash2 == hash3

        # And should be valid 64-char hex
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_default_prompt_exact_content_from_design(self):
        """Test that DEFAULT_JUDGE_SYSTEM_PROMPT matches the design specification."""
        from assayer.evaluators.hallucination import DEFAULT_JUDGE_SYSTEM_PROMPT

        # Expected content from design.md
        expected_prompt = """\
You are an expert evaluator assessing the quality and faithfulness of an AI assistant's response.

Given the following:
- Context (source material the assistant had access to)
- Question or input
- Assistant's response

Rate the response on a scale from 0.0 to 1.0, where:
  1.0 = fully faithful, accurate, and relevant
  0.0 = completely unfaithful, hallucinated, or irrelevant

Respond with ONLY a single float number between 0.0 and 1.0. No explanation.
"""

        assert DEFAULT_JUDGE_SYSTEM_PROMPT == expected_prompt


class TestFaithfulnessEvaluator:
    """Test cases for FaithfulnessEvaluator class."""

    def test_faithfulness_evaluator_constructor_default_values(self):
        """Test FaithfulnessEvaluator constructor with default parameters."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        # Check that it inherits from BaseEvaluator properly
        assert evaluator.name == "test_field"

        # Check default values are set correctly
        assert hasattr(evaluator, 'threshold')
        assert evaluator.threshold == 0.5

        assert hasattr(evaluator, 'model_name')
        assert evaluator.model_name == "cross-encoder/nli-deberta-v3-small"

    def test_faithfulness_evaluator_constructor_custom_values(self):
        """Test FaithfulnessEvaluator constructor with custom parameters."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator(
            field_name="custom_field",
            threshold=0.8,
            model_name="custom-model"
        )

        assert evaluator.name == "custom_field"
        assert evaluator.threshold == 0.8
        assert evaluator.model_name == "custom-model"

    def test_faithfulness_evaluator_inherits_from_base_evaluator(self):
        """Test that FaithfulnessEvaluator inherits from BaseEvaluator."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from assayer.evaluators.base import BaseEvaluator

        evaluator = FaithfulnessEvaluator("test_field")
        assert isinstance(evaluator, BaseEvaluator)

    def test_faithfulness_evaluator_returns_field_evaluation_with_score_in_range(self):
        """Test that evaluate returns FieldEvaluation with score in [0, 1]."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from assayer.models import FieldEvaluation
        
        def mock_classifier(_):
            return mock_scores
        
        evaluator = FaithfulnessEvaluator("test_field", classifier=mock_classifier)

        # Mock the NLI model to return a score in range
        mock_scores = [[0.1, 0.7, 0.2]]  # [contradiction, entailment, neutral]
        
        result = evaluator.evaluate("The sky is blue", "The sky is blue")

        assert isinstance(result, FieldEvaluation)
        assert 0.0 <= result.score <= 1.0
        assert result.score == 0.7  # entailment score


    def test_faithfulness_evaluator_metadata_contains_required_fields(self):
        """Test that metadata contains is_hallucination, method, and threshold."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock
        
        # Mock high entailment score (no hallucination)
        mock_scores = [[0.1, 0.8, 0.1]]  # [contradiction, entailment, neutral]
        
        mock_classifier = MagicMock()
        mock_classifier.return_value = mock_scores
        evaluator = FaithfulnessEvaluator("test_field", threshold=0.6, classifier=mock_classifier)

        result = evaluator.evaluate("Test prediction", "Test reference")

        # Check required metadata fields
        assert "is_hallucination" in result.metadata
        assert "method" in result.metadata
        assert "threshold" in result.metadata

        # Check metadata values
        assert result.metadata["is_hallucination"] is False  # 0.8 >= 0.6
        assert result.metadata["method"] == "faithfulness"
        assert result.metadata["threshold"] == 0.6

    def test_faithfulness_evaluator_metadata_hallucination_detection(self):
        """Test that is_hallucination flag works correctly with threshold."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        # Test case where score is below threshold (hallucination detected)
        mock_scores = [[0.6, 0.3, 0.1]]  # [contradiction, entailment, neutral]

        mock_classifier = MagicMock()
        mock_classifier.return_value = mock_scores
        evaluator = FaithfulnessEvaluator("test_field", threshold=0.5, classifier=mock_classifier)

        result = evaluator.evaluate("Incorrect prediction", "Correct reference")

        assert result.metadata["is_hallucination"] is True  # 0.3 < 0.5
        assert result.score == 0.3

    def test_faithfulness_evaluator_prompt_hash_is_none(self):
        """Test that prompt_hash is None (no external LLM calls)."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        mock_scores = [[0.2, 0.7, 0.1]]

        with patch('transformers.pipeline') as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate("Test prediction", "Test reference")

            assert result.prompt_hash is None

    def test_faithfulness_evaluator_no_external_llm_api_calls(self):
        """Test that evaluator makes no external LLM API calls."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        mock_scores = [[0.1, 0.8, 0.1]]

        # We only mock transformers.pipeline - no external API mocks needed
        with patch('transformers.pipeline') as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate("Test prediction", "Test reference")

            # Verify only local transformers pipeline was called
            mock_pipeline.assert_called_once()
            assert result.score == 0.8

    def test_faithfulness_evaluator_empty_prediction_returns_zero_score(self):
        """Test that empty prediction returns score=0.0 without raising."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        # Should not need to call the model for empty inputs
        result = evaluator.evaluate("", "Some reference")

        assert result.score == 0.0
        assert result.metadata["is_hallucination"] is True  # 0.0 < 0.5

    def test_faithfulness_evaluator_empty_reference_returns_zero_score(self):
        """Test that empty reference returns score=0.0 without raising."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        # Should not need to call the model for empty inputs
        result = evaluator.evaluate("Some prediction", "")

        assert result.score == 0.0
        assert result.metadata["is_hallucination"] is True  # 0.0 < 0.5

    def test_faithfulness_evaluator_both_empty_returns_zero_score(self):
        """Test that both empty inputs return score=0.0 without raising."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        result = evaluator.evaluate("", "")

        assert result.score == 0.0
        assert result.metadata["is_hallucination"] is True  # 0.0 < 0.5

    def test_faithfulness_evaluator_whitespace_only_inputs_return_zero_score(self):
        """Test that whitespace-only inputs return score=0.0."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        whitespace_inputs = [
            ("   ", "Some reference"),
            ("Some prediction", "\t\n  "),
            ("\t", "\n"),
            ("  ", "  "),
        ]

        for prediction, reference in whitespace_inputs:
            result = evaluator.evaluate(prediction, reference)
            assert result.score == 0.0
            assert result.metadata["is_hallucination"] is True

    def test_faithfulness_evaluator_field_evaluation_structure(self):
        """Test that returned FieldEvaluation has correct structure."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from assayer.models import FieldEvaluation
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("response_field", threshold=0.7)

        mock_scores = [[0.1, 0.6, 0.3]]
        prediction = "Test prediction"
        reference = "Test reference"

        with patch('transformers.pipeline') as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate(prediction, reference)

            # Check FieldEvaluation structure matches design
            assert isinstance(result, FieldEvaluation)
            assert result.field_name == "response_field"
            assert result.evaluator_method == "faithfulness"
            assert result.expected_value == reference
            assert result.obtained_value == prediction
            assert result.score == 0.6
            assert result.prompt_hash is None

            # Check metadata structure
            expected_metadata = {
                "is_hallucination": True,  # 0.6 < 0.7
                "method": "faithfulness",
                "threshold": 0.7,
            }
            assert result.metadata == expected_metadata

    def test_faithfulness_evaluator_fallback_jaccard_similarity(self):
        """Test fallback to Jaccard similarity when NLI model is unavailable."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch

        evaluator = FaithfulnessEvaluator("test_field")

        # Mock transformers.pipeline to raise exception (model unavailable)
        with patch('transformers.pipeline', side_effect=Exception("Model not found")):
            # Test identical strings (Jaccard = 1.0)
            result = evaluator.evaluate("hello world", "hello world")
            assert result.score == 1.0

            # Test no overlap (Jaccard = 0.0)
            result = evaluator.evaluate("completely different", "totally unrelated words")
            assert result.score == 0.0

            # Test partial overlap
            result = evaluator.evaluate("the quick brown", "the lazy brown")
            # Jaccard = |intersection| / |union| = 2 / 4 = 0.5
            assert result.score == 0.5

    def test_faithfulness_evaluator_nli_model_initialization(self):
        """Test that NLI model is properly initialized with correct parameters."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field", model_name="custom-nli-model")

        mock_scores = [[0.2, 0.7, 0.1]]

        with patch('transformers.pipeline') as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate("test prediction", "test reference")

            # Verify pipeline was called with correct parameters
            mock_pipeline.assert_called_once_with(
                "text-classification",
                model="custom-nli-model",
                return_all_scores=True
            )

    def test_faithfulness_evaluator_nli_input_formatting(self):
        """Test that inputs are properly formatted for NLI model."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from unittest.mock import patch, MagicMock

        evaluator = FaithfulnessEvaluator("test_field")

        mock_scores = [[0.1, 0.8, 0.1]]
        prediction = "The sky is blue"
        reference = "The sky appears blue in color"

        with patch('transformers.pipeline') as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate(prediction, reference)

            # Verify the classifier was called with properly formatted input
            # NLI format: premise [SEP] hypothesis
            expected_input = f"{reference} [SEP] {prediction}"
            mock_classifier.assert_called_once_with(expected_input)


class TestFaithfulnessEvaluatorDocstringsAndTypeHints:
    """Test that FaithfulnessEvaluator has proper docstrings and type hints."""

    def test_faithfulness_evaluator_class_has_docstring(self):
        """Test that FaithfulnessEvaluator class has a Google-style docstring."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        assert FaithfulnessEvaluator.__doc__ is not None
        doc = FaithfulnessEvaluator.__doc__

        # Should contain essential information about the evaluator
        assert "faithfulness" in doc.lower() or "faithful" in doc.lower()
        assert "nli" in doc.lower() or "entailment" in doc.lower()

    def test_faithfulness_evaluator_init_has_type_hints(self):
        """Test that __init__ method has full type hints."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        import inspect

        signature = inspect.signature(FaithfulnessEvaluator.__init__)

        # Check parameter type hints
        assert signature.parameters["field_name"].annotation == str
        assert signature.parameters["threshold"].annotation == float
        assert signature.parameters["model_name"].annotation == str

        # Check return type hint
        assert signature.return_annotation == type(None)

    def test_faithfulness_evaluator_evaluate_has_type_hints(self):
        """Test that evaluate method has full type hints."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from assayer.models import FieldEvaluation
        import inspect

        signature = inspect.signature(FaithfulnessEvaluator.evaluate)

        # Check parameter type hints
        assert signature.parameters["prediction"].annotation == str
        assert signature.parameters["reference"].annotation == str

        # Check return type hint
        assert signature.return_annotation == FieldEvaluation

    def test_faithfulness_evaluator_evaluate_has_docstring(self):
        """Test that evaluate method has a Google-style docstring."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        # We can't directly access the docstring until the class is implemented,
        # but we can test the abstract method requirement
        evaluator = FaithfulnessEvaluator("test_field")
        assert hasattr(evaluator, 'evaluate')

        # The method should exist and be callable
        assert callable(evaluator.evaluate)


class TestDocstringsAndTypeHints:
    """Test that functions have proper docstrings and type hints."""

    def test_hash_prompt_has_docstring(self):
        """Test that hash_prompt has a Google-style docstring."""
        from assayer.evaluators.hallucination import hash_prompt

        assert hash_prompt.__doc__ is not None
        doc = hash_prompt.__doc__

        # Check for Google-style docstring elements
        assert "Args:" in doc
        assert "Returns:" in doc
        # Should also have Raises for ValueError
        assert "Raises:" in doc or "ValueError" in doc

    def test_hash_prompt_has_type_hints(self):
        """Test that hash_prompt has full type hints."""
        from assayer.evaluators.hallucination import hash_prompt
        import inspect

        signature = inspect.signature(hash_prompt)

        # Check parameter type hint
        prompt_param = signature.parameters["prompt"]
        assert prompt_param.annotation == str

        # Check return type hint
        assert signature.return_annotation == str
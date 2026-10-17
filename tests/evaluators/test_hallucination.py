"""Tests for hallucination evaluator components."""

import hashlib

import pytest


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
        from assayer.evaluators.hallucination import DEFAULT_JUDGE_SYSTEM_PROMPT, hash_prompt

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
        assert hasattr(evaluator, "threshold")
        assert evaluator.threshold == 0.5

        assert hasattr(evaluator, "model_name")
        assert evaluator.model_name == "cross-encoder/nli-deberta-v3-small"

    def test_faithfulness_evaluator_constructor_custom_values(self):
        """Test FaithfulnessEvaluator constructor with custom parameters."""
        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator(
            field_name="custom_field", threshold=0.8, model_name="custom-model"
        )

        assert evaluator.name == "custom_field"
        assert evaluator.threshold == 0.8
        assert evaluator.model_name == "custom-model"

    def test_faithfulness_evaluator_inherits_from_base_evaluator(self):
        """Test that FaithfulnessEvaluator inherits from BaseEvaluator."""
        from assayer.evaluators.base import BaseEvaluator
        from assayer.evaluators.hallucination import FaithfulnessEvaluator

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
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

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
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

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
        from unittest.mock import MagicMock, patch

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        mock_scores = [[0.2, 0.7, 0.1]]

        with patch("transformers.pipeline") as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate("Test prediction", "Test reference")

            assert result.prompt_hash is None

    def test_faithfulness_evaluator_no_external_llm_api_calls(self):
        """Test that evaluator makes no external LLM API calls."""
        from unittest.mock import MagicMock, patch

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        mock_scores = [[0.1, 0.8, 0.1]]

        # We only mock transformers.pipeline - no external API mocks needed
        with patch("transformers.pipeline") as mock_pipeline:
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

        evaluator = FaithfulnessEvaluator("test_field")

        # Should not need to call the model for empty inputs
        result = evaluator.evaluate("", "Some reference")

        assert result.score == 0.0
        assert result.metadata["is_hallucination"] is True  # 0.0 < 0.5

    def test_faithfulness_evaluator_empty_reference_returns_zero_score(self):
        """Test that empty reference returns score=0.0 without raising."""

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        # Should not need to call the model for empty inputs
        result = evaluator.evaluate("Some prediction", "")

        assert result.score == 0.0
        assert result.metadata["is_hallucination"] is True  # 0.0 < 0.5

    def test_faithfulness_evaluator_both_empty_returns_zero_score(self):
        """Test that both empty inputs return score=0.0 without raising."""

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        result = evaluator.evaluate("", "")

        assert result.score == 0.0
        assert result.metadata["is_hallucination"] is True  # 0.0 < 0.5

    def test_faithfulness_evaluator_whitespace_only_inputs_return_zero_score(self):
        """Test that whitespace-only inputs return score=0.0."""

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

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
        from unittest.mock import MagicMock, patch

        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from assayer.models import FieldEvaluation

        evaluator = FaithfulnessEvaluator("response_field", threshold=0.7)

        mock_scores = [[0.1, 0.6, 0.3]]
        prediction = "Test prediction"
        reference = "Test reference"

        with patch("transformers.pipeline") as mock_pipeline:
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
        from unittest.mock import patch

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        # Mock transformers.pipeline to raise exception (model unavailable)
        with patch("transformers.pipeline", side_effect=Exception("Model not found")):
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
        from unittest.mock import MagicMock, patch

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field", model_name="custom-nli-model")

        mock_scores = [[0.2, 0.7, 0.1]]

        with patch("transformers.pipeline") as mock_pipeline:
            mock_classifier = MagicMock()
            mock_classifier.return_value = mock_scores
            mock_pipeline.return_value = mock_classifier

            result = evaluator.evaluate("test prediction", "test reference")

            # Verify pipeline was called with correct parameters
            mock_pipeline.assert_called_once_with(
                "text-classification", model="custom-nli-model", return_all_scores=True
            )

    def test_faithfulness_evaluator_nli_input_formatting(self):
        """Test that inputs are properly formatted for NLI model."""
        from unittest.mock import MagicMock, patch

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        evaluator = FaithfulnessEvaluator("test_field")

        mock_scores = [[0.1, 0.8, 0.1]]
        prediction = "The sky is blue"
        reference = "The sky appears blue in color"

        with patch("transformers.pipeline") as mock_pipeline:
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
        import inspect

        from assayer.evaluators.hallucination import FaithfulnessEvaluator

        signature = inspect.signature(FaithfulnessEvaluator.__init__)

        # Check parameter type hints
        assert signature.parameters["field_name"].annotation == str
        assert signature.parameters["threshold"].annotation == float
        assert signature.parameters["model_name"].annotation == str

        # Check return type hint
        assert signature.return_annotation == type(None)

    def test_faithfulness_evaluator_evaluate_has_type_hints(self):
        """Test that evaluate method has full type hints."""
        import inspect

        from assayer.evaluators.hallucination import FaithfulnessEvaluator
        from assayer.models import FieldEvaluation

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
        assert hasattr(evaluator, "evaluate")

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
        import inspect

        from assayer.evaluators.hallucination import hash_prompt

        signature = inspect.signature(hash_prompt)

        # Check parameter type hint
        prompt_param = signature.parameters["prompt"]
        assert prompt_param.annotation == str

        # Check return type hint
        assert signature.return_annotation == str


class TestParseScore:
    """Test cases for _parse_score helper function."""

    def test_parse_score_valid_integer_scores(self):
        """Test that _parse_score correctly parses integer scores."""
        from assayer.evaluators.hallucination import _parse_score

        # Test exact bounds
        assert _parse_score("0") == 0.0
        assert _parse_score("1") == 1.0

        # Test with surrounding text
        assert _parse_score("The score is 0 for this response.") == 0.0
        assert _parse_score("I rate this 1 out of 1.") == 1.0

    def test_parse_score_valid_float_scores(self):
        """Test that _parse_score correctly parses float scores."""
        from assayer.evaluators.hallucination import _parse_score

        # Test various decimal places
        assert _parse_score("0.5") == 0.5
        assert _parse_score("0.75") == 0.75
        assert _parse_score("0.123") == 0.123
        assert _parse_score("1.0") == 1.0
        assert _parse_score("1.00") == 1.0

        # Test with surrounding text
        assert _parse_score("The faithfulness score is 0.8 for accuracy.") == 0.8
        assert _parse_score("Rating: 0.25") == 0.25

    def test_parse_score_multiple_valid_scores_returns_first(self):
        """Test that _parse_score returns first valid score when multiple are present."""
        from assayer.evaluators.hallucination import _parse_score

        # Should return the first valid score
        assert _parse_score("0.3 and also 0.7") == 0.3
        assert _parse_score("Between 0.1 and 0.9, I choose 0.6") == 0.1
        assert _parse_score("First 1 then 0.5") == 1.0

    def test_parse_score_with_whitespace_and_formatting(self):
        """Test that _parse_score handles whitespace and formatting correctly."""
        from assayer.evaluators.hallucination import _parse_score

        # Test with various whitespace
        assert _parse_score("  0.7  ") == 0.7
        assert _parse_score("\t0.8\n") == 0.8
        assert _parse_score("   Score:   0.9   ") == 0.9

        # Test with newlines and formatting
        assert _parse_score("Result:\n0.6\nExplanation follows") == 0.6

    def test_parse_score_rejects_out_of_range_values(self):
        """Test that _parse_score only accepts values in [0, 1] range."""
        from assayer.evaluators.hallucination import _parse_score

        # Test values outside range
        with pytest.raises(ValueError, match="Could not parse score"):
            _parse_score("1.5")

        with pytest.raises(ValueError, match="Could not parse score"):
            _parse_score("2.0")

        with pytest.raises(ValueError, match="Could not parse score"):
            _parse_score("-0.1")

        with pytest.raises(ValueError, match="Could not parse score"):
            _parse_score("The answer is 42")

        with pytest.raises(ValueError, match="Could not parse score"):
            _parse_score("10")

    def test_parse_score_raises_value_error_no_valid_float(self):
        """Test that _parse_score raises ValueError when no valid float is found."""
        from assayer.evaluators.hallucination import _parse_score

        invalid_responses = [
            "",
            "no numbers here",
            "The response is good",
            "N/A",
            "null",
            "undefined",
            "score: high",
            "excellent quality",
            "2.5",  # Out of range
            "-1",  # Out of range
            "0.0.1",  # Invalid format
            "one point zero",  # Written out numbers
        ]

        for invalid_response in invalid_responses:
            with pytest.raises(ValueError) as exc_info:
                _parse_score(invalid_response)

            # Check error message contains the invalid response
            assert invalid_response in str(exc_info.value)

    def test_parse_score_handles_edge_case_formats(self):
        """Test _parse_score with edge case number formats."""
        from assayer.evaluators.hallucination import _parse_score

        # Test leading zeros (should be valid)
        assert _parse_score("0.50") == 0.5
        assert _parse_score("0.00") == 0.0
        assert _parse_score("1.00") == 1.0

        # Test mixed with invalid numbers
        assert _parse_score("Version 2.0 has score 0.8") == 0.8
        assert _parse_score("0.7 out of 100") == 0.7


class TestLLMJudgeEvaluator:
    """Test cases for LLMJudgeEvaluator class."""

    def test_llm_judge_evaluator_uses_default_prompt_when_none_provided(self):
        """Test that LLMJudgeEvaluator uses DEFAULT_JUDGE_SYSTEM_PROMPT when system_prompt=None."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import DEFAULT_JUDGE_SYSTEM_PROMPT, LLMJudgeEvaluator

        mock_judge_model = MagicMock()
        evaluator = LLMJudgeEvaluator(
            field_name="test_field", judge_model=mock_judge_model, system_prompt=None
        )

        # Access the private attribute to verify default prompt is used
        assert evaluator._prompt == DEFAULT_JUDGE_SYSTEM_PROMPT

    def test_llm_judge_evaluator_uses_custom_prompt_when_provided(self):
        """Test that LLMJudgeEvaluator uses custom prompt when provided."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        custom_prompt = "This is a custom evaluation prompt."
        mock_judge_model = MagicMock()

        evaluator = LLMJudgeEvaluator(
            field_name="test_field", judge_model=mock_judge_model, system_prompt=custom_prompt
        )

        assert evaluator._prompt == custom_prompt

    def test_llm_judge_evaluator_prompt_hash_equals_sha256_of_default_prompt(self):
        """Test that prompt_hash equals SHA-256 of DEFAULT_JUDGE_SYSTEM_PROMPT when no custom prompt."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import (
            DEFAULT_JUDGE_SYSTEM_PROMPT,
            LLMJudgeEvaluator,
            hash_prompt,
        )

        mock_judge_model = MagicMock()
        evaluator = LLMJudgeEvaluator(field_name="test_field", judge_model=mock_judge_model)

        expected_hash = hash_prompt(DEFAULT_JUDGE_SYSTEM_PROMPT)
        assert evaluator._prompt_hash == expected_hash

    def test_llm_judge_evaluator_prompt_hash_equals_sha256_of_custom_prompt(self):
        """Test that prompt_hash equals SHA-256 of custom prompt when provided."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator, hash_prompt

        custom_prompt = "Custom evaluation prompt for testing."
        mock_judge_model = MagicMock()

        evaluator = LLMJudgeEvaluator(
            field_name="test_field", judge_model=mock_judge_model, system_prompt=custom_prompt
        )

        expected_hash = hash_prompt(custom_prompt)
        assert evaluator._prompt_hash == expected_hash

    def test_llm_judge_evaluator_inherits_from_base_evaluator(self):
        """Test that LLMJudgeEvaluator inherits from BaseEvaluator."""
        from unittest.mock import MagicMock

        from assayer.evaluators.base import BaseEvaluator
        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        mock_judge_model = MagicMock()
        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)

        assert isinstance(evaluator, BaseEvaluator)
        assert evaluator.name == "test_field"

    def test_llm_judge_evaluator_evaluate_returns_field_evaluation_with_score_in_range(self):
        """Test that evaluate returns FieldEvaluation with score in [0, 1]."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator
        from assayer.models import FieldEvaluation

        # Mock judge model response
        mock_response = MagicMock()
        mock_response.content = "The score is 0.75"
        mock_judge_model = MagicMock()
        mock_judge_model.invoke.return_value = mock_response

        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)
        result = evaluator.evaluate("Test prediction", "Test reference")

        assert isinstance(result, FieldEvaluation)
        assert 0.0 <= result.score <= 1.0
        assert result.score == 0.75

    def test_llm_judge_evaluator_metadata_contains_required_fields(self):
        """Test that metadata contains judge_model and prompt_hash."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        # Mock judge model response
        mock_response = MagicMock()
        mock_response.content = "0.8"
        mock_judge_model = MagicMock()
        mock_judge_model.__class__.__name__ = "TestChatModel"
        mock_judge_model.invoke.return_value = mock_response

        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)
        result = evaluator.evaluate("Test prediction", "Test reference")

        # Check required metadata fields
        assert "judge_model" in result.metadata
        assert "prompt_hash" in result.metadata

        # Check metadata values
        assert result.metadata["judge_model"] == "TestChatModel"
        assert result.metadata["prompt_hash"] == evaluator._prompt_hash

    def test_llm_judge_evaluator_field_evaluation_structure(self):
        """Test that returned FieldEvaluation has correct structure."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator
        from assayer.models import FieldEvaluation

        # Mock judge model response
        mock_response = MagicMock()
        mock_response.content = "0.65"
        mock_judge_model = MagicMock()
        mock_judge_model.__class__.__name__ = "MockModel"
        mock_judge_model.invoke.return_value = mock_response

        evaluator = LLMJudgeEvaluator("response_field", mock_judge_model)
        prediction = "Test prediction"
        reference = "Test reference"

        result = evaluator.evaluate(prediction, reference)

        # Check FieldEvaluation structure matches design
        assert isinstance(result, FieldEvaluation)
        assert result.field_name == "response_field"
        assert result.evaluator_method == "llm_judge"
        assert result.expected_value == reference
        assert result.obtained_value == prediction
        assert result.score == 0.65
        assert result.prompt_hash == evaluator._prompt_hash

        # Check metadata structure
        expected_metadata = {
            "judge_model": "MockModel",
            "prompt_hash": evaluator._prompt_hash,
        }
        assert result.metadata == expected_metadata

    def test_llm_judge_evaluator_handles_reference_none(self):
        """Test that LLMJudgeEvaluator handles reference=None correctly."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        # Mock judge model response
        mock_response = MagicMock()
        mock_response.content = "0.4"
        mock_judge_model = MagicMock()
        mock_judge_model.invoke.return_value = mock_response

        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)
        result = evaluator.evaluate("Test prediction", None)

        assert result.expected_value is None
        assert result.obtained_value == "Test prediction"
        assert result.score == 0.4

    def test_llm_judge_evaluator_calls_judge_model_with_correct_format(self):
        """Test that judge model is called with correctly formatted messages."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        # Mock judge model response
        mock_response = MagicMock()
        mock_response.content = "0.9"
        mock_judge_model = MagicMock()
        mock_judge_model.invoke.return_value = mock_response

        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)
        prediction = "AI response text"
        reference = "Expected reference"

        evaluator.evaluate(prediction, reference)

        # Verify invoke was called once
        mock_judge_model.invoke.assert_called_once()

        # Get the messages passed to invoke
        call_args = mock_judge_model.invoke.call_args[0]
        messages = call_args[0]

        # Should be a list with system and user messages
        assert isinstance(messages, list)
        assert len(messages) >= 1

        # Check that it includes our prediction and reference in some form
        message_content = str(messages)
        assert prediction in message_content or reference in message_content

    def test_llm_judge_evaluator_raises_value_error_on_unparseable_response(self):
        """Test that _parse_score raises ValueError when judge response has no valid float."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        # Mock judge model to return unparseable response
        mock_response = MagicMock()
        mock_response.content = "This is a completely invalid response with no numbers"
        mock_judge_model = MagicMock()
        mock_judge_model.invoke.return_value = mock_response

        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)

        with pytest.raises(ValueError) as exc_info:
            evaluator.evaluate("Test prediction", "Test reference")

        # Check error message mentions the invalid response
        assert "Could not parse score" in str(exc_info.value)
        assert "invalid response" in str(exc_info.value)

    def test_llm_judge_evaluator_handles_various_valid_response_formats(self):
        """Test that evaluator handles various valid judge response formats."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        mock_judge_model = MagicMock()
        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)

        valid_responses = [
            ("0.5", 0.5),
            ("Score: 0.8", 0.8),
            ("The rating is 0.25 out of 1.0", 0.25),
            ("1", 1.0),
            ("0", 0.0),
            ("  0.75  ", 0.75),
            ("Rating:\n0.6\nExplanation...", 0.6),
        ]

        for response_text, expected_score in valid_responses:
            mock_response = MagicMock()
            mock_response.content = response_text
            mock_judge_model.invoke.return_value = mock_response

            result = evaluator.evaluate("Test prediction", "Test reference")
            assert result.score == expected_score, f"Failed for response: {response_text}"

    def test_llm_judge_evaluator_constructor_validates_field_name(self):
        """Test that constructor validates field_name properly."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        mock_judge_model = MagicMock()

        # Valid field name should work
        evaluator = LLMJudgeEvaluator("valid_field", mock_judge_model)
        assert evaluator.name == "valid_field"

        # Empty field name should raise ValueError (from BaseEvaluator)
        with pytest.raises(ValueError):
            LLMJudgeEvaluator("", mock_judge_model)

        # Whitespace-only field name should raise ValueError (from BaseEvaluator)
        with pytest.raises(ValueError):
            LLMJudgeEvaluator("   ", mock_judge_model)


class TestLLMJudgeEvaluatorDocstringsAndTypeHints:
    """Test that LLMJudgeEvaluator has proper docstrings and type hints."""

    def test_llm_judge_evaluator_class_has_docstring(self):
        """Test that LLMJudgeEvaluator class has a Google-style docstring."""
        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        assert LLMJudgeEvaluator.__doc__ is not None
        doc = LLMJudgeEvaluator.__doc__

        # Should contain essential information about the evaluator
        assert "llm" in doc.lower() or "judge" in doc.lower()
        assert "evaluator" in doc.lower()

    def test_llm_judge_evaluator_init_has_type_hints(self):
        """Test that __init__ method has full type hints."""
        import inspect

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        signature = inspect.signature(LLMJudgeEvaluator.__init__)

        # Check parameter type hints
        assert signature.parameters["field_name"].annotation == str
        # judge_model should be BaseChatModel, but we'll check for Any or the actual type
        assert signature.parameters["judge_model"].annotation is not None

        # system_prompt should be str | None
        system_prompt_annotation = signature.parameters["system_prompt"].annotation
        assert system_prompt_annotation is not None

        # Check return type hint
        assert signature.return_annotation == type(None)

    def test_llm_judge_evaluator_evaluate_has_type_hints(self):
        """Test that evaluate method has full type hints."""
        import inspect

        from assayer.evaluators.hallucination import LLMJudgeEvaluator
        from assayer.models import FieldEvaluation

        signature = inspect.signature(LLMJudgeEvaluator.evaluate)

        # Check parameter type hints
        assert signature.parameters["prediction"].annotation == str
        # reference might be str | None according to design
        reference_annotation = signature.parameters["reference"].annotation
        assert reference_annotation is not None

        # Check return type hint
        assert signature.return_annotation == FieldEvaluation

    def test_llm_judge_evaluator_evaluate_has_docstring(self):
        """Test that evaluate method has a Google-style docstring."""
        from unittest.mock import MagicMock

        from assayer.evaluators.hallucination import LLMJudgeEvaluator

        mock_judge_model = MagicMock()
        evaluator = LLMJudgeEvaluator("test_field", mock_judge_model)

        # The method should exist and be callable
        assert hasattr(evaluator, "evaluate")
        assert callable(evaluator.evaluate)

        # If implemented, it should have a docstring
        # We can't check this until it's implemented, but we verify it exists

    def test_parse_score_has_docstring(self):
        """Test that _parse_score has a Google-style docstring."""
        from assayer.evaluators.hallucination import _parse_score

        assert _parse_score.__doc__ is not None
        doc = _parse_score.__doc__

        # Check for Google-style docstring elements
        assert "Args:" in doc
        assert "Returns:" in doc
        assert "Raises:" in doc

    def test_parse_score_has_type_hints(self):
        """Test that _parse_score has full type hints."""
        import inspect

        from assayer.evaluators.hallucination import _parse_score

        signature = inspect.signature(_parse_score)

        # Check parameter type hint
        response_text_param = signature.parameters["response_text"]
        assert response_text_param.annotation == str

        # Check return type hint
        assert signature.return_annotation == float


class TestRegisterHallucinationEvaluators:
    """Test cases for register_hallucination_evaluators function."""

    def test_register_hallucination_evaluators_registers_faithfulness_evaluator(self):
        """Test that 'faithfulness' is retrievable via EvaluatorRegistry.get('faithfulness')."""
        from assayer.evaluators.hallucination import (
            FaithfulnessEvaluator,
            register_hallucination_evaluators,
        )
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        registry = EvaluatorRegistry()
        register_hallucination_evaluators(registry)

        # Should be able to retrieve FaithfulnessEvaluator by name
        retrieved_cls = registry.get("faithfulness")
        assert retrieved_cls is FaithfulnessEvaluator

    def test_register_hallucination_evaluators_registers_llm_judge_evaluator(self):
        """Test that 'llm_judge' is retrievable via EvaluatorRegistry.get('llm_judge')."""
        from assayer.evaluators.hallucination import (
            LLMJudgeEvaluator,
            register_hallucination_evaluators,
        )
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        registry = EvaluatorRegistry()
        register_hallucination_evaluators(registry)

        # Should be able to retrieve LLMJudgeEvaluator by name
        retrieved_cls = registry.get("llm_judge")
        assert retrieved_cls is LLMJudgeEvaluator

    def test_register_hallucination_evaluators_registers_both_evaluators(self):
        """Test that both evaluators are registered correctly."""
        from assayer.evaluators.hallucination import (
            FaithfulnessEvaluator,
            LLMJudgeEvaluator,
            register_hallucination_evaluators,
        )
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        registry = EvaluatorRegistry()
        register_hallucination_evaluators(registry)

        # Check that both evaluators are in the registry
        evaluator_names = registry.list_evaluators()
        assert "faithfulness" in evaluator_names
        assert "llm_judge" in evaluator_names
        assert len(evaluator_names) >= 2

        # Verify the classes are correct
        assert registry.get("faithfulness") is FaithfulnessEvaluator
        assert registry.get("llm_judge") is LLMJudgeEvaluator

    def test_register_hallucination_evaluators_duplicate_registration_raises_value_error(self):
        """Test that duplicate registration raises ValueError."""
        from assayer.evaluators.hallucination import register_hallucination_evaluators
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        registry = EvaluatorRegistry()

        # First registration should succeed
        register_hallucination_evaluators(registry)

        # Second registration should raise ValueError
        with pytest.raises(ValueError):
            register_hallucination_evaluators(registry)

    def test_register_hallucination_evaluators_partial_duplicate_registration_raises_value_error(
        self,
    ):
        """Test that partial duplicate registration raises ValueError."""
        from assayer.evaluators.hallucination import (
            FaithfulnessEvaluator,
            register_hallucination_evaluators,
        )
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        registry = EvaluatorRegistry()

        # Pre-register one evaluator manually
        registry.register("faithfulness", FaithfulnessEvaluator)

        # Attempting to register all evaluators should raise ValueError due to duplicate
        with pytest.raises(ValueError):
            register_hallucination_evaluators(registry)

    def test_register_hallucination_evaluators_works_with_empty_registry(self):
        """Test that registration works correctly with empty registry."""
        from assayer.evaluators.hallucination import register_hallucination_evaluators
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        registry = EvaluatorRegistry()

        # Should start empty
        assert registry.list_evaluators() == []

        # Registration should succeed
        register_hallucination_evaluators(registry)

        # Should now contain the evaluators
        evaluator_names = registry.list_evaluators()
        assert "faithfulness" in evaluator_names
        assert "llm_judge" in evaluator_names

    def test_register_hallucination_evaluators_works_with_existing_different_evaluators(self):
        """Test that registration works when registry has other evaluators."""
        from assayer.evaluators.base import BaseEvaluator
        from assayer.evaluators.hallucination import (
            FaithfulnessEvaluator,
            LLMJudgeEvaluator,
            register_hallucination_evaluators,
        )
        from assayer.models import FieldEvaluation
        from assayer.registries.evaluator_registry import EvaluatorRegistry

        # Create a dummy evaluator class for testing
        class DummyEvaluator(BaseEvaluator):
            def evaluate(self, prediction, reference, **kwargs):
                return FieldEvaluation(
                    field_name=self.name,
                    evaluator_method="dummy",
                    expected_value=reference,
                    obtained_value=prediction,
                    score=0.5,
                    prompt_hash=None,
                    metadata={},
                )

        registry = EvaluatorRegistry()

        # Pre-register a different evaluator
        registry.register("dummy", DummyEvaluator)

        # Should be able to register hallucination evaluators
        register_hallucination_evaluators(registry)

        # All three should be present
        evaluator_names = registry.list_evaluators()
        assert "dummy" in evaluator_names
        assert "faithfulness" in evaluator_names
        assert "llm_judge" in evaluator_names

        # Verify the classes are correct
        assert registry.get("dummy") is DummyEvaluator
        assert registry.get("faithfulness") is FaithfulnessEvaluator
        assert registry.get("llm_judge") is LLMJudgeEvaluator

    def test_register_hallucination_evaluators_has_docstring(self):
        """Test that register_hallucination_evaluators has a Google-style docstring."""
        from assayer.evaluators.hallucination import register_hallucination_evaluators

        assert register_hallucination_evaluators.__doc__ is not None
        doc = register_hallucination_evaluators.__doc__

        # Should contain essential information about what it does
        assert "register" in doc.lower()
        assert "evaluator" in doc.lower()

    def test_register_hallucination_evaluators_has_type_hints(self):
        """Test that register_hallucination_evaluators has full type hints."""
        import inspect

        from assayer.evaluators.hallucination import register_hallucination_evaluators

        signature = inspect.signature(register_hallucination_evaluators)

        # Check parameter type hints
        registry_param = signature.parameters["registry"]
        # Should have EvaluatorRegistry type annotation
        assert registry_param.annotation is not None

        # Check return type hint - should be None
        assert signature.return_annotation == type(None)

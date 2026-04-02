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
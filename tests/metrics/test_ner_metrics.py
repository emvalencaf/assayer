"""Tests for the NER metrics."""

from assayer.metrics import EntitySpan, NERMatcher, ner_macro_f1


class TestNerMacroF1:
    """Test cases for the ner_macro_f1 batch metric function."""

    def test_ner_macro_f1_perfect_match_single_example(self):
        """Test ner_macro_f1 with perfect predictions for a single example."""
        predictions = [
            [EntitySpan("John Doe", "PERSON", 0, 8), EntitySpan("Apple Inc", "ORG", 20, 29)]
        ]
        references = [
            [EntitySpan("John Doe", "PERSON", 0, 8), EntitySpan("Apple Inc", "ORG", 20, 29)]
        ]

        result = ner_macro_f1(predictions, references)

        # Should return 1.0 for perfect match
        assert abs(result - 1.0) <= 0.001

    def test_ner_macro_f1_perfect_match_multiple_examples(self):
        """Test ner_macro_f1 with perfect predictions across multiple examples."""
        predictions = [
            [EntitySpan("John", "PERSON", 0, 4)],
            [EntitySpan("Apple", "ORG", 10, 15)],
            [EntitySpan("Paris", "LOC", 5, 10)],
        ]
        references = [
            [EntitySpan("John", "PERSON", 0, 4)],
            [EntitySpan("Apple", "ORG", 10, 15)],
            [EntitySpan("Paris", "LOC", 5, 10)],
        ]

        result = ner_macro_f1(predictions, references)

        # Should return 1.0 for perfect match across all examples
        assert abs(result - 1.0) <= 0.001

    def test_ner_macro_f1_partial_match_multiple_examples(self):
        """Test ner_macro_f1 with varying accuracy across examples."""
        # Example 1: Perfect match (F1 = 1.0)
        # Example 2: Partial match (some precision/recall issues)
        # Example 3: No match (F1 = 0.0)
        predictions = [
            # Example 1: Perfect match
            [EntitySpan("John", "PERSON", 0, 4)],
            # Example 2: Missing one entity from reference
            [EntitySpan("Apple", "ORG", 0, 5)],
            # Example 3: Completely wrong prediction
            [EntitySpan("Wrong", "PERSON", 0, 5)],
        ]
        references = [
            # Example 1: Perfect match
            [EntitySpan("John", "PERSON", 0, 4)],
            # Example 2: Has two entities, predictions only has one
            [EntitySpan("Apple", "ORG", 0, 5), EntitySpan("Google", "ORG", 10, 16)],
            # Example 3: Different entity entirely
            [EntitySpan("Correct", "LOC", 10, 17)],
        ]

        result = ner_macro_f1(predictions, references)

        # Calculate expected result manually:
        # Example 1: F1 = 1.0 (perfect match)
        # Example 2: precision=1.0 (1/1), recall=0.5 (1/2), F1=0.667
        # Example 3: F1 = 0.0 (no match)
        # Mean = (1.0 + 0.667 + 0.0) / 3 = 0.556
        expected = (1.0 + (2 * 1.0 * 0.5 / (1.0 + 0.5)) + 0.0) / 3
        assert abs(result - expected) <= 0.001

    def test_ner_macro_f1_empty_inputs(self):
        """Test ner_macro_f1 returns 0.0 for empty input lists."""
        predictions = []
        references = []

        result = ner_macro_f1(predictions, references)

        # Should return 0.0 for empty inputs
        assert result == 0.0

    def test_ner_macro_f1_empty_examples_in_lists(self):
        """Test ner_macro_f1 with examples that have empty entity lists."""
        predictions = [
            [],  # No predicted entities
            [EntitySpan("Apple", "ORG", 0, 5)],  # Has predictions
            [],  # No predicted entities
        ]
        references = [
            [],  # No reference entities
            [],  # No reference entities
            [EntitySpan("Paris", "LOC", 0, 5)],  # Has reference entities
        ]

        result = ner_macro_f1(predictions, references)

        # Example 1: Both empty -> F1 = 0.0 (NERMatcher should return 0.0)
        # Example 2: predictions=1, references=0 -> F1 = 0.0
        # Example 3: predictions=0, references=1 -> F1 = 0.0
        # Mean = (0.0 + 0.0 + 0.0) / 3 = 0.0
        assert result == 0.0

    def test_ner_macro_f1_consistent_with_ner_matcher(self):
        """Test that ner_macro_f1 returns the same values as individual NERMatcher calls."""
        predictions = [
            [EntitySpan("John", "PERSON", 0, 4), EntitySpan("Apple", "ORG", 10, 15)],
            [EntitySpan("Paris", "LOC", 0, 5)],
        ]
        references = [
            [EntitySpan("John", "PERSON", 0, 4), EntitySpan("Google", "ORG", 10, 16)],
            [EntitySpan("Paris", "LOC", 0, 5), EntitySpan("London", "LOC", 10, 16)],
        ]

        result = ner_macro_f1(predictions, references)

        # Calculate expected using NERMatcher directly
        matcher = NERMatcher()
        scores = []
        for pred, ref in zip(predictions, references):
            match_result = matcher.match(pred, ref)
            scores.append(match_result.macro_f1)
        expected = sum(scores) / len(scores)

        assert abs(result - expected) <= 0.001

    def test_ner_macro_f1_single_example_multiple_types(self):
        """Test ner_macro_f1 with one example containing multiple entity types."""
        predictions = [
            [
                EntitySpan("John Doe", "PERSON", 0, 8),
                EntitySpan("Apple Inc", "ORG", 20, 29),
                EntitySpan("New York", "LOC", 40, 48),
                EntitySpan("Jane Smith", "PERSON", 60, 70),
            ]
        ]
        references = [
            [
                EntitySpan("John Doe", "PERSON", 0, 8),  # TP for PERSON
                EntitySpan("Microsoft", "ORG", 30, 39),  # FN for ORG (different entity)
                EntitySpan("New York", "LOC", 40, 48),  # TP for LOC
                EntitySpan("Jane Smith", "PERSON", 60, 70),  # TP for PERSON
            ]
        ]

        result = ner_macro_f1(predictions, references)

        # Calculate expected manually:
        # PERSON: 2 TP, 0 FP, 0 FN -> precision=1.0, recall=1.0, F1=1.0
        # ORG: 0 TP, 1 FP, 1 FN -> precision=0.0, recall=0.0, F1=0.0
        # LOC: 1 TP, 0 FP, 0 FN -> precision=1.0, recall=1.0, F1=1.0
        # Macro F1 = (1.0 + 0.0 + 1.0) / 3 = 0.667
        expected = (1.0 + 0.0 + 1.0) / 3
        assert abs(result - expected) <= 0.001

    def test_ner_macro_f1_mismatched_list_lengths(self):
        """Test ner_macro_f1 behavior with mismatched prediction and reference list lengths."""
        predictions = [[EntitySpan("John", "PERSON", 0, 4)], [EntitySpan("Apple", "ORG", 0, 5)]]
        references = [
            [EntitySpan("John", "PERSON", 0, 4)]
            # Missing second reference
        ]

        # This should be handled gracefully - zip will stop at the shorter list
        result = ner_macro_f1(predictions, references)

        # Only the first example should be processed (perfect match)
        assert abs(result - 1.0) <= 0.001

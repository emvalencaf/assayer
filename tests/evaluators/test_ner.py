"""Tests for NER evaluator components."""

import pytest
from dataclasses import dataclass, FrozenInstanceError

# Import the EntitySpan when implemented
# from assayer.evaluators.ner import EntitySpan


class TestEntitySpan:
    """Test cases for EntitySpan dataclass."""

    def test_entity_span_creation_valid_inputs(self):
        """Test EntitySpan creation with valid inputs."""
        from assayer.evaluators.ner import EntitySpan

        span = EntitySpan(
            text="John Doe",
            entity_type="PERSON",
            start=0,
            end=8
        )

        assert span.text == "John Doe"
        assert span.entity_type == "PERSON"
        assert span.start == 0
        assert span.end == 8

    def test_entity_span_is_hashable(self):
        """Test that EntitySpan is hashable (frozen=True)."""
        from assayer.evaluators.ner import EntitySpan

        span1 = EntitySpan(text="Apple Inc.", entity_type="ORG", start=5, end=15)
        span2 = EntitySpan(text="Apple Inc.", entity_type="ORG", start=5, end=15)

        # Should be hashable
        hash1 = hash(span1)
        hash2 = hash(span2)

        # Identical spans should have same hash
        assert hash1 == hash2

        # Should be able to add to set
        span_set = {span1, span2}
        assert len(span_set) == 1  # Same span, so only one in set

    def test_entity_span_is_frozen(self):
        """Test that EntitySpan is frozen (immutable)."""
        from assayer.evaluators.ner import EntitySpan

        span = EntitySpan(text="Tesla", entity_type="ORG", start=0, end=5)

        # Should not be able to modify fields
        with pytest.raises(FrozenInstanceError):
            span.text = "Modified"

        with pytest.raises(FrozenInstanceError):
            span.entity_type = "MODIFIED"

        with pytest.raises(FrozenInstanceError):
            span.start = 10

        with pytest.raises(FrozenInstanceError):
            span.end = 20

    def test_entity_span_equality(self):
        """Test that two EntitySpans with identical fields are equal."""
        from assayer.evaluators.ner import EntitySpan

        span1 = EntitySpan(text="Microsoft", entity_type="ORG", start=10, end=19)
        span2 = EntitySpan(text="Microsoft", entity_type="ORG", start=10, end=19)
        span3 = EntitySpan(text="Microsoft", entity_type="ORG", start=10, end=20)  # Different end

        # Identical spans should be equal
        assert span1 == span2
        assert span2 == span1

        # Different spans should not be equal
        assert span1 != span3
        assert span3 != span1

    def test_entity_span_hash_consistency(self):
        """Test that equal EntitySpans have equal hashes."""
        from assayer.evaluators.ner import EntitySpan

        span1 = EntitySpan(text="Google", entity_type="ORG", start=0, end=6)
        span2 = EntitySpan(text="Google", entity_type="ORG", start=0, end=6)

        # Equal objects must have equal hashes
        assert span1 == span2
        assert hash(span1) == hash(span2)

    def test_entity_span_empty_text_raises_error(self):
        """Test that empty text raises ValueError."""
        from assayer.evaluators.ner import EntitySpan

        with pytest.raises(ValueError, match="EntitySpan.text must not be empty"):
            EntitySpan(text="", entity_type="PERSON", start=0, end=5)

    def test_entity_span_empty_entity_type_raises_error(self):
        """Test that empty entity_type raises ValueError."""
        from assayer.evaluators.ner import EntitySpan

        with pytest.raises(ValueError, match="EntitySpan.entity_type must not be empty"):
            EntitySpan(text="John", entity_type="", start=0, end=4)

    def test_entity_span_negative_start_raises_error(self):
        """Test that negative start raises ValueError."""
        from assayer.evaluators.ner import EntitySpan

        with pytest.raises(ValueError, match="EntitySpan.start must be >= 0"):
            EntitySpan(text="Amazon", entity_type="ORG", start=-1, end=6)

    def test_entity_span_end_less_equal_start_raises_error(self):
        """Test that end <= start raises ValueError."""
        from assayer.evaluators.ner import EntitySpan

        # Test end == start
        with pytest.raises(ValueError, match="EntitySpan.end must be > start"):
            EntitySpan(text="IBM", entity_type="ORG", start=5, end=5)

        # Test end < start
        with pytest.raises(ValueError, match="EntitySpan.end must be > start"):
            EntitySpan(text="IBM", entity_type="ORG", start=5, end=3)

    def test_entity_span_boundary_values(self):
        """Test EntitySpan with boundary values."""
        from assayer.evaluators.ner import EntitySpan

        # Minimum valid values
        span = EntitySpan(text="A", entity_type="X", start=0, end=1)
        assert span.text == "A"
        assert span.entity_type == "X"
        assert span.start == 0
        assert span.end == 1

        # Large values should work
        large_span = EntitySpan(text="Very long entity name", entity_type="LONG_TYPE", start=1000, end=2000)
        assert large_span.start == 1000
        assert large_span.end == 2000

    def test_entity_span_different_types_inequality(self):
        """Test EntitySpans with different entity types are not equal."""
        from assayer.evaluators.ner import EntitySpan

        span1 = EntitySpan(text="John", entity_type="PERSON", start=0, end=4)
        span2 = EntitySpan(text="John", entity_type="ORG", start=0, end=4)  # Same text, different type

        assert span1 != span2
        assert hash(span1) != hash(span2)

    def test_entity_span_different_positions_inequality(self):
        """Test EntitySpans with different positions are not equal."""
        from assayer.evaluators.ner import EntitySpan

        span1 = EntitySpan(text="Apple", entity_type="ORG", start=0, end=5)
        span2 = EntitySpan(text="Apple", entity_type="ORG", start=10, end=15)  # Same text and type, different position

        assert span1 != span2
        assert hash(span1) != hash(span2)

    def test_entity_span_whitespace_text_validation(self):
        """Test that whitespace-only text raises ValueError."""
        from assayer.evaluators.ner import EntitySpan

        # Whitespace-only text should be considered empty
        with pytest.raises(ValueError, match="EntitySpan.text must not be empty"):
            EntitySpan(text="   ", entity_type="PERSON", start=0, end=3)

        with pytest.raises(ValueError, match="EntitySpan.text must not be empty"):
            EntitySpan(text="\t\n ", entity_type="ORG", start=5, end=10)

    def test_entity_span_whitespace_entity_type_validation(self):
        """Test that whitespace-only entity_type raises ValueError."""
        from assayer.evaluators.ner import EntitySpan

        # Whitespace-only entity_type should be considered empty
        with pytest.raises(ValueError, match="EntitySpan.entity_type must not be empty"):
            EntitySpan(text="John", entity_type="   ", start=0, end=4)

        with pytest.raises(ValueError, match="EntitySpan.entity_type must not be empty"):
            EntitySpan(text="Apple", entity_type="\t\n ", start=0, end=5)

    def test_entity_span_valid_text_with_spaces(self):
        """Test that text with internal spaces is valid."""
        from assayer.evaluators.ner import EntitySpan

        # Text with spaces should be valid
        span = EntitySpan(text="New York City", entity_type="LOCATION", start=0, end=13)
        assert span.text == "New York City"

        # Entity type with spaces/underscores should be valid
        span2 = EntitySpan(text="John", entity_type="PERSON_NAME", start=0, end=4)
        assert span2.entity_type == "PERSON_NAME"

    def test_entity_span_unicode_text(self):
        """Test EntitySpan with unicode text."""
        from assayer.evaluators.ner import EntitySpan

        # Unicode characters should work
        span = EntitySpan(text="François", entity_type="PERSON", start=0, end=8)
        assert span.text == "François"

        # Emoji and special characters
        span2 = EntitySpan(text="🏢 Company", entity_type="ORG", start=5, end=15)
        assert span2.text == "🏢 Company"

    def test_entity_span_zero_start_valid(self):
        """Test that start=0 is valid."""
        from assayer.evaluators.ner import EntitySpan

        span = EntitySpan(text="Start", entity_type="TEST", start=0, end=5)
        assert span.start == 0

    def test_entity_span_large_indices(self):
        """Test EntitySpan with large start/end indices."""
        from assayer.evaluators.ner import EntitySpan

        span = EntitySpan(text="Entity", entity_type="TYPE", start=999999, end=1000006)
        assert span.start == 999999
        assert span.end == 1000006


class TestNERMatchResult:
    """Test cases for NERMatchResult dataclass."""

    def test_ner_match_result_creation(self):
        """Test NERMatchResult creation with valid data."""
        from assayer.evaluators.ner import NERMatchResult

        per_type_precision = {"PERSON": 0.9, "ORG": 0.8}
        per_type_recall = {"PERSON": 0.85, "ORG": 0.75}
        per_type_f1 = {"PERSON": 0.875, "ORG": 0.775}
        macro_f1 = 0.825

        result = NERMatchResult(
            per_type_precision=per_type_precision,
            per_type_recall=per_type_recall,
            per_type_f1=per_type_f1,
            macro_f1=macro_f1
        )

        assert result.per_type_precision == per_type_precision
        assert result.per_type_recall == per_type_recall
        assert result.per_type_f1 == per_type_f1
        assert result.macro_f1 == macro_f1


class TestNERMatcher:
    """Test cases for NERMatcher class."""

    def test_ner_matcher_known_fixture_precision_recall_f1(self):
        """Test NERMatcher returns correct precision, recall, F1 per type for known fixture."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Known fixture case with carefully calculated expected values
        predicted = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),
            EntitySpan(text="Mary", entity_type="PERSON", start=20, end=24),
            EntitySpan(text="Microsoft", entity_type="ORG", start=30, end=39),
            EntitySpan(text="FakeOrg", entity_type="ORG", start=50, end=57),  # False positive
        ]

        reference = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),     # TP for PERSON
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),    # TP for ORG
            EntitySpan(text="Mary", entity_type="PERSON", start=20, end=24),  # TP for PERSON
            EntitySpan(text="Google", entity_type="ORG", start=40, end=46),   # FN for ORG (missed)
            EntitySpan(text="Alice", entity_type="PERSON", start=60, end=65), # FN for PERSON (missed)
        ]

        # Expected calculations:
        # PERSON: TP=2 (John, Mary), FP=0, FN=1 (Alice missed)
        #   precision = 2/2 = 1.0
        #   recall = 2/3 = 0.6667
        #   f1 = 2 * 1.0 * 0.6667 / (1.0 + 0.6667) = 0.8

        # ORG: TP=1 (Apple), FP=2 (Microsoft, FakeOrg), FN=1 (Google missed)
        # predicted ORG = {Apple, Microsoft, FakeOrg}, reference ORG = {Apple, Google}
        # TP = intersection = {Apple} = 1
        # precision = 1/3 = 0.3333 (1 correct out of 3 predicted)
        # recall = 1/2 = 0.5 (1 correct out of 2 reference)
        # f1 = 2 * 0.3333 * 0.5 / (0.3333 + 0.5) = 0.4

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        assert abs(result.per_type_precision["PERSON"] - 1.0) < 0.001
        assert abs(result.per_type_recall["PERSON"] - 0.6667) < 0.001
        assert abs(result.per_type_f1["PERSON"] - 0.8) < 0.001

        assert abs(result.per_type_precision["ORG"] - 0.3333) < 0.001
        assert abs(result.per_type_recall["ORG"] - 0.5) < 0.001
        assert abs(result.per_type_f1["ORG"] - 0.4) < 0.001

    def test_ner_matcher_macro_f1_unweighted_mean(self):
        """Test Macro F1 equals unweighted mean of per-type F1 values."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Simple case where we can easily verify macro F1
        predicted = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),
        ]

        reference = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),  # Perfect PERSON
            EntitySpan(text="Google", entity_type="ORG", start=20, end=26),  # Missed ORG, wrong prediction
        ]

        # Expected:
        # PERSON: TP=1, precision=1/1=1.0, recall=1/1=1.0, f1=1.0
        # ORG: TP=0, precision=0/1=0.0, recall=0/1=0.0, f1=0.0
        # macro_f1 = (1.0 + 0.0) / 2 = 0.5

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        expected_macro = (result.per_type_f1["PERSON"] + result.per_type_f1["ORG"]) / 2
        assert abs(result.macro_f1 - expected_macro) < 0.001
        assert abs(result.macro_f1 - 0.5) < 0.001

    def test_ner_matcher_empty_predicted_list(self):
        """Test handles empty predicted list (F1=0.0 for all types present in reference)."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        reference = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),
            EntitySpan(text="Google", entity_type="ORG", start=20, end=26),
        ]

        predicted = []  # Empty predictions

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # All types should have 0.0 precision, recall, and F1
        assert result.per_type_precision["PERSON"] == 0.0
        assert result.per_type_recall["PERSON"] == 0.0
        assert result.per_type_f1["PERSON"] == 0.0

        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0

        # Macro F1 should be 0.0
        assert result.macro_f1 == 0.0

    def test_ner_matcher_empty_reference_list(self):
        """Test handles empty reference list (F1=0.0 for all types present in predicted)."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        predicted = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),
            EntitySpan(text="Microsoft", entity_type="ORG", start=20, end=29),
        ]

        reference = []  # Empty reference

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # All types should have 0.0 precision, recall, and F1
        assert result.per_type_precision["PERSON"] == 0.0
        assert result.per_type_recall["PERSON"] == 0.0
        assert result.per_type_f1["PERSON"] == 0.0

        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0

        # Macro F1 should be 0.0
        assert result.macro_f1 == 0.0

    def test_ner_matcher_both_empty_lists(self):
        """Test both empty lists returns macro_f1=0.0 without raising."""
        from assayer.evaluators.ner import NERMatcher

        predicted = []
        reference = []

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # No types to evaluate, should return 0.0 without error
        assert result.per_type_precision == {}
        assert result.per_type_recall == {}
        assert result.per_type_f1 == {}
        assert result.macro_f1 == 0.0

    def test_ner_matcher_perfect_predictions(self):
        """Test perfect predictions (all correct, no false positives/negatives) returns F1=1.0."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Perfect case where all predictions match references exactly
        entities = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),
            EntitySpan(text="Mary", entity_type="PERSON", start=20, end=24),
        ]

        predicted = entities.copy()
        reference = entities.copy()

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # All types should have perfect scores
        assert result.per_type_precision["PERSON"] == 1.0
        assert result.per_type_recall["PERSON"] == 1.0
        assert result.per_type_f1["PERSON"] == 1.0

        assert result.per_type_precision["ORG"] == 1.0
        assert result.per_type_recall["ORG"] == 1.0
        assert result.per_type_f1["ORG"] == 1.0

        # Macro F1 should be 1.0
        assert result.macro_f1 == 1.0

    def test_ner_matcher_type_in_predicted_only(self):
        """Test entity type present only in predictions contributes precision=0, recall=0, F1=0."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        predicted = [
            EntitySpan(text="FakeOrg", entity_type="ORG", start=0, end=7),
            EntitySpan(text="FakePerson", entity_type="PERSON", start=10, end=20),
        ]

        reference = [
            EntitySpan(text="RealLocation", entity_type="LOCATION", start=30, end=42),
        ]

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # Types only in predictions should have precision=0, recall=0, f1=0
        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0

        assert result.per_type_precision["PERSON"] == 0.0
        assert result.per_type_recall["PERSON"] == 0.0
        assert result.per_type_f1["PERSON"] == 0.0

        # Type only in reference should also have precision=0, recall=0, f1=0
        assert result.per_type_precision["LOCATION"] == 0.0
        assert result.per_type_recall["LOCATION"] == 0.0
        assert result.per_type_f1["LOCATION"] == 0.0

        # Macro F1 should be 0.0
        assert result.macro_f1 == 0.0

    def test_ner_matcher_type_in_reference_only(self):
        """Test entity type present only in references contributes F1=0."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        predicted = [
            EntitySpan(text="John", entity_type="PERSON", start=0, end=4),
        ]

        reference = [
            EntitySpan(text="Apple", entity_type="ORG", start=10, end=15),
            EntitySpan(text="London", entity_type="LOCATION", start=20, end=26),
        ]

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # Type only in reference should have precision=0, recall=0, f1=0
        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0

        assert result.per_type_precision["LOCATION"] == 0.0
        assert result.per_type_recall["LOCATION"] == 0.0
        assert result.per_type_f1["LOCATION"] == 0.0

        # Type only in predictions should also have f1=0
        assert result.per_type_precision["PERSON"] == 0.0
        assert result.per_type_recall["PERSON"] == 0.0
        assert result.per_type_f1["PERSON"] == 0.0

        # Macro F1 should be 0.0
        assert result.macro_f1 == 0.0

    def test_ner_matcher_complex_multi_type_scenario(self):
        """Test complex scenario with multiple types and mixed results."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Complex fixture with careful calculation
        predicted = [
            # PERSON entities - 2 correct, 1 wrong
            EntitySpan(text="John Doe", entity_type="PERSON", start=0, end=8),      # TP
            EntitySpan(text="Jane Smith", entity_type="PERSON", start=15, end=25),  # TP
            EntitySpan(text="Fake Person", entity_type="PERSON", start=50, end=61), # FP

            # ORG entities - 1 correct, 1 wrong
            EntitySpan(text="Apple Inc", entity_type="ORG", start=30, end=39),      # TP
            EntitySpan(text="Fake Corp", entity_type="ORG", start=70, end=79),      # FP

            # LOCATION entities - 1 correct
            EntitySpan(text="New York", entity_type="LOCATION", start=90, end=98),  # TP
        ]

        reference = [
            # PERSON entities - 3 total (2 found, 1 missed)
            EntitySpan(text="John Doe", entity_type="PERSON", start=0, end=8),      # TP
            EntitySpan(text="Jane Smith", entity_type="PERSON", start=15, end=25),  # TP
            EntitySpan(text="Bob Johnson", entity_type="PERSON", start=100, end=111), # FN

            # ORG entities - 2 total (1 found, 1 missed)
            EntitySpan(text="Apple Inc", entity_type="ORG", start=30, end=39),      # TP
            EntitySpan(text="Google LLC", entity_type="ORG", start=120, end=130),   # FN

            # LOCATION entities - 2 total (1 found, 1 missed)
            EntitySpan(text="New York", entity_type="LOCATION", start=90, end=98),  # TP
            EntitySpan(text="California", entity_type="LOCATION", start=140, end=150), # FN
        ]

        # Expected calculations:
        # PERSON: TP=2, pred_count=3, ref_count=3
        #   precision = 2/3 = 0.6667, recall = 2/3 = 0.6667, f1 = 0.6667

        # ORG: TP=1, pred_count=2, ref_count=2
        #   precision = 1/2 = 0.5, recall = 1/2 = 0.5, f1 = 0.5

        # LOCATION: TP=1, pred_count=1, ref_count=2
        #   precision = 1/1 = 1.0, recall = 1/2 = 0.5, f1 = 2*1.0*0.5/(1.0+0.5) = 0.6667

        # macro_f1 = (0.6667 + 0.5 + 0.6667) / 3 = 0.6111

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # Check PERSON metrics
        assert abs(result.per_type_precision["PERSON"] - 0.6667) < 0.001
        assert abs(result.per_type_recall["PERSON"] - 0.6667) < 0.001
        assert abs(result.per_type_f1["PERSON"] - 0.6667) < 0.001

        # Check ORG metrics
        assert abs(result.per_type_precision["ORG"] - 0.5) < 0.001
        assert abs(result.per_type_recall["ORG"] - 0.5) < 0.001
        assert abs(result.per_type_f1["ORG"] - 0.5) < 0.001

        # Check LOCATION metrics
        assert abs(result.per_type_precision["LOCATION"] - 1.0) < 0.001
        assert abs(result.per_type_recall["LOCATION"] - 0.5) < 0.001
        assert abs(result.per_type_f1["LOCATION"] - 0.6667) < 0.001

        # Check macro F1
        expected_macro = (0.6667 + 0.5 + 0.6667) / 3
        assert abs(result.macro_f1 - expected_macro) < 0.001

    def test_ner_matcher_single_type_single_entity_perfect(self):
        """Test single entity type with perfect match."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        predicted = [EntitySpan(text="Apple", entity_type="ORG", start=0, end=5)]
        reference = [EntitySpan(text="Apple", entity_type="ORG", start=0, end=5)]

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        assert result.per_type_precision["ORG"] == 1.0
        assert result.per_type_recall["ORG"] == 1.0
        assert result.per_type_f1["ORG"] == 1.0
        assert result.macro_f1 == 1.0

    def test_ner_matcher_different_text_same_position_and_type(self):
        """Test entities with same position and type but different text are not matches."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Same position and type but different text - should not be TP
        predicted = [EntitySpan(text="Apple", entity_type="ORG", start=0, end=5)]
        reference = [EntitySpan(text="Microsoft", entity_type="ORG", start=0, end=5)]

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # No true positives since text differs
        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0
        assert result.macro_f1 == 0.0

    def test_ner_matcher_same_text_different_positions(self):
        """Test entities with same text and type but different positions are not matches."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Same text and type but different positions - should not be TP
        predicted = [EntitySpan(text="Apple", entity_type="ORG", start=0, end=5)]
        reference = [EntitySpan(text="Apple", entity_type="ORG", start=10, end=15)]

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # No true positives since positions differ
        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0
        assert result.macro_f1 == 0.0

    def test_ner_matcher_same_text_and_position_different_type(self):
        """Test entities with same text and position but different type are not matches."""
        from assayer.evaluators.ner import EntitySpan, NERMatcher

        # Same text and position but different type - should not be TP
        predicted = [EntitySpan(text="Apple", entity_type="ORG", start=0, end=5)]
        reference = [EntitySpan(text="Apple", entity_type="PRODUCT", start=0, end=5)]

        matcher = NERMatcher()
        result = matcher.match(predicted, reference)

        # Each type has 0 TP since they don't match across types
        assert result.per_type_precision["ORG"] == 0.0
        assert result.per_type_recall["ORG"] == 0.0
        assert result.per_type_f1["ORG"] == 0.0

        assert result.per_type_precision["PRODUCT"] == 0.0
        assert result.per_type_recall["PRODUCT"] == 0.0
        assert result.per_type_f1["PRODUCT"] == 0.0

        assert result.macro_f1 == 0.0
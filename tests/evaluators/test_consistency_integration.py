"""Integration smoke tests for ConsistencyEvaluator with built-in evaluators.

This module contains integration tests that verify ConsistencyEvaluator can
successfully wrap various built-in evaluator types and produce valid results.
Tests use real or mocked evaluators to avoid external dependencies.
"""

from unittest.mock import MagicMock

from assayer.evaluators.base import BaseEvaluator
from assayer.evaluators.consistency import ConsistencyEvaluator
from assayer.evaluators.hallucination import FaithfulnessEvaluator, LLMJudgeEvaluator
from assayer.evaluators.ner import EntitySpan, NEREvaluator
from assayer.models.consistency_field_evaluation import ConsistencyFieldEvaluation
from assayer.models.consistency_summary import ConsistencySummary
from assayer.models.field_evaluation import FieldEvaluation


class MockClassificationEvaluator(BaseEvaluator):
    """Mock classification evaluator for testing purposes."""

    def __init__(self, name: str = "classification") -> None:
        super().__init__(name)

    def evaluate(self, prediction: str, reference: str, **kwargs) -> FieldEvaluation:
        """Mock evaluate method that returns a basic FieldEvaluation."""
        score = 1.0 if prediction == reference else 0.0
        return FieldEvaluation(
            field_name=self.name,
            evaluator_method="classification",
            expected_value=reference,
            obtained_value=prediction,
            score=score,
            prompt_hash=None,
            metadata={},
        )


class TestConsistencyEvaluatorImport:
    """Test that ConsistencyEvaluator can be imported from assayer.evaluators."""

    def test_consistency_evaluator_is_importable(self):
        """Test that ConsistencyEvaluator is importable from assayer.evaluators."""
        from assayer.evaluators import ConsistencyEvaluator

        assert ConsistencyEvaluator is not None


class TestConsistencyEvaluatorIntegration:
    """Integration tests for ConsistencyEvaluator with various evaluator types."""

    def test_with_classification_evaluator_evaluate_dataset(self):
        """Test ConsistencyEvaluator wrapping ClassificationEvaluator for dataset evaluation."""
        # Create mock classification evaluator
        base_evaluator = MockClassificationEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator=base_evaluator, k=3, min_k=2)

        # Create test dataset with predictions and references
        dataset = [
            {"group": "A", "prediction": "positive", "reference": "positive"},
            {"group": "A", "prediction": "positive", "reference": "positive"},
            {"group": "A", "prediction": "negative", "reference": "positive"},
            {"group": "B", "prediction": "neutral", "reference": "neutral"},
            {"group": "B", "prediction": "neutral", "reference": "neutral"},
        ]

        # Evaluate dataset
        result = consistency_evaluator.evaluate_dataset(
            dataset=dataset,
            group_by="group",
            prediction_field="prediction",
            reference_field="reference",
        )

        # Verify result type and structure
        assert isinstance(result, ConsistencySummary)
        assert len(result.per_group) == 2  # Two groups: A and B
        assert all(isinstance(group, ConsistencyFieldEvaluation) for group in result.per_group)

        # Verify that all required fields are present and have valid values
        assert 0.0 <= result.mean_agreement_rate <= 1.0
        assert result.mean_entropy >= 0.0
        assert result.mean_score_std >= 0.0
        assert 0.0 <= result.mean_correct_rate <= 1.0
        assert 0.0 <= result.pass_at_k_rate <= 1.0
        assert 0.0 <= result.mean_recall_at_k <= 1.0
        assert len(result.worst_groups) <= 10

    def test_with_mocked_llm_judge_evaluate_live(self):
        """Test ConsistencyEvaluator wrapping mocked LLMJudgeEvaluator for live evaluation."""
        # Create mock LLM model
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "0.8"
        mock_model.invoke.return_value = mock_response

        # Create LLMJudgeEvaluator with mocked model
        base_evaluator = LLMJudgeEvaluator(
            field_name="quality",
            judge_model=mock_model,
            system_prompt="Rate this response from 0.0 to 1.0",
        )

        # Mock the evaluate method to avoid actual LLM calls
        mock_evaluate = MagicMock(
            return_value=FieldEvaluation(
                field_name="quality",
                evaluator_method="llm_judge",
                expected_value="Good response",
                obtained_value="Decent response",
                score=0.8,
                prompt_hash="abc123",
                metadata={},
            )
        )
        base_evaluator.evaluate = mock_evaluate

        consistency_evaluator = ConsistencyEvaluator(evaluator=base_evaluator, k=3)

        # Create mock target function
        mock_target_fn = MagicMock(
            side_effect=[
                "Response 1",
                "Response 2",
                "Response 1",  # Repeat to test agreement
            ]
        )

        # Evaluate live
        result = consistency_evaluator.evaluate_live(
            target_fn=mock_target_fn, input="Test input", reference="Good response"
        )

        # Verify result type and structure
        assert isinstance(result, ConsistencyFieldEvaluation)
        assert result.group_key is None  # Should be None in live mode
        assert result.n == 3  # Should have k=3 runs
        assert 0.0 <= result.agreement_rate <= 1.0
        assert result.entropy >= 0.0
        assert result.score_std >= 0.0
        assert 0.0 <= result.correct_rate <= 1.0
        assert isinstance(result.pass_at_k, bool)
        assert 0.0 <= result.recall_at_k <= 1.0
        assert len(result.raw_results) == 3

        # Verify target function was called k times
        assert mock_target_fn.call_count == 3
        # Verify evaluate was called k times
        assert mock_evaluate.call_count == 3

    def test_with_mocked_ner_evaluator_evaluate_dataset(self):
        """Test ConsistencyEvaluator wrapping mocked NEREvaluator for dataset evaluation."""
        # Create NEREvaluator (NERJudgeEvaluator equivalent)
        base_evaluator = NEREvaluator(field_name="entities")

        # Mock the evaluate method to avoid complex entity matching logic
        mock_evaluate = MagicMock(
            return_value=FieldEvaluation(
                field_name="entities",
                evaluator_method="ner_exact_match",
                expected_value=[EntitySpan("John", "PERSON", 0, 4)],
                obtained_value=[EntitySpan("John", "PERSON", 0, 4)],
                score=1.0,
                prompt_hash=None,
                metadata={"macro_f1": 1.0},
            )
        )
        base_evaluator.evaluate = mock_evaluate

        consistency_evaluator = ConsistencyEvaluator(evaluator=base_evaluator, k=2, min_k=2)

        # Create test dataset with entity predictions
        entity_ref = [EntitySpan("Alice", "PERSON", 0, 5)]
        entity_pred1 = [EntitySpan("Alice", "PERSON", 0, 5)]
        entity_pred2 = [EntitySpan("Bob", "PERSON", 0, 3)]

        dataset = [
            {"group": "doc1", "prediction": entity_pred1, "reference": entity_ref},
            {"group": "doc1", "prediction": entity_pred2, "reference": entity_ref},
        ]

        # Evaluate dataset
        result = consistency_evaluator.evaluate_dataset(
            dataset=dataset,
            group_by="group",
            prediction_field="prediction",
            reference_field="reference",
        )

        # Verify result type and structure
        assert isinstance(result, ConsistencySummary)
        assert len(result.per_group) == 1  # One group: doc1
        assert all(isinstance(group, ConsistencyFieldEvaluation) for group in result.per_group)

        # Verify that all required fields are present and have valid values
        assert 0.0 <= result.mean_agreement_rate <= 1.0
        assert result.mean_entropy >= 0.0
        assert result.mean_score_std >= 0.0
        assert 0.0 <= result.mean_correct_rate <= 1.0
        assert 0.0 <= result.pass_at_k_rate <= 1.0
        assert 0.0 <= result.mean_recall_at_k <= 1.0

        # Verify evaluate was called twice (once per record)
        assert mock_evaluate.call_count == 2

    def test_with_mocked_faithfulness_evaluator(self):
        """Test ConsistencyEvaluator wrapping mocked FaithfulnessEvaluator."""
        # Create FaithfulnessEvaluator with mocked classifier
        mock_classifier = MagicMock(
            return_value=[[{"label": "LABEL_0", "score": 0.2}, {"label": "LABEL_1", "score": 0.8}]]
        )

        base_evaluator = FaithfulnessEvaluator(
            field_name="faithfulness", threshold=0.5, classifier=mock_classifier
        )

        consistency_evaluator = ConsistencyEvaluator(evaluator=base_evaluator, k=2)

        # Create test dataset
        dataset = [
            {"group": "question1", "prediction": "Answer A", "reference": "Context about A"},
            {"group": "question1", "prediction": "Answer B", "reference": "Context about A"},
        ]

        # Evaluate dataset
        result = consistency_evaluator.evaluate_dataset(
            dataset=dataset,
            group_by="group",
            prediction_field="prediction",
            reference_field="reference",
        )

        # Verify result type and structure
        assert isinstance(result, ConsistencySummary)
        assert len(result.per_group) == 1  # One group: question1

        # Verify that all required fields are present and have valid values
        assert 0.0 <= result.mean_agreement_rate <= 1.0
        assert result.mean_entropy >= 0.0
        assert result.mean_score_std >= 0.0
        assert 0.0 <= result.mean_correct_rate <= 1.0
        assert 0.0 <= result.pass_at_k_rate <= 1.0
        assert 0.0 <= result.mean_recall_at_k <= 1.0

    def test_no_built_in_evaluators_modified(self):
        """Test that no built-in evaluator classes are modified by ConsistencyEvaluator.

        This test verifies that ConsistencyEvaluator works by composition/wrapping
        without modifying the original evaluator classes.
        """
        # Test with FaithfulnessEvaluator
        mock_classifier = MagicMock(return_value=[[{"label": "LABEL_1", "score": 0.9}]])
        faith_eval = FaithfulnessEvaluator("faith", classifier=mock_classifier)
        consistency_eval = ConsistencyEvaluator(faith_eval)

        # Verify the wrapped evaluator retains its original interface
        assert hasattr(faith_eval, "evaluate")
        assert hasattr(faith_eval, "threshold")
        assert faith_eval.threshold == 0.5  # Default value should be unchanged

        # Test with NEREvaluator
        ner_eval = NEREvaluator("entities")
        consistency_eval2 = ConsistencyEvaluator(ner_eval)

        # Verify the wrapped evaluator retains its original interface
        assert hasattr(ner_eval, "evaluate")
        assert hasattr(ner_eval, "field_name")
        assert ner_eval.field_name == "entities"

        # Verify that ConsistencyEvaluator doesn't inherit from BaseEvaluator
        # (it's a wrapper, not a subclass)
        assert not isinstance(consistency_eval, BaseEvaluator)
        assert not isinstance(consistency_eval2, BaseEvaluator)

    def test_empty_dataset_handling(self):
        """Test that ConsistencyEvaluator handles empty datasets correctly."""
        base_evaluator = MockClassificationEvaluator()
        consistency_evaluator = ConsistencyEvaluator(evaluator=base_evaluator)

        result = consistency_evaluator.evaluate_dataset(
            dataset=[],
            group_by="group",
        )

        # Verify empty dataset returns valid empty summary
        assert isinstance(result, ConsistencySummary)
        assert len(result.per_group) == 0
        assert len(result.worst_groups) == 0
        assert result.mean_agreement_rate == 0.0
        assert result.mean_entropy == 0.0
        assert result.mean_score_std == 0.0
        assert result.mean_correct_rate == 0.0
        assert result.pass_at_k_rate == 0.0
        assert result.mean_recall_at_k == 0.0

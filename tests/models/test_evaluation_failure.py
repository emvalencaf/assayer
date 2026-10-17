"""Tests for the EvaluationFailure model."""

from assayer.models import EvaluationFailure


class TestEvaluationFailure:
    def test_target_id_is_optional(self):
        failure = EvaluationFailure(metric="m", error="boom")

        assert (failure.metric, failure.error, failure.target_id) == ("m", "boom", None)

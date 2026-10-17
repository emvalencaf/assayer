"""Tests for the Dataset and Case models."""

from assayer.models import Case, Dataset


class TestCase:
    def test_reference_fields_are_all_optional(self):
        case = Case(input="q")

        assert case.expected_output is None
        assert case.expected_tool_calls is None
        assert case.expected_steps is None
        assert case.expected_outcome is None
        assert case.expected_state is None
        assert case.reference_contexts is None
        assert case.reference_context_ids is None

    def test_reference_fields_are_accepted(self):
        case = Case(
            input="q",
            id="c1",
            expected_output="a",
            expected_tool_calls=[{"name": "search"}],
            expected_steps=["search", "answer"],
            expected_outcome="refund issued",
            expected_state={"refunded": True},
            reference_contexts=["ctx"],
            reference_context_ids=["d1"],
        )

        assert case.expected_tool_calls == [{"name": "search"}]
        assert case.expected_steps == ["search", "answer"]
        assert case.expected_outcome == "refund issued"
        assert case.expected_state == {"refunded": True}
        assert case.reference_contexts == ["ctx"]
        assert case.reference_context_ids == ["d1"]


class TestDataset:
    def test_dataset_holds_named_cases(self):
        dataset = Dataset(name="d", cases=[Case(input="q")])

        assert dataset.name == "d"
        assert len(dataset.cases) == 1

    def test_dataset_defaults_to_no_cases(self):
        assert Dataset(name="d").cases == []

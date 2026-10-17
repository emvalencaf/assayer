"""Tests for the Dataset and Case models."""

from assayer.models import Case, Dataset


class TestDataset:
    def test_dataset_holds_named_cases(self):
        dataset = Dataset(name="d", cases=[Case(input="q")])

        assert dataset.name == "d"
        assert len(dataset.cases) == 1

    def test_dataset_defaults_to_no_cases(self):
        assert Dataset(name="d").cases == []

"""InMemoryAdapter, held to the shared conformance suite, plus what is its own."""

import pytest

from assayer.adapters import AdapterConfigError, InMemoryAdapter
from assayer.models import Case, Dataset
from assayer.runner import Runner

from .conformance import AdapterConformance


class TestInMemoryConformance(AdapterConformance):
    def make_adapter(self):
        return InMemoryAdapter(sleep=lambda seconds: None)

    def inject(self, adapter, target_kind, *errors, nth=0):
        adapter.fail_on(target_kind, *errors, nth=nth)

    def stored(self, adapter):
        return {(i.target_kind, i.target_id): p for i, p in adapter.items.items()}


class TestInMemoryAdapter:
    def test_empty_name_is_a_config_error(self):
        with pytest.raises(AdapterConfigError):
            InMemoryAdapter(name="  ")

    def test_queue_marks_items_queued_instead_of_confirmed(self):
        adapter = InMemoryAdapter(queue=True)
        runner = Runner(lambda v: v, adapter=adapter)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))

        report = runner.export(experiment)

        assert report.ok
        assert report.confirmed == []
        assert len(report.queued) == 3  # Case, Trajectory, Step

    def test_close_marks_closed(self):
        with InMemoryAdapter() as adapter:
            pass
        assert adapter.closed

    def test_export_without_adapter_is_rejected(self):
        runner = Runner(lambda v: v)
        experiment = runner.run(Dataset("d", [Case(input="a", id="c1")]))

        with pytest.raises(ValueError, match="adapter"):
            runner.export(experiment)

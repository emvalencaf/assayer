"""LangSmithAdapter: exports an Experiment to LangSmith as an experiment project.

The Cases become examples of a dataset, the Experiment becomes a project that references that
dataset, each Trajectory becomes a run tree (one root run, one child run per Step) linked to its
example, and each Score becomes feedback. Run ids, trace ids and `dotted_order` are generated
here, because the SDK queues runs in the background and does not return them.
"""

import datetime as dt
import os
import time
from collections.abc import Callable
from types import TracebackType
from typing import Self

import langsmith
from langsmith.utils import LangSmithError

from assayer.adapters import AdapterConfigError, ExportReport, export_experiment
from assayer.integrations.langsmith_export import LangSmithExport
from assayer.models import Experiment

_API_KEY_VARIABLES = ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY")


class LangSmithAdapter:
    """Exports an Experiment to LangSmith. Sync only, not thread-safe: one export at a time.

    Trajectories carry no timing, so runs get a synthetic one: every run of an export starts at
    the time of the Adapter's first export of that Experiment, offset by one microsecond per
    Step so that `dotted_order` keeps the Steps in order. Exporting again from the same Adapter
    reuses that time, and `started_at` fixes it across Adapters. Model Steps carry their tokens
    (and cost, when known) as `usage_metadata`, and a Trajectory's totals are in the
    `assayer.usage` metadata of its root run.

    Args:
        client: A `langsmith.Client`. It is left open by `close`. Without it, one is built from
            `api_key` or the environment.
        api_key: Key for the client the Adapter builds itself. Defaults to `LANGSMITH_API_KEY`,
            then `LANGCHAIN_API_KEY`.
        dataset_name: Name of the LangSmith dataset the Cases go to, created when missing and
            reused otherwise. Defaults to the Experiment's name.
        started_at: Start time of every run, timezone-aware. Pass the same value to export an
            Experiment again from a new Adapter and keep the runs' `dotted_order` unchanged.
            Defaults to the time of the Adapter's first export of each Experiment.
        name: Name of the Adapter. Must be non-empty.
        clock: Gives the current time; injected so tests are deterministic.
        sleep: Waits between retries; pass a no-op in tests.

    Raises:
        AdapterConfigError: If name or dataset_name is empty, started_at has no timezone, or
            there is no client and no key.
    """

    def __init__(
        self,
        client: langsmith.Client | None = None,
        *,
        api_key: str | None = None,
        dataset_name: str | None = None,
        started_at: dt.datetime | None = None,
        name: str = "langsmith",
        clock: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.UTC),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not name.strip():
            raise AdapterConfigError("name must not be empty")
        if dataset_name is not None and not dataset_name.strip():
            raise AdapterConfigError("dataset_name must not be empty")
        if started_at is not None and started_at.tzinfo is None:
            raise AdapterConfigError("started_at must be timezone-aware")
        self._owns_client = client is None
        if client is None:
            key = api_key or next(filter(None, map(os.environ.get, _API_KEY_VARIABLES)), None)
            if not key:
                raise AdapterConfigError(
                    "no LangSmith credentials: set LANGSMITH_API_KEY (or LANGCHAIN_API_KEY), "
                    "pass api_key, or pass a langsmith.Client"
                )
            try:
                client = langsmith.Client(api_key=key)
            except LangSmithError as error:
                raise AdapterConfigError(f"could not build a LangSmith client: {error}") from error
        self.name = name
        self.client = client
        self._dataset_name = dataset_name
        self._started_at = started_at
        self._clock = clock
        self._sleep = sleep
        self._started: dict[str, dt.datetime] = {}

    def export(self, experiment: Experiment, *, include_content: bool = True) -> ExportReport:
        """Export the Experiment.

        Args:
            experiment: What to export.
            include_content: When False, only structure, Scores and metadata are sent. An
                example that already exists keeps the inputs and references it has.

        Returns:
            The report. Cases and Scores are confirmed; runs are queued in the SDK and flushed
            at the end of the export.
        """
        started = self._started_at or self._started.setdefault(experiment.name, self._clock())
        session = LangSmithExport(
            self.client,
            experiment,
            self._dataset_name or experiment.name,
            started,
        )
        report = export_experiment(
            experiment, session.send, include_content=include_content, sleep=self._sleep
        )
        report.notes.extend(session.notes)
        try:
            self.client.flush()
        except Exception as error:
            report.notes.append(f"flushing the queued runs failed: {type(error).__name__}: {error}")
        return report

    def close(self) -> None:
        """Close the client the Adapter built; one passed in is left open."""
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

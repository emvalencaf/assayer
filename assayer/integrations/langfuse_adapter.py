"""LangfuseAdapter: exports an Experiment to Langfuse, one dataset run per repetition.

The Cases become items of a dataset (the item id is the `case_id`), each repetition becomes a
dataset run named `{experiment}/rep-{n}`, each Trajectory becomes a trace of typed observations
linked to its item, and each Score becomes a `NUMERIC` score. Observations are sent as OTLP spans
through the REST API, because the SDK's tracing API cannot set observation ids or times, and
those must be deterministic for a re-export to update instead of duplicate.
"""

import datetime as dt
import os
import time
from collections.abc import Callable
from types import TracebackType
from typing import Self

from langfuse import Langfuse

from assayer.adapters import AdapterConfigError, ExportReport, export_experiment
from assayer.integrations.langfuse_export import LangfuseExport
from assayer.models import Experiment


class LangfuseAdapter:
    """Exports an Experiment to Langfuse. Sync only, not thread-safe: one export at a time.

    Trajectories carry no timing, so observations get a synthetic one: every observation of an
    export starts at the time of the Adapter's first export of that Experiment, offset by one
    microsecond per Step so the Steps stay in order. Exporting again from the same Adapter
    reuses that time, and `started_at` fixes it across Adapters. Observations carry
    `assayer.synthetic_timing` in their metadata. Model Steps carry their tokens (and cost,
    when known) as `usage_details` and `cost_details`; a Trajectory's totals, `final_output`
    and `final_state` are in the metadata of its trace.

    Spans and dataset items are confirmed by the API. Scores go through the SDK's background
    queue, which swallows errors: they are reported as queued and flushed at the end of the
    export, and a delivery failure only shows in the `langfuse` logger. Scores carry `metadata`
    only if the installed SDK accepts it; otherwise it is dropped and the report notes it.

    Args:
        client: A `langfuse.Langfuse`. It is left open by `close`. Without it, one is built
            from the keys. Note that the SDK keeps one client per public key, so a client
            built here reuses an existing one for the same key.
        public_key: Defaults to `LANGFUSE_PUBLIC_KEY`.
        secret_key: Defaults to `LANGFUSE_SECRET_KEY`.
        base_url: Defaults to `LANGFUSE_BASE_URL`, then the SDK's (EU cloud). US, HIPAA and
            self-hosted installations need it.
        dataset_name: Name of the Langfuse dataset the Cases go to, created when missing and
            reused otherwise. Defaults to the Experiment's name.
        started_at: Start time of every observation, timezone-aware. Pass the same value to
            export an Experiment again from a new Adapter.
        name: Name of the Adapter. Must be non-empty.
        clock: Gives the current time; injected so tests are deterministic.
        sleep: Waits between retries; pass a no-op in tests.

    Raises:
        AdapterConfigError: If name or dataset_name is empty, started_at has no timezone, or
            there is no client and no keys.
    """

    def __init__(
        self,
        client: Langfuse | None = None,
        *,
        public_key: str | None = None,
        secret_key: str | None = None,
        base_url: str | None = None,
        dataset_name: str | None = None,
        started_at: dt.datetime | None = None,
        name: str = "langfuse",
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
            public = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY")
            secret = secret_key or os.environ.get("LANGFUSE_SECRET_KEY")
            if not public or not secret:
                raise AdapterConfigError(
                    "no Langfuse credentials: set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY, "
                    "pass public_key and secret_key, or pass a langfuse.Langfuse"
                )
            client = Langfuse(public_key=public, secret_key=secret, base_url=base_url)
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
            include_content: When False, only structure, Scores and metadata are sent. A dataset
                item that already exists keeps the input and expected output it has.

        Returns:
            The report. Cases and observations are confirmed; Scores are queued in the SDK and
            flushed at the end of the export.
        """
        started = self._started_at or self._started.setdefault(experiment.name, self._clock())
        session = LangfuseExport(
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
            report.notes.append(
                f"flushing the queued scores failed: {type(error).__name__}: {error}"
            )
        return report

    def close(self) -> None:
        """Shut down the client the Adapter built; one passed in is left open."""
        if self._owns_client:
            self.client.shutdown()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

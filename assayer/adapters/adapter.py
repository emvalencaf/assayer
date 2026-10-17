"""The Adapter Protocol: how an Experiment reaches an observability backend."""

from types import TracebackType
from typing import Protocol, Self, runtime_checkable

from assayer.adapters.report import ExportReport
from assayer.models import Experiment


@runtime_checkable
class Adapter(Protocol):
    """Exports an Experiment to a backend. Sync only, not thread-safe: one export at a time.

    Implementations raise `AdapterConfigError` from the constructor for local misconfiguration
    (no network call), and report every later problem in the `ExportReport` instead of raising.
    Exporting the same Experiment again updates what is there, it does not duplicate it.
    """

    name: str

    def export(self, experiment: Experiment, *, include_content: bool = True) -> ExportReport:
        """Export the Experiment.

        Args:
            experiment: What to export.
            include_content: When False, only structure, Scores and metadata are sent, not
                inputs, outputs, final outputs, final states or Case references.

        Returns:
            What was confirmed, queued, failed and skipped.
        """
        ...

    def close(self) -> None:
        """Release what the Adapter created; a client passed in by the caller is left open."""
        ...

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

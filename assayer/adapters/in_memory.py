"""An Adapter that keeps the export in memory, for tests and as the bar for real Adapters."""

import time
from collections import defaultdict, deque
from collections.abc import Callable
from types import TracebackType
from typing import Any, Self

from assayer.adapters.errors import AdapterCallError, AdapterConfigError
from assayer.adapters.export import Delivery, PlannedItem, export_experiment
from assayer.adapters.report import ExportItem, ExportReport, TargetKind
from assayer.models import Experiment


class InMemoryAdapter:
    """Stores exported items in `items`, keyed by kind and id, so re-exporting overwrites.

    Args:
        name: Name of the Adapter. Must be non-empty.
        queue: When True, items are reported as queued instead of confirmed, like an SDK that
            buffers them.
        sleep: Waits between retries; pass a no-op in tests.

    Raises:
        AdapterConfigError: If name is empty.
    """

    def __init__(
        self,
        name: str = "in-memory",
        *,
        queue: bool = False,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not name.strip():
            raise AdapterConfigError("name must not be empty")
        self.name = name
        self.items: dict[ExportItem, dict[str, Any]] = {}
        self.closed = False
        self._queue = queue
        self._sleep = sleep
        self._faults: dict[TargetKind, dict[int, deque[AdapterCallError]]] = defaultdict(dict)

    def fail_on(self, target_kind: TargetKind, *errors: AdapterCallError, nth: int = 0) -> None:
        """Make sending the `nth` item of a kind (in export order) raise `errors`, one per attempt.

        Once the errors are used up, sending succeeds, so a retryable error followed by nothing
        models a transient failure.
        """
        self._faults[target_kind][nth] = deque(errors)

    def export(self, experiment: Experiment, *, include_content: bool = True) -> ExportReport:
        """Store the Experiment's items.

        Args:
            experiment: What to export.
            include_content: When False, payloads hold structure, Scores and metadata only.

        Returns:
            The report; failures injected with `fail_on` appear in it, they are not raised.
        """
        position: dict[ExportItem, int] = {}
        counts: dict[TargetKind, int] = defaultdict(int)

        def send(entry: PlannedItem) -> Delivery:
            kind = entry.item.target_kind
            if entry.item not in position:  # a retry sends the same item again
                position[entry.item] = counts[kind]
                counts[kind] += 1
            faults = self._faults[kind].get(position[entry.item])
            if faults:
                raise faults.popleft()
            self.items[entry.item] = entry.payload
            return "queued" if self._queue else "confirmed"

        return export_experiment(
            experiment, send, include_content=include_content, sleep=self._sleep
        )

    def close(self) -> None:
        """Mark the Adapter closed."""
        self.closed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

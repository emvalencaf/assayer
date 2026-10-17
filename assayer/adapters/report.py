"""What an export reports back: what was delivered, what failed and what was not tried."""

from dataclasses import dataclass, field
from typing import Literal

from assayer.adapters.errors import FAILURE_KINDS, FailureKind

TargetKind = Literal["experiment", "case", "trajectory", "step", "score"]
TARGET_KINDS = ("experiment", "case", "trajectory", "step", "score")


@dataclass(frozen=True)
class ExportItem:
    """One exported thing, named by its kind and its deterministic id."""

    target_kind: TargetKind
    target_id: str


@dataclass(frozen=True)
class ExportFailure:
    """An item that could not be exported.

    Args:
        target_kind: One of "experiment" (the export could not be planned), "case", "trajectory",
            "step" or "score".
        target_id: The deterministic id of the item.
        kind: One of the closed failure taxonomy.
        message: What went wrong.
        retryable: Whether exporting again may succeed.

    Raises:
        ValueError: If target_kind or kind is unknown.
    """

    target_kind: TargetKind
    target_id: str
    kind: FailureKind
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        """Validate the kinds.

        Raises:
            ValueError: If target_kind or kind is unknown.
        """
        if self.target_kind not in TARGET_KINDS:
            raise ValueError(f"target_kind must be one of {TARGET_KINDS}")
        if self.kind not in FAILURE_KINDS:
            raise ValueError(f"kind must be one of {FAILURE_KINDS}")


@dataclass
class ExportReport:
    """The outcome of exporting an Experiment.

    Args:
        confirmed: Items the backend acknowledged.
        queued: Items handed to an SDK that buffers them, delivery not confirmed.
        failed: Items that could not be exported.
        skipped: Items not tried because an `auth` failure aborted the export.
        notes: Things dropped or degraded on purpose, such as unsupported metadata.
    """

    confirmed: list[ExportItem] = field(default_factory=list)
    queued: list[ExportItem] = field(default_factory=list)
    failed: list[ExportFailure] = field(default_factory=list)
    skipped: list[ExportItem] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Whether nothing failed and nothing was skipped."""
        return not self.failed and not self.skipped

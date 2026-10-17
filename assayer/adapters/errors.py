"""Errors of the Adapter boundary and the closed failure taxonomy."""

from typing import Literal

FailureKind = Literal["auth", "rate_limited", "validation", "transport", "unsupported", "unknown"]
FAILURE_KINDS = ("auth", "rate_limited", "validation", "transport", "unsupported", "unknown")

_RETRYABLE = ("rate_limited", "transport")


class AdapterConfigError(ValueError):
    """Local misconfiguration of an Adapter, raised by its constructor before any network call."""


class AdapterCallError(Exception):
    """A call to a backend failed. Backend code raises it; the export turns it into a failure.

    Args:
        kind: One of the closed failure taxonomy.
        message: What went wrong.
        retryable: Whether trying again may succeed. Defaults to True for `rate_limited` and
            `transport`, False for the other kinds.
        retry_after: Seconds the backend asked to wait before the next attempt, if any.

    Raises:
        ValueError: If kind is not in the taxonomy.
    """

    def __init__(
        self,
        kind: FailureKind,
        message: str,
        *,
        retryable: bool | None = None,
        retry_after: float | None = None,
    ) -> None:
        if kind not in FAILURE_KINDS:
            raise ValueError(f"kind must be one of {FAILURE_KINDS}")
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.retryable = kind in _RETRYABLE if retryable is None else retryable
        self.retry_after = retry_after

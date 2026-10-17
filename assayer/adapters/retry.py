"""Retry policy for direct calls to a backend."""

import time
from collections.abc import Callable
from typing import TypeVar

from assayer.adapters.errors import AdapterCallError

T = TypeVar("T")

ATTEMPTS = 3
BASE_DELAY = 1.0
MAX_RETRY_AFTER = 60.0


def call_with_retry(
    call: Callable[[], T],
    *,
    attempts: int = ATTEMPTS,
    base_delay: float = BASE_DELAY,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call `call`, trying again on a retryable `AdapterCallError`.

    Waits `base_delay * 2**n` between attempts, or the backend's `retry_after` capped at 60 s.

    Args:
        call: The backend call.
        attempts: Total attempts, the first included.
        base_delay: Seconds before the first retry.
        sleep: Waits; injected so tests do not.

    Returns:
        What `call` returned.

    Raises:
        AdapterCallError: The error of the last attempt, or a non-retryable one at once.
    """
    for attempt in range(attempts):
        try:
            return call()
        except AdapterCallError as error:
            if not error.retryable or attempt == attempts - 1:
                raise
            if error.retry_after is not None:
                delay = min(error.retry_after, MAX_RETRY_AFTER)
            else:
                delay = base_delay * 2**attempt
            sleep(delay)
    raise AssertionError("unreachable")  # attempts < 1

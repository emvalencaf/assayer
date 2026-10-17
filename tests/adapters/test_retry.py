import pytest

from assayer.adapters import AdapterCallError, call_with_retry


def _flaky(*errors):
    queue = list(errors)

    def call():
        if queue:
            raise queue.pop(0)
        return "ok"

    return call


def test_backs_off_exponentially_and_gives_up_after_three_attempts():
    waits = []
    error = AdapterCallError("transport", "reset")

    with pytest.raises(AdapterCallError):
        call_with_retry(_flaky(error, error, error, error), sleep=waits.append)

    assert waits == [1.0, 2.0]


def test_honors_retry_after_up_to_sixty_seconds():
    waits = []

    call_with_retry(
        _flaky(
            AdapterCallError("rate_limited", "x", retry_after=5),
            AdapterCallError("rate_limited", "x", retry_after=600),
        ),
        sleep=waits.append,
    )

    assert waits == [5, 60.0]


def test_does_not_retry_what_is_not_retryable():
    waits = []

    with pytest.raises(AdapterCallError):
        call_with_retry(_flaky(AdapterCallError("auth", "no")), sleep=waits.append)

    assert waits == []


def test_unknown_kind_is_rejected():
    with pytest.raises(ValueError):
        AdapterCallError("weird", "x")

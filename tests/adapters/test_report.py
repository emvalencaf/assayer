import pytest

from assayer.adapters import AdapterCallError, ExportFailure, ExportItem, ExportReport


def test_report_is_ok_only_without_failures_and_skips():
    item = ExportItem("case", "a")
    failure = ExportFailure("case", "a", "transport", "x")

    assert ExportReport(confirmed=[item]).ok
    assert not ExportReport(failed=[failure]).ok
    assert not ExportReport(skipped=[item]).ok


def test_failure_rejects_unknown_kinds():
    with pytest.raises(ValueError):
        ExportFailure("case", "a", "weird", "x")
    with pytest.raises(ValueError):
        ExportFailure("thing", "a", "auth", "x")


def test_only_rate_limits_and_transport_errors_are_retryable_by_default():
    retryable = {
        k: AdapterCallError(k, "x").retryable
        for k in ("auth", "rate_limited", "validation", "transport", "unsupported", "unknown")
    }

    assert retryable == {
        "auth": False,
        "rate_limited": True,
        "validation": False,
        "transport": True,
        "unsupported": False,
        "unknown": False,
    }
    assert AdapterCallError("unknown", "x", retryable=True).retryable

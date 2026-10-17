"""Adapters: the vendor-neutral boundary to observability backends.

`LangfuseAdapter` and `LangSmithAdapter` are importable from here too; they are loaded on first
access and need `assayer[langfuse]` or `assayer[langsmith]`.
"""

import importlib

from assayer.adapters.adapter import Adapter
from assayer.adapters.errors import (
    FAILURE_KINDS,
    AdapterCallError,
    AdapterConfigError,
    FailureKind,
)
from assayer.adapters.export import (
    Delivery,
    ExportPlan,
    PlannedItem,
    export_experiment,
    plan_export,
    run_export,
)
from assayer.adapters.ids import (
    case_export_id,
    score_ids,
    step_id,
    step_key,
    trajectory_id,
)
from assayer.adapters.in_memory import InMemoryAdapter
from assayer.adapters.report import ExportFailure, ExportItem, ExportReport
from assayer.adapters.retry import call_with_retry

_LAZY = {
    "LangSmithAdapter": "assayer.integrations.langsmith_adapter",
    "LangfuseAdapter": "assayer.integrations.langfuse_adapter",
}


def __getattr__(name: str) -> object:
    """Load a backend Adapter on first use, so that the core imports without its extra."""
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), *_LAZY])


__all__ = [
    "FAILURE_KINDS",
    "Adapter",
    "AdapterCallError",
    "AdapterConfigError",
    "Delivery",
    "ExportFailure",
    "ExportItem",
    "ExportPlan",
    "ExportReport",
    "FailureKind",
    "InMemoryAdapter",
    "PlannedItem",
    "call_with_retry",
    "case_export_id",
    "export_experiment",
    "plan_export",
    "run_export",
    "score_ids",
    "step_id",
    "step_key",
    "trajectory_id",
]

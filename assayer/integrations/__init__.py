"""Integration modules for external services.

Each Adapter needs its own extra (`assayer[langfuse]`, `assayer[langsmith]`) and is loaded
on first access, so importing this package needs neither.
"""

import importlib

_LAZY = {
    "LangSmithAdapter": "assayer.integrations.langsmith_adapter",
    "LangfuseAdapter": "assayer.integrations.langfuse_adapter",
}


def __getattr__(name: str) -> object:
    """Load an Adapter on first use, so that the core imports without its extra."""
    if name in _LAZY:
        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), *_LAZY])


__all__ = ["LangSmithAdapter", "LangfuseAdapter"]

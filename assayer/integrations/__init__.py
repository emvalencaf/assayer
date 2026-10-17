"""Integration modules for external services.

Each Adapter needs its own extra (`llm-assayer-eval[langfuse]`,
`llm-assayer-eval[langsmith]`) and is loaded
on first access, so importing this package needs neither.
"""

from assayer._extras import lazy_exports

__getattr__, __dir__ = lazy_exports(
    __name__,
    {
        "LangSmithAdapter": "assayer.integrations.langsmith_adapter",
        "LangfuseAdapter": "assayer.integrations.langfuse_adapter",
    },
)

__all__ = ["LangSmithAdapter", "LangfuseAdapter"]

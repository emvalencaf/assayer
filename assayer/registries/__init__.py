"""Registry of metrics.

`Registry` is instantiable and holds no global state; built-in and custom metrics are
registered into it the same way.
"""

from assayer.registries.registry import Registry

__all__ = ["Registry"]

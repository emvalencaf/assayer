"""Optional dependencies: import them on demand and name the extra when one is missing."""

import importlib
from types import ModuleType


def missing_extra(extra: str, feature: str) -> ImportError:
    """Build the ImportError that tells the user which extra to install.

    Args:
        extra: Name of the extra, such as `langfuse`.
        feature: What needs it, such as `LangfuseAdapter`.

    Returns:
        An ImportError naming `assayer[extra]`.
    """
    return ImportError(f"{feature} needs the {extra} extra: pip install 'assayer[{extra}]'")


def require(module: str, extra: str, feature: str) -> ModuleType:
    """Import an optional module.

    Args:
        module: Dotted name of the module to import.
        extra: The extra that installs it.
        feature: What needs it, for the error message.

    Returns:
        The imported module.

    Raises:
        ImportError: If the module is not installed, naming `assayer[extra]`.
    """
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        raise missing_extra(extra, feature) from exc

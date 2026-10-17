"""Optional dependencies: import them on demand and name the extra when one is missing."""

import importlib
from collections.abc import Callable
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


def lazy_exports(
    package: str, exports: dict[str, str]
) -> tuple[Callable[[str], object], Callable[[], list[str]]]:
    """Build the module `__getattr__` and `__dir__` that load names that need an extra.

    Args:
        package: `__name__` of the module the hooks are for.
        exports: Maps each lazy name to the module that defines it.

    Returns:
        The `__getattr__` and `__dir__` to assign in that module.
    """

    def module_getattr(name: str) -> object:
        if name in exports:
            return getattr(importlib.import_module(exports[name]), name)
        raise AttributeError(f"module {package!r} has no attribute {name!r}")

    def module_dir() -> list[str]:
        return sorted([*vars(importlib.import_module(package)), *exports])

    return module_getattr, module_dir

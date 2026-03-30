"""Signal registry for auto-registration and discovery."""
from __future__ import annotations
from typing import Type
from signals.base import BaseSignal

# Global signal registry
_SIGNAL_REGISTRY: dict[str, Type[BaseSignal]] = {}


def register_signal(cls: Type[BaseSignal]) -> Type[BaseSignal]:
    """Decorator to auto-register a signal class."""
    _SIGNAL_REGISTRY[cls.__name__] = cls
    return cls


def get_registered_signals() -> dict[str, Type[BaseSignal]]:
    """Return all registered signal classes."""
    return _SIGNAL_REGISTRY.copy()


def get_signal(name: str) -> Type[BaseSignal] | None:
    """Get a registered signal class by name."""
    return _SIGNAL_REGISTRY.get(name)

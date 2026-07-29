"""Helpers for fail-loud status-model wiring to producer signals."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def connect_required(owner: Any, signal_name: str, callback: Callable[..., None]) -> None:
    """Connect ``owner.signal_name`` to ``callback``.

    Raises ``AttributeError`` if the attribute is missing or is not connectable.
    Migrated status models use this instead of silent ``_connect_if_signal``.
    """
    signal = getattr(owner, signal_name, None)
    if signal is None or not hasattr(signal, "connect"):
        owner_name = type(owner).__name__
        raise AttributeError(f"Required signal {owner_name}.{signal_name} is missing or not connectable")
    signal.connect(lambda *_args, **_kwargs: callback())

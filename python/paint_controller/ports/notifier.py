"""Device change-notification Protocol for pure HAL adapters (Level C).

Adapters mutate plain state then call ``notifier.notify(name, *args)``.
Presentation / I/O shells map names to Qt Signals. This module is Qt-free.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DeviceNotifier(Protocol):
    """Duck-typed notify surface for pure device adapters.

    ``name`` is a producer signal key (e.g. ``\"distance_changed\"``), matching
    the Status wiring schema used by ``SimpleDeviceStatus`` / ``connect_required``.
    Extra ``args`` are forwarded to Signal.emit for payload signals
    (e.g. ``error_state_changed(bool, str)``).
    """

    def notify(self, name: str, *args: object) -> None:
        """Signal that field/event ``name`` changed."""
        ...


class NullDeviceNotifier:
    """No-op default for pure unit tests or optional inject."""

    def notify(self, name: str, *args: object) -> None:
        return None


class RecordingDeviceNotifier:
    """Test double: records notify names (and args) in call order."""

    def __init__(self) -> None:
        self.names: list[str] = []
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def notify(self, name: str, *args: object) -> None:
        self.names.append(name)
        self.calls.append((name, args))

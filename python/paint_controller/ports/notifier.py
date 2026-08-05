"""Device change-notification Protocol for pure HAL adapters (Level C).

Adapters mutate plain state then call ``notifier.notify(name)``. Presentation /
I/O shells map names to Qt Signals. This module is Qt-free.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class DeviceNotifier(Protocol):
    """Duck-typed notify surface for pure device adapters.

    ``name`` is a producer signal key (e.g. ``\"distance_changed\"``), matching
    the Status wiring schema used by ``SimpleDeviceStatus`` / ``connect_required``.
    """

    def notify(self, name: str) -> None:
        """Signal that field/event ``name`` changed."""
        ...


class NullDeviceNotifier:
    """No-op default for pure unit tests or optional inject."""

    def notify(self, name: str) -> None:
        return None


class RecordingDeviceNotifier:
    """Test double: records notify names in call order."""

    def __init__(self) -> None:
        self.names: list[str] = []

    def notify(self, name: str) -> None:
        self.names.append(name)

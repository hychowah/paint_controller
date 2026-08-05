"""Qt Signal mirror for :class:`~paint_controller.ports.notifier.DeviceNotifier`.

Used by composition-owned I/O shells / future pure-HAL pilots (Level C P1+).
Not a hardware HAL — only maps notify names to ``Signal.emit``.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


class SignalDeviceNotifier(QObject):
    """Maps ``DeviceNotifier`` names to ``owner.<name>.emit()``.

    ``owner`` may be this object or an external shell that declares the Signals
    Status models already wire via ``connect_required``.
    """

    def __init__(self, owner: QObject, parent: QObject | None = None) -> None:
        super().__init__(parent)
        if owner is None:
            raise TypeError("owner must not be None")
        self._owner = owner

    def notify(self, name: str) -> None:
        sig = getattr(self._owner, name, None)
        if sig is None or not hasattr(sig, "emit"):
            owner_name = type(self._owner).__name__
            raise AttributeError(
                f"Required signal {owner_name}.{name} is missing or not emittable"
            )
        sig.emit()

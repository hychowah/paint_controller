"""Composition-owned QObject lifetime parent for device I/O (Level C P2).

Parents :class:`RosTelemetryBridge` instances and :class:`AvailabilityWatchdog`
timers so pure or dual-role adapters are not the Qt lifetime root for marshal
hops.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


class DeviceIoShell(QObject):
    """Empty QObject shell used only for lifetime parenting of bridges/timers."""

    def __init__(self, name: str = "", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.name = name

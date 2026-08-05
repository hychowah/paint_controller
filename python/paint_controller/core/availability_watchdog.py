"""Qt timer host for availability polling (Level C P2).

Owns the QTimer; pure policy stays in :class:`AvailabilityState` + device
``_check_availability`` callbacks.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QObject, QTimer


class AvailabilityWatchdog(QObject):
    """Periodic main-thread tick that invokes ``on_tick``."""

    def __init__(
        self,
        on_tick: Callable[[], None],
        *,
        interval_ms: int = 200,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if on_tick is None:
            raise TypeError("on_tick must not be None")
        self._on_tick = on_tick
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(int(interval_ms))

    @property
    def is_active(self) -> bool:
        return self._timer.isActive()

    def stop(self) -> None:
        if self._timer.isActive():
            self._timer.stop()

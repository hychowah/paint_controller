"""ROS → Qt main telemetry marshal (TD-056).

Deep module dual to :mod:`ros_io`: RosThread (or any non-UI thread) may only
``post`` immutable POD snapshots; QObject-visible mutation runs on the Qt main
thread via explicit ``QueuedConnection`` + last-wins coalesce.

Not a status HAL and not a command bus.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any, TypeVar

from PySide6.QtCore import QObject, Qt, Signal, Slot

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RosTelemetryBridge(QObject):
    """Last-wins telemetry bridge: ``post`` anywhere, ``apply_fn`` only on main.

    Construct on the Qt main thread with ``parent`` typically the device controller.
    """

    _wake = Signal()

    def __init__(self, apply_fn: Callable[[Any], None], parent: QObject | None = None) -> None:
        super().__init__(parent)
        if apply_fn is None:
            raise TypeError("apply_fn must not be None")
        self._apply_fn = apply_fn
        self._lock = threading.Lock()
        self._pending: Any | None = None
        self._scheduled = False
        # Explicit QueuedConnection: never rely on Auto for the marshal hop.
        self._wake.connect(self._on_wake, Qt.QueuedConnection)

    def post(self, snapshot: Any) -> None:
        """Accept a frozen POD from any thread. Does not call apply_fn."""
        with self._lock:
            self._pending = snapshot
            if self._scheduled:
                return
            self._scheduled = True
        self._wake.emit()

    @Slot()
    def _on_wake(self) -> None:
        with self._lock:
            snap = self._pending
            self._pending = None
            self._scheduled = False
        if snap is not None:
            try:
                self._apply_fn(snap)
            except Exception:
                logger.exception("RosTelemetryBridge apply_fn failed")
        # Re-arm if a post raced after we cleared pending.
        with self._lock:
            if self._pending is not None and not self._scheduled:
                self._scheduled = True
                rearm = True
            else:
                rearm = False
        if rearm:
            self._wake.emit()

    def pending_snapshot(self) -> Any | None:
        """Test/diagnostics: current pending POD (may be None)."""
        with self._lock:
            return self._pending

    @property
    def is_scheduled(self) -> bool:
        with self._lock:
            return self._scheduled


class ImmediateTelemetryBridge(RosTelemetryBridge):
    """Test helper: apply on ``post`` (same process, no event loop).

    Production code must use :class:`RosTelemetryBridge` so affinity is real.
    """

    def post(self, snapshot: Any) -> None:
        with self._lock:
            self._pending = snapshot
            self._scheduled = False
        self._apply_fn(snapshot)
        with self._lock:
            self._pending = None

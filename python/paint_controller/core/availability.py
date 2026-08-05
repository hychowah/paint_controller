"""Pure availability state core (Level C P2) — no Qt / no ROS.

Used by ROS device adapters and optional non-Qt tests. Timer ownership lives on
:class:`~paint_controller.core.availability_watchdog.AvailabilityWatchdog`.
"""

from __future__ import annotations

import time


class AvailabilityState:
    """Connection freshness and available flag for a single device stream."""

    def __init__(self, connection_timeout: float = 1.0) -> None:
        self.connection_timeout = float(connection_timeout)
        self.available = False
        self.last_status_update_time = 0.0

    def record_status_update(self, now: float | None = None) -> float:
        current = time.time() if now is None else float(now)
        self.last_status_update_time = current
        return current

    def time_since_last_status(self, now: float | None = None) -> float:
        current = time.time() if now is None else float(now)
        return current - self.last_status_update_time

    def status_is_recent(self, now: float | None = None) -> bool:
        return self.time_since_last_status(now) <= self.connection_timeout

    def set_available(self, value: bool) -> bool:
        """Set available flag. Returns True when the value changed."""
        value = bool(value)
        if self.available == value:
            return False
        self.available = value
        return True

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QTimer
from rclpy.node import Node


class RosStatusController(QObject):
    """Shared availability lifecycle for ROS-backed controllers.

    This base intentionally stays narrow: it owns the ROS node reference,
    availability state, last-status timestamp, the connection timeout, and the
    polling timer lifecycle. Subclasses keep their own signals and decide how
    availability changes should be emitted/logged.
    """

    def __init__(self, node: Node, *, connection_timeout: float = 1.0) -> None:
        super().__init__()
        self._node = node
        self._available = False
        self._last_status_update_time = 0.0
        self._connection_timeout = connection_timeout
        self._availability_timer = QTimer(self)

    def _start_availability_timer(self, interval_ms: int = 200) -> None:
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(interval_ms)

    def _record_status_update(self) -> float:
        current_time = time.time()
        self._last_status_update_time = current_time
        return current_time

    def _time_since_last_status(self, current_time: float | None = None) -> float:
        current_time = time.time() if current_time is None else current_time
        return current_time - self._last_status_update_time

    def _status_is_recent(self, current_time: float | None = None) -> bool:
        return self._time_since_last_status(current_time) <= self._connection_timeout

    def get_available(self) -> bool:
        return self._available

    def set_available(self, value: bool) -> bool:
        if self._available == value:
            return False
        self._available = value
        return True

    def cleanup(self) -> None:
        if self._availability_timer.isActive():
            self._availability_timer.stop()

    def _check_availability(self) -> None:
        raise NotImplementedError
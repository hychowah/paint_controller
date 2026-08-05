from __future__ import annotations

from PySide6.QtCore import QObject
from rclpy.node import Node

from paint_controller.core.availability import AvailabilityState
from paint_controller.core.availability_watchdog import AvailabilityWatchdog
from paint_controller.core.device_io_shell import DeviceIoShell


class RosStatusController(QObject):
    """Shared availability lifecycle for ROS-backed controllers.

    Availability **state** is pure (:class:`AvailabilityState`). The periodic
    check timer and telemetry-bridge lifetime parent live on a composition
    :class:`DeviceIoShell` (Level C P2). Subclasses keep their own Signals and
    decide how availability changes should be emitted/logged.
    """

    def __init__(
        self,
        node: Node,
        *,
        connection_timeout: float = 1.0,
        io_shell: QObject | None = None,
    ) -> None:
        super().__init__()
        self._node = node
        # External shell when provided; otherwise a dedicated unparented shell so
        # bridges/timers are not parented to the adapter itself.
        self._io_shell: QObject = io_shell if io_shell is not None else DeviceIoShell(
            name=type(self).__name__
        )
        self._availability = AvailabilityState(connection_timeout)
        self._watchdog: AvailabilityWatchdog | None = None

    # --- back-compat attribute surface used by subclasses and tests ----------

    @property
    def _available(self) -> bool:
        return self._availability.available

    @_available.setter
    def _available(self, value: bool) -> None:
        self._availability.available = bool(value)

    @property
    def _last_status_update_time(self) -> float:
        return self._availability.last_status_update_time

    @_last_status_update_time.setter
    def _last_status_update_time(self, value: float) -> None:
        self._availability.last_status_update_time = float(value)

    @property
    def _connection_timeout(self) -> float:
        return self._availability.connection_timeout

    @_connection_timeout.setter
    def _connection_timeout(self, value: float) -> None:
        self._availability.connection_timeout = float(value)

    @property
    def io_shell(self) -> QObject:
        return self._io_shell

    def _lifetime_parent(self) -> QObject:
        """QObject parent for bridges and the availability watchdog."""
        return self._io_shell

    def _start_availability_timer(self, interval_ms: int = 200) -> None:
        self._watchdog = AvailabilityWatchdog(
            self._check_availability,
            interval_ms=interval_ms,
            parent=self._lifetime_parent(),
        )

    def _record_status_update(self) -> float:
        return self._availability.record_status_update()

    def _time_since_last_status(self, current_time: float | None = None) -> float:
        return self._availability.time_since_last_status(current_time)

    def _status_is_recent(self, current_time: float | None = None) -> bool:
        return self._availability.status_is_recent(current_time)

    def get_available(self) -> bool:
        return self._availability.available

    def set_available(self, value: bool) -> bool:
        return self._availability.set_available(value)

    def cleanup(self) -> None:
        if self._watchdog is not None:
            self._watchdog.stop()

    def _check_availability(self) -> None:
        raise NotImplementedError

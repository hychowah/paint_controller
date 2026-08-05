#!/usr/bin/env python3
"""Pure wheel HAL (Level C P3) — no PySide6.

State + ROS command/status. Notifications via DeviceNotifier; telemetry posts
via injected ``post_status``. Presentation Signals live on ``wheel_shell``.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from paint_interfaces.msg import MoveVehiclePos, MoveVehicleSpd, VehicleStatus
from rclpy.node import Node
from std_msgs.msg import Bool

from paint_controller.core.availability import AvailabilityState
from paint_controller.ports.notifier import DeviceNotifier, NullDeviceNotifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WheelStatusSnapshot:
    """Immutable vehicle status POD for TD-056 main-thread apply."""

    recv_mono: float
    left_available: bool
    right_available: bool
    left_error: bool
    right_error: bool
    left_speed: float
    right_speed: float
    left_current: float
    right_current: float
    left_travel_mm: float
    right_travel_mm: float


class WheelHal:
    """Wheel device HAL (Qt-free)."""

    def __init__(
        self,
        node: Node,
        *,
        notifier: DeviceNotifier | None = None,
        post_status: Callable[[object], None] | None = None,
        command_bus: Any | None = None,
        connection_timeout: float = 1.0,
    ) -> None:
        self._node = node
        self._notifier: DeviceNotifier = notifier if notifier is not None else NullDeviceNotifier()
        self._post_status = post_status
        self._command_bus = command_bus
        self._availability = AvailabilityState(connection_timeout)

        self._left_wheel_speed = 0.0
        self._right_wheel_speed = 0.0
        self._left_wheel_current = 0.0
        self._right_wheel_current = 0.0
        self._left_wheel_position = 0.0
        self._right_wheel_position = 0.0

        self._left_error = False
        self._right_error = False
        self._left_motor_available = False
        self._right_motor_available = False

        self._last_left_rpm = 0
        self._last_right_rpm = 0

        self._enabled = False
        self._last_command_time = time.time()

        self._last_update_time = 0.0
        self._min_update_interval = 0.05

        self._setup_publishers()
        self._setup_subscribers()

    # --- availability surface (mirrors RosStatusController API) ---------------

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

    def get_available(self) -> bool:
        return self._availability.available

    def set_available(self, value: bool) -> bool:
        return self._availability.set_available(value)

    def _time_since_last_status(self, current_time: float | None = None) -> float:
        return self._availability.time_since_last_status(current_time)

    def _bind_cmd(self, publisher: Any, *, continuous: bool = False) -> Any:
        bus = self._command_bus
        if bus is None:
            return publisher
        from paint_controller.core.ros_io import TrafficKind

        kind = TrafficKind.CONTINUOUS if continuous else TrafficKind.ONESHOT
        return bus.bind(publisher, kind=kind)

    def _setup_publishers(self) -> None:
        self._speed_cmd_pub = self._bind_cmd(
            self._node.create_publisher(MoveVehicleSpd, "vehicle/speed/cmd", 1),
            continuous=True,
        )
        self._pos_cmd_pub = self._bind_cmd(
            self._node.create_publisher(MoveVehiclePos, "vehicle/position/cmd", 1)
        )
        self._disable_pub = self._bind_cmd(self._node.create_publisher(Bool, "wheel/disable/cmd", 1))
        self._set_zero_pub = self._bind_cmd(self._node.create_publisher(Bool, "wheel/set_zero/cmd", 1))

    def _setup_subscribers(self) -> None:
        self._status_sub = self._node.create_subscription(
            VehicleStatus, "vehicle/status", self._status_callback, 10
        )
        logger.info("Vehicle status subscriber set up on topic 'vehicle/status'")

    def _check_availability(self) -> None:
        self._recompute_available(log_disconnect=True)

    def _recompute_available(self, *, log_disconnect: bool = False) -> None:
        current_time = time.time()
        time_since_last_update = self._time_since_last_status(current_time)
        is_connected = time_since_last_update <= self._connection_timeout
        motors_available = self._left_motor_available and self._right_motor_available
        new_available = is_connected and motors_available

        if self.set_available(new_available):
            self._notifier.notify("available_changed")
            if not new_available and log_disconnect:
                if not is_connected:
                    logger.warning(
                        "Wheel controller considered disconnected: %.1fs since last message",
                        time_since_last_update,
                    )
                elif not motors_available:
                    logger.warning(
                        "Wheel controller unavailable: left_available=%s, right_available=%s",
                        self._left_motor_available,
                        self._right_motor_available,
                    )
            elif new_available and not log_disconnect:
                logger.info("Wheel controller connection restored")

    @staticmethod
    def _snapshot_from_msg(msg: VehicleStatus) -> WheelStatusSnapshot:
        return WheelStatusSnapshot(
            recv_mono=time.time(),
            left_available=bool(msg.left_available),
            right_available=bool(msg.right_available),
            left_error=bool(msg.left_error),
            right_error=bool(msg.right_error),
            left_speed=float(msg.left_speed),
            right_speed=float(msg.right_speed),
            left_current=float(msg.left_current),
            right_current=float(msg.right_current),
            left_travel_mm=float(msg.left_travel_mm),
            right_travel_mm=float(msg.right_travel_mm),
        )

    def _status_callback(self, msg: VehicleStatus) -> None:
        try:
            snap = self._snapshot_from_msg(msg)
            if self._post_status is not None:
                self._post_status(snap)
            else:
                self._apply_status_snapshot(snap)
        except Exception as e:
            logger.error("Error in vehicle status callback: %s", e)

    def _apply_status_snapshot(self, snap: object) -> None:
        if not isinstance(snap, WheelStatusSnapshot):
            logger.error("Wheel status apply expected WheelStatusSnapshot, got %s", type(snap))
            return

        self._last_status_update_time = float(snap.recv_mono)

        prev_left_error = self._left_error
        prev_right_error = self._right_error

        if self._left_motor_available != snap.left_available:
            self._left_motor_available = snap.left_available
            self._notifier.notify("left_motor_available_changed")
        if self._right_motor_available != snap.right_available:
            self._right_motor_available = snap.right_available
            self._notifier.notify("right_motor_available_changed")

        if self._left_error != snap.left_error:
            self._left_error = snap.left_error
            self._notifier.notify("left_error_changed")
        if self._right_error != snap.right_error:
            self._right_error = snap.right_error
            self._notifier.notify("right_error_changed")

        new_errors: list[str] = []
        if snap.left_error and not prev_left_error:
            new_errors.append("Left")
        if snap.right_error and not prev_right_error:
            new_errors.append("Right")
        if new_errors:
            if len(new_errors) == 2:
                error_msg = "Both track motors error"
            else:
                error_msg = f"{new_errors[0]} track motor error"
            self._notifier.notify("error_state_changed", True, error_msg)

        current_time = time.time()
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            self.set_left_wheel_speed(snap.left_speed)
            self.set_right_wheel_speed(snap.right_speed)
            self.set_left_wheel_current(snap.left_current)
            self.set_right_wheel_current(snap.right_current)
            self.set_left_wheel_position(snap.left_travel_mm)
            self.set_right_wheel_position(snap.right_travel_mm)

        self._recompute_available(log_disconnect=False)

    def command_speed(self, left_rpm: int, right_rpm: int) -> bool:
        msg = MoveVehicleSpd()
        msg.left_rpm = int(left_rpm)
        msg.right_rpm = int(right_rpm)
        self._speed_cmd_pub.publish(msg)
        self._last_command_time = time.time()
        self._last_left_rpm = int(left_rpm)
        self._last_right_rpm = int(right_rpm)
        return True

    def command_position(self, left_mm: int, right_mm: int, rpm_limit: int, relative: bool = True) -> bool:
        msg = MoveVehiclePos()
        msg.left_travel_mm = int(left_mm)
        msg.right_travel_mm = int(right_mm)
        msg.rpm_limit = int(rpm_limit)
        msg.relative = relative
        self._pos_cmd_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def command_left_wheel_speed(self, speed: float) -> bool:
        self._last_left_rpm = int(speed)
        return self.command_speed(self._last_left_rpm, self._last_right_rpm)

    def command_right_wheel_speed(self, speed: float) -> bool:
        self._last_right_rpm = int(speed)
        return self.command_speed(self._last_left_rpm, self._last_right_rpm)

    def get_left_wheel_speed(self) -> float:
        return self._left_wheel_speed

    def set_left_wheel_speed(self, value: float) -> None:
        if self._left_wheel_speed != value:
            self._left_wheel_speed = value
            self._notifier.notify("left_wheel_speed_changed")

    def get_right_wheel_speed(self) -> float:
        return self._right_wheel_speed

    def set_right_wheel_speed(self, value: float) -> None:
        if self._right_wheel_speed != value:
            self._right_wheel_speed = value
            self._notifier.notify("right_wheel_speed_changed")

    def get_left_wheel_current(self) -> float:
        return self._left_wheel_current

    def set_left_wheel_current(self, value: float) -> None:
        if self._left_wheel_current != value:
            self._left_wheel_current = value
            self._notifier.notify("left_wheel_current_changed")

    def get_right_wheel_current(self) -> float:
        return self._right_wheel_current

    def set_right_wheel_current(self, value: float) -> None:
        if self._right_wheel_current != value:
            self._right_wheel_current = value
            self._notifier.notify("right_wheel_current_changed")

    def get_left_wheel_position(self) -> float:
        return self._left_wheel_position

    def set_left_wheel_position(self, value: float) -> None:
        if self._left_wheel_position != value:
            self._left_wheel_position = value
            self._notifier.notify("left_wheel_position_changed")

    def get_right_wheel_position(self) -> float:
        return self._right_wheel_position

    def set_right_wheel_position(self, value: float) -> None:
        if self._right_wheel_position != value:
            self._right_wheel_position = value
            self._notifier.notify("right_wheel_position_changed")

    def get_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        if self._enabled != value:
            self._enabled = value
            self._notifier.notify("enabled_changed")

    def get_left_error(self) -> bool:
        return self._left_error

    def get_right_error(self) -> bool:
        return self._right_error

    def get_left_motor_available(self) -> bool:
        return self._left_motor_available

    def get_right_motor_available(self) -> bool:
        return self._right_motor_available

    @property
    def left_wheel_speed(self) -> float:
        return self.get_left_wheel_speed()

    @left_wheel_speed.setter
    def left_wheel_speed(self, value: float) -> None:
        self.set_left_wheel_speed(value)

    @property
    def right_wheel_speed(self) -> float:
        return self.get_right_wheel_speed()

    @right_wheel_speed.setter
    def right_wheel_speed(self, value: float) -> None:
        self.set_right_wheel_speed(value)

    @property
    def left_wheel_current(self) -> float:
        return self.get_left_wheel_current()

    @left_wheel_current.setter
    def left_wheel_current(self, value: float) -> None:
        self.set_left_wheel_current(value)

    @property
    def right_wheel_current(self) -> float:
        return self.get_right_wheel_current()

    @right_wheel_current.setter
    def right_wheel_current(self, value: float) -> None:
        self.set_right_wheel_current(value)

    @property
    def left_wheel_position(self) -> float:
        return self.get_left_wheel_position()

    @left_wheel_position.setter
    def left_wheel_position(self, value: float) -> None:
        self.set_left_wheel_position(value)

    @property
    def right_wheel_position(self) -> float:
        return self.get_right_wheel_position()

    @right_wheel_position.setter
    def right_wheel_position(self, value: float) -> None:
        self.set_right_wheel_position(value)

    @property
    def available(self) -> bool:
        return self.get_available()

    @property
    def enabled(self) -> bool:
        return self.get_enabled()

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self.set_enabled(value)

    @property
    def left_error(self) -> bool:
        return self.get_left_error()

    @property
    def right_error(self) -> bool:
        return self.get_right_error()

    @property
    def left_motor_available(self) -> bool:
        return self.get_left_motor_available()

    @property
    def right_motor_available(self) -> bool:
        return self.get_right_motor_available()

    def setEnabled(self, enabled: bool) -> None:
        self.set_enabled(enabled)
        msg = Bool()
        msg.data = not enabled
        self._disable_pub.publish(msg)
        logger.info("Wheel controller %s", "enabled" if enabled else "disabled")

    def setLeftSpeed(self, speed: float) -> bool:
        return self.command_left_wheel_speed(speed)

    def setRightSpeed(self, speed: float) -> bool:
        return self.command_right_wheel_speed(speed)

    def setSpeed(self, left_rpm: int, right_rpm: int) -> bool:
        return self.command_speed(left_rpm, right_rpm)

    def setPosition(self, left_mm: int, right_mm: int, rpm_limit: int, relative: bool) -> bool:
        return self.command_position(left_mm, right_mm, rpm_limit, relative)

    def emergency_stop(self) -> None:
        """Emergency stop — continuous zero (product halt traffic kind; do not change)."""
        self.command_speed(0, 0)
        logger.info("Wheel controller emergency stop activated")

    def resetWheelPosition(self) -> None:
        msg = Bool()
        msg.data = True
        self._set_zero_pub.publish(msg)
        logger.info("Wheel positions reset to zero")

    def cleanup(self) -> None:
        logger.info("Cleaning up WheelHal...")


# Tests/factory that still import WheelController from this module get the pure HAL
# only if they do not need Signals; production uses wheel_shell.WheelController.

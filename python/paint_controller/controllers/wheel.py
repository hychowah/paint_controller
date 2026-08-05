#!/usr/bin/env python3

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from paint_interfaces.msg import MoveVehiclePos, MoveVehicleSpd, VehicleStatus
from PySide6.QtCore import Signal
from rclpy.node import Node
from std_msgs.msg import Bool

from paint_controller.controllers._base import RosStatusController
from paint_controller.core.ros_telemetry import RosTelemetryBridge

if TYPE_CHECKING:
    from paint_controller.core.ros_io import RosCommandBus

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


class WheelController(RosStatusController):
    # Signals for property changed notifications
    left_wheel_speed_changed = Signal()
    right_wheel_speed_changed = Signal()
    left_wheel_current_changed = Signal()
    right_wheel_current_changed = Signal()
    left_wheel_position_changed = Signal()
    right_wheel_position_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()

    # New signals for motor error and availability
    left_error_changed = Signal()
    right_error_changed = Signal()
    left_motor_available_changed = Signal()
    right_motor_available_changed = Signal()

    # Error signal for emergency overlay (has_error: bool, message: str)
    error_state_changed = Signal(bool, str)

    def __init__(self, node: Node, command_bus: RosCommandBus | None = None) -> None:
        super().__init__(node)
        self._command_bus = command_bus

        # Initialize property values
        self._left_wheel_speed = 0.0
        self._right_wheel_speed = 0.0
        self._left_wheel_current = 0.0
        self._right_wheel_current = 0.0
        self._left_wheel_position = 0.0
        self._right_wheel_position = 0.0

        # Motor error and availability states
        self._left_error = False
        self._right_error = False
        self._left_motor_available = False
        self._right_motor_available = False

        # Track last commanded speeds for unified command
        self._last_left_rpm = 0
        self._last_right_rpm = 0

        # Connection status
        self._enabled = False
        self._last_command_time = time.time()

        # Throttle variables (telemetry floats only; applied on main)
        self._last_update_time = 0.0
        self._min_update_interval = 0.05  # 50ms minimum between UI telemetry updates

        # TD-056: ROS callback only posts POD; main apply owns QObject fields.
        self._telemetry = RosTelemetryBridge(self._apply_status_snapshot, parent=self)

        # Setup publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()

        # Create availability check timer
        self._start_availability_timer()

    def _bind_cmd(self, publisher: Any, *, continuous: bool = False) -> Any:
        """TD-054: wrap command publishers; call sites keep ``.publish(msg)``."""
        bus = self._command_bus
        if bus is None:
            return publisher
        from paint_controller.core.ros_io import TrafficKind

        kind = TrafficKind.CONTINUOUS if continuous else TrafficKind.ONESHOT
        return bus.bind(publisher, kind=kind)

    def _setup_publishers(self) -> None:
        """Setup ROS publishers for vehicle control"""
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
        """Setup ROS subscribers for vehicle status"""
        self._status_sub = self._node.create_subscription(VehicleStatus, "vehicle/status", self._status_callback, 10)
        logger.info("Vehicle status subscriber set up on topic 'vehicle/status'")

    def _check_availability(self) -> None:
        """Main-thread timer: recompute availability from main-owned status state."""
        self._recompute_available(log_disconnect=True)

    def _recompute_available(self, *, log_disconnect: bool = False) -> None:
        """Single owner for ``available`` (apply path + availability timer)."""
        current_time = time.time()
        time_since_last_update = self._time_since_last_status(current_time)
        is_connected = time_since_last_update <= self._connection_timeout
        motors_available = self._left_motor_available and self._right_motor_available
        new_available = is_connected and motors_available

        if self.set_available(new_available):
            self.available_changed.emit()
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
        """Pure mapping: ROS message → frozen POD (scalar copy only)."""
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
        """ROS spin thread: pack POD and post — no QObject field mutation."""
        try:
            self._telemetry.post(self._snapshot_from_msg(msg))
        except Exception as e:
            logger.error("Error in vehicle status callback: %s", e)

    def _apply_status_snapshot(self, snap: object) -> None:
        """Main thread only: mutate fields, NOTIFY, error edges, availability."""
        if not isinstance(snap, WheelStatusSnapshot):
            logger.error("Wheel status apply expected WheelStatusSnapshot, got %s", type(snap))
            return

        self._last_status_update_time = float(snap.recv_mono)

        # Safety / motor flags: always apply (unthrottled).
        prev_left_error = self._left_error
        prev_right_error = self._right_error

        if self._left_motor_available != snap.left_available:
            self._left_motor_available = snap.left_available
            self.left_motor_available_changed.emit()
        if self._right_motor_available != snap.right_available:
            self._right_motor_available = snap.right_available
            self.right_motor_available_changed.emit()

        if self._left_error != snap.left_error:
            self._left_error = snap.left_error
            self.left_error_changed.emit()
        if self._right_error != snap.right_error:
            self._right_error = snap.right_error
            self.right_error_changed.emit()

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
            self.error_state_changed.emit(True, error_msg)

        # Telemetry floats: throttled on main.
        current_time = time.time()
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            self.set_left_wheel_speed(snap.left_speed)
            self.set_right_wheel_speed(snap.right_speed)
            self.set_left_wheel_current(snap.left_current)
            self.set_right_wheel_current(snap.right_current)
            self.set_left_wheel_position(snap.left_travel_mm)
            self.set_right_wheel_position(snap.right_travel_mm)

        # Message implies connected for this tick; timer handles timeout disconnect.
        self._recompute_available(log_disconnect=False)

    def command_speed(self, left_rpm: int, right_rpm: int) -> bool:
        """
        Command vehicle speed using unified MoveVehicleSpd message.

        Args:
            left_rpm: Left track RPM command
            right_rpm: Right track RPM command

        Returns:
            True if command was published
        """
        msg = MoveVehicleSpd()
        msg.left_rpm = int(left_rpm)
        msg.right_rpm = int(right_rpm)
        self._speed_cmd_pub.publish(msg)
        self._last_command_time = time.time()
        self._last_left_rpm = int(left_rpm)
        self._last_right_rpm = int(right_rpm)
        return True

    def command_position(self, left_mm: int, right_mm: int, rpm_limit: int, relative: bool = True) -> bool:
        """
        Command vehicle position using MoveVehiclePos message.

        Args:
            left_mm: Left track travel distance in mm
            right_mm: Right track travel distance in mm
            rpm_limit: Maximum RPM limit for the movement
            relative: If True, distances are relative to current position

        Returns:
            True if command was published
        """
        msg = MoveVehiclePos()
        msg.left_travel_mm = int(left_mm)
        msg.right_travel_mm = int(right_mm)
        msg.rpm_limit = int(rpm_limit)
        msg.relative = relative
        self._pos_cmd_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def command_left_wheel_speed(self, speed: float) -> bool:
        """
        Command left wheel speed. Uses unified command_speed internally.

        Args:
            speed: Left wheel RPM command

        Returns:
            True if command was published
        """
        self._last_left_rpm = int(speed)
        return self.command_speed(self._last_left_rpm, self._last_right_rpm)

    def command_right_wheel_speed(self, speed: float) -> bool:
        """
        Command right wheel speed. Uses unified command_speed internally.

        Args:
            speed: Right wheel RPM command

        Returns:
            True if command was published
        """
        self._last_right_rpm = int(speed)
        return self.command_speed(self._last_left_rpm, self._last_right_rpm)

    # Property getters and setters
    def get_left_wheel_speed(self) -> float:
        return self._left_wheel_speed

    def set_left_wheel_speed(self, value: float) -> None:
        if self._left_wheel_speed != value:
            self._left_wheel_speed = value
            self.left_wheel_speed_changed.emit()

    def get_right_wheel_speed(self) -> float:
        return self._right_wheel_speed

    def set_right_wheel_speed(self, value: float) -> None:
        if self._right_wheel_speed != value:
            self._right_wheel_speed = value
            self.right_wheel_speed_changed.emit()

    def get_left_wheel_current(self) -> float:
        return self._left_wheel_current

    def set_left_wheel_current(self, value: float) -> None:
        if self._left_wheel_current != value:
            self._left_wheel_current = value
            self.left_wheel_current_changed.emit()

    def get_right_wheel_current(self) -> float:
        return self._right_wheel_current

    def set_right_wheel_current(self, value: float) -> None:
        if self._right_wheel_current != value:
            self._right_wheel_current = value
            self.right_wheel_current_changed.emit()

    def get_left_wheel_position(self) -> float:
        return self._left_wheel_position

    def set_left_wheel_position(self, value: float) -> None:
        if self._left_wheel_position != value:
            self._left_wheel_position = value
            self.left_wheel_position_changed.emit()

    def get_right_wheel_position(self) -> float:
        return self._right_wheel_position

    def set_right_wheel_position(self, value: float) -> None:
        if self._right_wheel_position != value:
            self._right_wheel_position = value
            self.right_wheel_position_changed.emit()

    def get_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        if self._enabled != value:
            self._enabled = value
            self.enabled_changed.emit()

    # Getters for new error and motor availability states
    def get_left_error(self) -> bool:
        return self._left_error

    def get_right_error(self) -> bool:
        return self._right_error

    def get_left_motor_available(self) -> bool:
        return self._left_motor_available

    def get_right_motor_available(self) -> bool:
        return self._right_motor_available

    # Plain Python properties (Level B) — QML surface is WheelStatus.
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
        """
        Enable or disable wheel control

        Args:
            enabled (bool): True to enable, False to disable
        """
        # Record operator intent (the wire protocol is inverted: we publish
        # `not enabled` to wheel/disable/cmd — publish semantics unchanged).
        self.set_enabled(enabled)
        msg = Bool()
        msg.data = not enabled
        self._disable_pub.publish(msg)
        logger.info("Wheel controller %s", "enabled" if enabled else "disabled")

    def setLeftSpeed(self, speed: float) -> bool:
        """Set left wheel speed (alias of command_left_wheel_speed)."""
        return self.command_left_wheel_speed(speed)

    def setRightSpeed(self, speed: float) -> bool:
        """Set right wheel speed (alias of command_right_wheel_speed)."""
        return self.command_right_wheel_speed(speed)

    def setSpeed(self, left_rpm: int, right_rpm: int) -> bool:
        """Set both wheel speeds using unified command."""
        return self.command_speed(left_rpm, right_rpm)

    def setPosition(self, left_mm: int, right_mm: int, rpm_limit: int, relative: bool) -> bool:
        """Command wheel position (alias of command_position)."""
        return self.command_position(left_mm, right_mm, rpm_limit, relative)

    def emergency_stop(self) -> None:
        """Emergency stop - immediately set both wheels to zero speed"""
        self.command_speed(0, 0)
        logger.info("Wheel controller emergency stop activated")

    def resetWheelPosition(self) -> None:
        """
        Reset both wheel positions to zero
        """
        msg = Bool()
        msg.data = True
        self._set_zero_pub.publish(msg)
        logger.info("Wheel positions reset to zero")

    def cleanup(self) -> None:
        """Clean up resources when shutting down"""
        super().cleanup()

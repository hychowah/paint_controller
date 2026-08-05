#!/usr/bin/env python3
"""Pure winch HAL (Level C P3) — no PySide6.

Settings max-speed is injected via ``set_max_speed`` (shell owns Settings signals).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from paint_interfaces.msg import MoveWinchLength, WinchStatus
from rclpy.node import Node
from std_msgs.msg import Bool, Float64

from paint_controller.core.availability import AvailabilityState
from paint_controller.ports.notifier import DeviceNotifier, NullDeviceNotifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class WinchStatusSnapshot:
    """Immutable winch status POD for TD-056 main-thread apply."""

    recv_mono: float
    enabled: bool
    cable_length: float
    cable_speed: float
    winch_torque: float
    motor_temperature: float
    motor_voltage: float
    motor_brake: bool
    load_detection_mode: bool
    unusual_load_detected: bool


class WinchHal:
    """Winch device HAL (Qt-free)."""

    def __init__(
        self,
        node: Node,
        *,
        notifier: DeviceNotifier | None = None,
        post_status: Callable[[object], None] | None = None,
        command_bus: Any | None = None,
        max_speed: float = 400.0,
        connection_timeout: float = 1.0,
    ) -> None:
        self._node = node
        self._notifier: DeviceNotifier = notifier if notifier is not None else NullDeviceNotifier()
        self._post_status = post_status
        self._command_bus = command_bus
        self._availability = AvailabilityState(connection_timeout)
        self._max_speed = float(max_speed)

        self._cable_length = 0.0
        self._cable_speed = 0.0
        self._winch_torque = 0.0
        self._motor_temperature = 0.0
        self._motor_voltage = 0.0
        self._motor_brake = True
        self._enabled = False
        self._load_detection_enabled = False
        self._unusual_load_detected = False

        self._last_command_time = time.time()
        self._watchdog_timeout = 1.0
        self._last_update_time = 0.0
        self._min_update_interval = 0.1

        self._setup_publishers()
        self._setup_subscribers()

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

    def set_max_speed(self, value: float) -> None:
        """Inject max speed (shell wires SettingsManager without HAL .connect)."""
        self._max_speed = float(value)
        try:
            self._node.get_logger().info(f"[WinchHal] Max speed updated to: {value}")
        except Exception:
            logger.info("[WinchHal] Max speed updated to: %s", value)

    def _bind_cmd(self, publisher: Any, *, continuous: bool = False) -> Any:
        bus = self._command_bus
        if bus is None:
            return publisher
        from paint_controller.core.ros_io import TrafficKind

        kind = TrafficKind.CONTINUOUS if continuous else TrafficKind.ONESHOT
        return bus.bind(publisher, kind=kind)

    def _setup_publishers(self) -> None:
        self._speed_rpm_pub = self._bind_cmd(
            self._node.create_publisher(Float64, "winch/move/speed/rpm/cmd", 1),
            continuous=True,
        )
        self._speed_mmps_pub = self._bind_cmd(
            self._node.create_publisher(Float64, "winch/move/speed/mmps/cmd", 1),
            continuous=True,
        )
        self._enable_pub = self._bind_cmd(self._node.create_publisher(Bool, "winch/enable/cmd", 1))
        self._move_increment_pub = self._bind_cmd(
            self._node.create_publisher(MoveWinchLength, "winch/move/increment/cmd", 1)
        )
        self._move_absolute_pub = self._bind_cmd(
            self._node.create_publisher(MoveWinchLength, "winch/move/absolute/cmd", 1)
        )
        self._load_detection_pub = self._bind_cmd(
            self._node.create_publisher(Bool, "winch/load_detection/cmd", 1)
        )

    def _setup_subscribers(self) -> None:
        self._status_sub = self._node.create_subscription(
            WinchStatus, "winch/status", self._status_callback, 10
        )
        self._node.get_logger().info("Winch status subscriber set up on topic 'winch/status'")

    def _status_callback(self, msg: WinchStatus) -> None:
        try:
            snap = self._snapshot_from_msg(msg)
            if self._post_status is not None:
                self._post_status(snap)
            else:
                self._apply_status_snapshot(snap)
        except Exception as e:
            self._node.get_logger().error(f"Error in winch status callback: {e}")

    def _check_availability(self) -> None:
        current_time = time.time()
        time_since_last_update = self._time_since_last_status(current_time)
        if time_since_last_update > self._connection_timeout:
            if self.set_available(False):
                self._notifier.notify("available_changed")
                self._node.get_logger().warning(
                    f"Winch considered disconnected: {time_since_last_update:.1f}s since last message"
                )

    @staticmethod
    def _snapshot_from_msg(msg: WinchStatus) -> WinchStatusSnapshot:
        return WinchStatusSnapshot(
            recv_mono=time.time(),
            enabled=bool(msg.enabled),
            cable_length=float(msg.cable_length),
            cable_speed=float(msg.cable_speed),
            winch_torque=float(msg.winch_torque),
            motor_temperature=float(msg.motor_temperature),
            motor_voltage=float(msg.motor_voltage),
            motor_brake=bool(msg.motor_brake),
            load_detection_mode=bool(msg.load_detection_mode),
            unusual_load_detected=bool(msg.unusual_load_detected),
        )

    def _apply_status_snapshot(self, snap: object) -> None:
        if not isinstance(snap, WinchStatusSnapshot):
            self._node.get_logger().error(
                f"Winch status apply expected WinchStatusSnapshot, got {type(snap)}"
            )
            return

        self._last_status_update_time = float(snap.recv_mono)

        if self.set_available(True):
            self._notifier.notify("available_changed")
            self._node.get_logger().info("Winch connection restored")

        current_time = time.time()
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            self.set_enabled(snap.enabled)
            self.set_cable_length(snap.cable_length)
            self.set_cable_speed(snap.cable_speed)
            self.set_winch_torque(snap.winch_torque)
            self.set_motor_temperature(snap.motor_temperature)
            self.set_motor_voltage(snap.motor_voltage)
            self.set_motor_brake(snap.motor_brake)
            self.set_load_detection_enabled(snap.load_detection_mode)
            self.set_unusual_load_detected(snap.unusual_load_detected)

    def command_speed_rpm(self, speed: float) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot command speed: Winch not available")
            return False
        safe_speed = float(self._apply_safety_limits(speed))
        msg = Float64()
        msg.data = safe_speed
        self._speed_rpm_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def command_speed_mmps(self, speed: float) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot command speed: Winch not available")
            return False
        clamped_speed = float(self._apply_safety_limits(speed))
        msg = Float64()
        msg.data = clamped_speed
        self._speed_mmps_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def move_increment(self, length_mm: int, speed_mm_s: int) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot move increment: Winch not available")
            return False
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            self._move_increment_pub.publish(msg)
            self._node.get_logger().info(f"Moving winch by: {length_mm} mm at {speed_mm_s} mm/s")
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error moving winch: {e}")
            return False

    def move_increment_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot move increment: Winch not available")
            return False
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            msg.acceleration_rpm_s = int(acceleration_rpm_s)
            self._move_increment_pub.publish(msg)
            self._node.get_logger().info(
                f"Moving winch by: {length_mm} mm at {speed_mm_s} mm/s with acceleration {acceleration_rpm_s} RPM/s"
            )
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error moving winch: {e}")
            return False

    def move_absolute(self, length_mm: int, speed_mm_s: int) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot move absolute: Winch not available")
            return False
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            self._move_absolute_pub.publish(msg)
            self._node.get_logger().info(f"Moving winch to: {length_mm} mm at {speed_mm_s} mm/s")
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error moving winch: {e}")
            return False

    def move_absolute_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot move absolute: Winch not available")
            return False
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            msg.acceleration_rpm_s = int(acceleration_rpm_s)
            self._move_absolute_pub.publish(msg)
            self._node.get_logger().info(
                f"Moving winch to: {length_mm} mm at {speed_mm_s} mm/s with acceleration {acceleration_rpm_s} RPM/s"
            )
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error moving winch: {e}")
            return False

    def set_load_detection_mode(self, enable: bool) -> bool:
        if not self.available:
            self._node.get_logger().warning("Cannot set load detection: Winch not available")
            return False
        try:
            msg = Bool()
            msg.data = enable
            self._load_detection_pub.publish(msg)
            self._node.get_logger().info(f"Load detection mode set to: {enable}")
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error setting load detection mode: {e}")
            return False

    def _apply_safety_limits(self, speed: float) -> float:
        return max(min(speed, self._max_speed), -self._max_speed)

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._check_watchdog()

    def _check_watchdog(self) -> bool:
        return time.time() - self._last_command_time < self._watchdog_timeout

    def get_cable_length(self) -> float:
        return self._cable_length

    def set_cable_length(self, value: float) -> None:
        if self._cable_length != value:
            self._cable_length = value
            self._notifier.notify("cable_length_changed")

    def get_cable_speed(self) -> float:
        return self._cable_speed

    def set_cable_speed(self, value: float) -> None:
        if self._cable_speed != value:
            self._cable_speed = value
            self._notifier.notify("cable_speed_changed")

    def get_winch_torque(self) -> float:
        return self._winch_torque

    def set_winch_torque(self, value: float) -> None:
        if self._winch_torque != value:
            self._winch_torque = value
            self._notifier.notify("winch_torque_changed")

    def get_motor_temperature(self) -> float:
        return self._motor_temperature

    def set_motor_temperature(self, value: float) -> None:
        if self._motor_temperature != value:
            self._motor_temperature = value
            self._notifier.notify("motor_temperature_changed")

    def get_motor_voltage(self) -> float:
        return self._motor_voltage

    def set_motor_voltage(self, value: float) -> None:
        if self._motor_voltage != value:
            self._motor_voltage = value
            self._notifier.notify("motor_voltage_changed")

    def get_motor_brake(self) -> bool:
        return self._motor_brake

    def set_motor_brake(self, value: bool) -> None:
        if self._motor_brake != value:
            self._motor_brake = value
            self._notifier.notify("motor_brake_changed")

    def get_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        if self._enabled != value:
            self._enabled = value
            self._notifier.notify("enabled_changed")

    def get_load_detection_enabled(self) -> bool:
        return self._load_detection_enabled

    def set_load_detection_enabled(self, value: bool) -> None:
        if self._load_detection_enabled != value:
            self._load_detection_enabled = value
            self._notifier.notify("load_detection_changed")

    def get_unusual_load_detected(self) -> bool:
        return self._unusual_load_detected

    def set_unusual_load_detected(self, value: bool) -> None:
        if self._unusual_load_detected != value:
            self._unusual_load_detected = value
            self._notifier.notify("unusual_load_detected_changed")

    @property
    def cable_length(self) -> float:
        return self.get_cable_length()

    @cable_length.setter
    def cable_length(self, value: float) -> None:
        self.set_cable_length(value)

    @property
    def cable_speed(self) -> float:
        return self.get_cable_speed()

    @cable_speed.setter
    def cable_speed(self, value: float) -> None:
        self.set_cable_speed(value)

    @property
    def winch_torque(self) -> float:
        return self.get_winch_torque()

    @winch_torque.setter
    def winch_torque(self, value: float) -> None:
        self.set_winch_torque(value)

    @property
    def motor_temperature(self) -> float:
        return self.get_motor_temperature()

    @motor_temperature.setter
    def motor_temperature(self, value: float) -> None:
        self.set_motor_temperature(value)

    @property
    def motor_voltage(self) -> float:
        return self.get_motor_voltage()

    @motor_voltage.setter
    def motor_voltage(self, value: float) -> None:
        self.set_motor_voltage(value)

    @property
    def motor_brake(self) -> bool:
        return self.get_motor_brake()

    @motor_brake.setter
    def motor_brake(self, value: bool) -> None:
        self.set_motor_brake(value)

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
    def load_detection_enabled(self) -> bool:
        return self.get_load_detection_enabled()

    @load_detection_enabled.setter
    def load_detection_enabled(self, value: bool) -> None:
        self.set_load_detection_enabled(value)

    @property
    def unusual_load_detected(self) -> bool:
        return self.get_unusual_load_detected()

    def setSpeed(self, speed: float) -> bool:
        return self.command_speed_rpm(speed)

    def moveIncrement(self, length_mm: int, speed_mm_s: int) -> bool:
        return self.move_increment(length_mm, speed_mm_s)

    def moveAbsolute(self, length_mm: int, speed_mm_s: int) -> bool:
        return self.move_absolute(length_mm, speed_mm_s)

    def moveIncrementWithAccel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        return self.move_increment_with_accel(length_mm, speed_mm_s, acceleration_rpm_s)

    def moveAbsoluteWithAccel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        return self.move_absolute_with_accel(length_mm, speed_mm_s, acceleration_rpm_s)

    def setEnabled(self, enabled: bool) -> bool:
        if not self._available:
            self._node.get_logger().warning("Cannot enable winch: Winch not available")
            return False
        msg = Bool()
        msg.data = enabled
        self._enable_pub.publish(msg)
        self._node.get_logger().info(f"Winch {'enabled' if enabled else 'disabled'}")
        return True

    def setLoadDetectionEnabled(self, enabled: bool) -> None:
        self.set_load_detection_mode(enabled)

    def cleanup(self) -> None:
        logger.info("Cleaning up WinchHal...")

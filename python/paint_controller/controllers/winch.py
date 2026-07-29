#!/usr/bin/env python3

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from paint_interfaces.msg import MoveWinchLength, WinchStatus
from PySide6.QtCore import Property, Signal, Slot
from rclpy.node import Node
from std_msgs.msg import Bool, Float64

from paint_controller.controllers._base import RosStatusController
from paint_controller.core.ros_telemetry import RosTelemetryBridge

if TYPE_CHECKING:
    from paint_controller.core.ros_io import RosCommandBus
    from paint_controller.core.settings import SettingsManager

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


class WinchController(RosStatusController):
    # Define signals for property changes
    cable_length_changed = Signal()
    cable_speed_changed = Signal()
    winch_torque_changed = Signal()
    motor_temperature_changed = Signal()
    motor_voltage_changed = Signal()
    motor_brake_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()
    load_detection_changed = Signal()
    unusual_load_detected_changed = Signal()

    def __init__(
        self,
        node: Node,
        settings_manager: SettingsManager | None = None,
        command_bus: RosCommandBus | None = None,
    ) -> None:
        super().__init__(node)
        self._command_bus = command_bus

        # Initialize property values
        # Get max_speed from settings_manager if available, otherwise use default
        if settings_manager is not None:
            self._max_speed = settings_manager.get("winch_max_speed_mmps") or 400.0
            settings_manager.winch_max_speed_mmps_changed.connect(self._on_max_speed_changed)
        else:
            self._max_speed = 400.0  # default output mm/s

        self._cable_length = 0.0
        self._cable_speed = 0.0
        self._winch_torque = 0.0
        self._motor_temperature = 0.0
        self._motor_voltage = 0.0
        self._motor_brake = True
        self._enabled = False
        self._load_detection_enabled = False
        self._unusual_load_detected = False

        # Status tracking
        self._last_command_time = time.time()
        self._watchdog_timeout = 1.0

        # Throttle variables (telemetry applied on main)
        self._last_update_time = 0.0
        self._min_update_interval = 0.1

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
        """Setup ROS publishers for winch control"""
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
        """Setup ROS subscribers for winch status"""
        self._status_sub = self._node.create_subscription(WinchStatus, "winch/status", self._status_callback, 10)
        self._node.get_logger().info("Winch status subscriber set up on topic 'winch/status'")

    def _status_callback(self, msg: WinchStatus) -> None:
        """ROS spin thread: pack POD and post — no QObject field mutation."""
        try:
            self._telemetry.post(self._snapshot_from_msg(msg))
        except Exception as e:
            self._node.get_logger().error(f"Error in winch status callback: {e}")

    def _check_availability(self) -> None:
        """Main-thread timer: mark disconnected when status is stale."""
        current_time = time.time()
        time_since_last_update = self._time_since_last_status(current_time)
        if time_since_last_update > self._connection_timeout:
            if self.set_available(False):
                self.available_changed.emit()
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
        """Main thread only: mutate fields and NOTIFY."""
        if not isinstance(snap, WinchStatusSnapshot):
            self._node.get_logger().error(f"Winch status apply expected WinchStatusSnapshot, got {type(snap)}")
            return

        self._last_status_update_time = float(snap.recv_mono)

        # Message received ⇒ connected (msg.available false can still mean "error but linked").
        if self.set_available(True):
            self.available_changed.emit()
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
        """Command winch speed with safety limits (RPM)"""
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
        """Command winch speed in mm/s with clamping to ±max_speed"""
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
        """Move winch by an increment (uses default acceleration of 30 RPM/s)"""
        if not self._available:
            self._node.get_logger().warning("Cannot move increment: Winch not available")
            return False

        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            # acceleration_rpm_s will use message default (30 RPM/s)
            self._move_increment_pub.publish(msg)
            self._node.get_logger().info(f"Moving winch by: {length_mm} mm at {speed_mm_s} mm/s")
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error moving winch: {e}")
            return False

    def move_increment_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        """Move winch by an increment with custom acceleration"""
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
        """Move winch to an absolute position (uses default acceleration of 30 RPM/s)"""
        if not self._available:
            self._node.get_logger().warning("Cannot move absolute: Winch not available")
            return False

        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            # acceleration_rpm_s will use message default (30 RPM/s)
            self._move_absolute_pub.publish(msg)
            self._node.get_logger().info(f"Moving winch to: {length_mm} mm at {speed_mm_s} mm/s")
            return True
        except Exception as e:
            self._node.get_logger().error(f"Error moving winch: {e}")
            return False

    def move_absolute_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        """Move winch to an absolute position with custom acceleration"""
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
        """Apply safety limits to winch speed"""
        return max(min(speed, self._max_speed), -self._max_speed)

    def _on_max_speed_changed(self, new_value: float) -> None:
        """Handle max_speed change from SettingsManager"""
        self._max_speed = new_value
        self._node.get_logger().info(f"[WinchController] Max speed updated to: {new_value}")

    @property
    def is_enabled(self) -> bool:
        """Check if winch is enabled and watchdog is alive"""
        return self._enabled and self._check_watchdog()

    def _check_watchdog(self) -> bool:
        """Check if commands have been sent recently enough to keep watchdog alive"""
        return time.time() - self._last_command_time < self._watchdog_timeout

    # Property getters and setters
    def get_cable_length(self) -> float:
        return self._cable_length

    def set_cable_length(self, value: float) -> None:
        if self._cable_length != value:
            self._cable_length = value
            self.cable_length_changed.emit()

    def get_cable_speed(self) -> float:
        return self._cable_speed

    def set_cable_speed(self, value: float) -> None:
        if self._cable_speed != value:
            self._cable_speed = value
            self.cable_speed_changed.emit()

    def get_winch_torque(self) -> float:
        return self._winch_torque

    def set_winch_torque(self, value: float) -> None:
        if self._winch_torque != value:
            self._winch_torque = value
            self.winch_torque_changed.emit()

    def get_motor_temperature(self) -> float:
        return self._motor_temperature

    def set_motor_temperature(self, value: float) -> None:
        if self._motor_temperature != value:
            self._motor_temperature = value
            self.motor_temperature_changed.emit()

    def get_motor_voltage(self) -> float:
        return self._motor_voltage

    def set_motor_voltage(self, value: float) -> None:
        if self._motor_voltage != value:
            self._motor_voltage = value
            self.motor_voltage_changed.emit()

    def get_motor_brake(self) -> bool:
        return self._motor_brake

    def set_motor_brake(self, value: bool) -> None:
        if self._motor_brake != value:
            self._motor_brake = value
            self.motor_brake_changed.emit()

    def get_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        if self._enabled != value:
            self._enabled = value
            self.enabled_changed.emit()

    def get_load_detection_enabled(self) -> bool:
        return self._load_detection_enabled

    def set_load_detection_enabled(self, value: bool) -> None:
        if self._load_detection_enabled != value:
            self._load_detection_enabled = value
            self.load_detection_changed.emit()

    def get_unusual_load_detected(self) -> bool:
        return self._unusual_load_detected

    def set_unusual_load_detected(self, value: bool) -> None:
        if self._unusual_load_detected != value:
            self._unusual_load_detected = value
            self.unusual_load_detected_changed.emit()

    # Define Qt properties
    cable_length = Property(float, get_cable_length, set_cable_length, notify=cable_length_changed)
    cable_speed = Property(float, get_cable_speed, set_cable_speed, notify=cable_speed_changed)
    winch_torque = Property(float, get_winch_torque, set_winch_torque, notify=winch_torque_changed)
    motor_temperature = Property(float, get_motor_temperature, set_motor_temperature, notify=motor_temperature_changed)
    motor_voltage = Property(float, get_motor_voltage, set_motor_voltage, notify=motor_voltage_changed)
    motor_brake = Property(bool, get_motor_brake, set_motor_brake, notify=motor_brake_changed)
    available = Property(bool, RosStatusController.get_available, notify=available_changed)
    enabled = Property(bool, get_enabled, set_enabled, notify=enabled_changed)
    load_detection_enabled = Property(
        bool, get_load_detection_enabled, set_load_detection_enabled, notify=load_detection_changed
    )
    unusual_load_detected = Property(bool, get_unusual_load_detected, notify=unusual_load_detected_changed)

    # Slot methods for QML
    @Slot(float)
    def setSpeed(self, speed: float) -> bool:
        """Set winch speed from QML"""
        return self.command_speed_rpm(speed)

    @Slot(int, int)
    def moveIncrement(self, length_mm: int, speed_mm_s: int) -> bool:
        """Move winch by increment from QML"""
        return self.move_increment(length_mm, speed_mm_s)

    @Slot(int, int)
    def moveAbsolute(self, length_mm: int, speed_mm_s: int) -> bool:
        """Move winch to absolute position from QML"""
        return self.move_absolute(length_mm, speed_mm_s)

    @Slot(int, int, int)
    def moveIncrementWithAccel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        """Move winch by increment with custom acceleration from QML"""
        return self.move_increment_with_accel(length_mm, speed_mm_s, acceleration_rpm_s)

    @Slot(int, int, int)
    def moveAbsoluteWithAccel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        """Move winch to absolute position with custom acceleration from QML"""
        return self.move_absolute_with_accel(length_mm, speed_mm_s, acceleration_rpm_s)

    @Slot(bool)
    def setEnabled(self, enabled: bool) -> bool:
        """Enable/disable winch from QML"""
        if not self._available:
            self._node.get_logger().warning("Cannot enable winch: Winch not available")
            return False

        # Send command to enable/disable winch
        msg = Bool()
        msg.data = enabled
        self._enable_pub.publish(msg)
        self._node.get_logger().info(f"Winch {'enabled' if enabled else 'disabled'}")
        return True

    @Slot(bool)
    def setLoadDetectionEnabled(self, enabled: bool) -> None:
        """Enable/disable load detection from QML"""
        self.set_load_detection_mode(enabled)

    def cleanup(self) -> None:
        """Clean up resources when shutting down"""
        super().cleanup()

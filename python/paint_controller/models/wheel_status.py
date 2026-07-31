"""QML-facing wheel telemetry surface with per-property NOTIFY (TD-037 Slice B)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject

from paint_controller.models.simple_device_status import SimpleDeviceStatus, _make_status_field

# Producer signal → status property notify signal name (for tests / docs).
WHEEL_STATUS_SIGNAL_MAP: tuple[tuple[str, str], ...] = (
    ("available_changed", "availableChanged"),
    ("enabled_changed", "enabledChanged"),
    ("left_motor_available_changed", "leftMotorAvailableChanged"),
    ("right_motor_available_changed", "rightMotorAvailableChanged"),
    ("left_wheel_speed_changed", "leftWheelSpeedChanged"),
    ("right_wheel_speed_changed", "rightWheelSpeedChanged"),
    ("left_wheel_current_changed", "leftWheelCurrentChanged"),
    ("right_wheel_current_changed", "rightWheelCurrentChanged"),
    ("left_wheel_position_changed", "leftWheelPositionChanged"),
    ("right_wheel_position_changed", "rightWheelPositionChanged"),
)

WHEEL_STATUS_PROPERTY_NAMES: tuple[str, ...] = (
    "available",
    "enabled",
    "leftMotorAvailable",
    "rightMotorAvailable",
    "leftWheelSpeed",
    "rightWheelSpeed",
    "leftWheelCurrent",
    "rightWheelCurrent",
    "leftWheelPosition",
    "rightWheelPosition",
)


class WheelStatus(SimpleDeviceStatus):
    """Read-only camelCase projection of ``WheelController`` for QML."""

    availableChanged, available = _make_status_field("available", bool, False)
    enabledChanged, enabled = _make_status_field("enabled", bool, False)
    leftMotorAvailableChanged, leftMotorAvailable = _make_status_field("left_motor_available", bool, False)
    rightMotorAvailableChanged, rightMotorAvailable = _make_status_field("right_motor_available", bool, False)
    leftWheelSpeedChanged, leftWheelSpeed = _make_status_field("left_wheel_speed", float, 0.0)
    rightWheelSpeedChanged, rightWheelSpeed = _make_status_field("right_wheel_speed", float, 0.0)
    leftWheelCurrentChanged, leftWheelCurrent = _make_status_field("left_wheel_current", float, 0.0)
    rightWheelCurrentChanged, rightWheelCurrent = _make_status_field("right_wheel_current", float, 0.0)
    leftWheelPositionChanged, leftWheelPosition = _make_status_field("left_wheel_position", float, 0.0)
    rightWheelPositionChanged, rightWheelPosition = _make_status_field("right_wheel_position", float, 0.0)

    _STATUS_SCHEMA: tuple[tuple[str, str, str, type], ...] = (
        ("available_changed", "available", "availableChanged", bool),
        ("enabled_changed", "enabled", "enabledChanged", bool),
        ("left_motor_available_changed", "left_motor_available", "leftMotorAvailableChanged", bool),
        ("right_motor_available_changed", "right_motor_available", "rightMotorAvailableChanged", bool),
        ("left_wheel_speed_changed", "left_wheel_speed", "leftWheelSpeedChanged", float),
        ("right_wheel_speed_changed", "right_wheel_speed", "rightWheelSpeedChanged", float),
        ("left_wheel_current_changed", "left_wheel_current", "leftWheelCurrentChanged", float),
        ("right_wheel_current_changed", "right_wheel_current", "rightWheelCurrentChanged", float),
        ("left_wheel_position_changed", "left_wheel_position", "leftWheelPositionChanged", float),
        ("right_wheel_position_changed", "right_wheel_position", "rightWheelPositionChanged", float),
    )

    def __init__(self, wheel_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(wheel_controller, parent)

"""QML-facing winch telemetry surface with per-property NOTIFY (TD-037 Slice A)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject

from paint_controller.models.simple_device_status import SimpleDeviceStatus, _make_status_field

# Producer signal → status property notify signal name (for tests / docs).
WINCH_STATUS_SIGNAL_MAP: tuple[tuple[str, str], ...] = (
    ("available_changed", "availableChanged"),
    ("enabled_changed", "enabledChanged"),
    ("load_detection_changed", "loadDetectionEnabledChanged"),
    ("cable_length_changed", "cableLengthChanged"),
    ("cable_speed_changed", "cableSpeedChanged"),
    ("winch_torque_changed", "winchTorqueChanged"),
    ("motor_temperature_changed", "motorTemperatureChanged"),
    ("motor_voltage_changed", "motorVoltageChanged"),
    ("motor_brake_changed", "motorBrakeChanged"),
    ("unusual_load_detected_changed", "unusualLoadDetectedChanged"),
)

WINCH_STATUS_PROPERTY_NAMES: tuple[str, ...] = (
    "available",
    "enabled",
    "loadDetectionEnabled",
    "cableLength",
    "cableSpeed",
    "winchTorque",
    "motorTemperature",
    "motorVoltage",
    "motorBrake",
    "unusualLoadDetected",
)


class WinchStatus(SimpleDeviceStatus):
    """Read-only camelCase projection of ``WinchController`` for QML.

    Each producer signal maps to exactly one property notify — no blanket ``changed``.
    """

    availableChanged, available = _make_status_field("available", bool, False)
    enabledChanged, enabled = _make_status_field("enabled", bool, False)
    loadDetectionEnabledChanged, loadDetectionEnabled = _make_status_field("load_detection_enabled", bool, False)
    cableLengthChanged, cableLength = _make_status_field("cable_length", float, 0.0)
    cableSpeedChanged, cableSpeed = _make_status_field("cable_speed", float, 0.0)
    winchTorqueChanged, winchTorque = _make_status_field("winch_torque", float, 0.0)
    motorTemperatureChanged, motorTemperature = _make_status_field("motor_temperature", float, 0.0)
    motorVoltageChanged, motorVoltage = _make_status_field("motor_voltage", float, 0.0)
    motorBrakeChanged, motorBrake = _make_status_field("motor_brake", bool, False)
    unusualLoadDetectedChanged, unusualLoadDetected = _make_status_field("unusual_load_detected", bool, False)

    _STATUS_SCHEMA: tuple[tuple[str, str, str, type], ...] = (
        ("available_changed", "available", "availableChanged", bool),
        ("enabled_changed", "enabled", "enabledChanged", bool),
        ("load_detection_changed", "load_detection_enabled", "loadDetectionEnabledChanged", bool),
        ("cable_length_changed", "cable_length", "cableLengthChanged", float),
        ("cable_speed_changed", "cable_speed", "cableSpeedChanged", float),
        ("winch_torque_changed", "winch_torque", "winchTorqueChanged", float),
        ("motor_temperature_changed", "motor_temperature", "motorTemperatureChanged", float),
        ("motor_voltage_changed", "motor_voltage", "motorVoltageChanged", float),
        ("motor_brake_changed", "motor_brake", "motorBrakeChanged", bool),
        ("unusual_load_detected_changed", "unusual_load_detected", "unusualLoadDetectedChanged", bool),
    )

    def __init__(self, winch_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(winch_controller, parent)

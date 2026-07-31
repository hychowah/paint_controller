"""QML-facing ESP32 valve telemetry with per-property NOTIFY (TD-037 residual)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject

from paint_controller.models.simple_device_status import SimpleDeviceStatus, _make_status_field

VALVE_STATUS_SIGNAL_MAP: tuple[tuple[str, str], ...] = (
    ("valve_position_changed", "valvePositionChanged"),
    ("valve_rate_changed", "valveRateChanged"),
    ("total_volume_changed", "totalVolumeChanged"),
    ("valve_motor_current_changed", "valveMotorCurrentChanged"),
    ("valve_motor_connected_changed", "valveMotorConnectedChanged"),
    ("flow_meter_connected_changed", "flowMeterConnectedChanged"),
    ("esp32_connected_changed", "connectedChanged"),
)

VALVE_STATUS_PROPERTY_NAMES: tuple[str, ...] = (
    "valvePosition",
    "valveRate",
    "totalVolume",
    "valveMotorCurrent",
    "valveMotorConnected",
    "flowMeterConnected",
    "connected",
)


class ValveStatus(SimpleDeviceStatus):
    """Read-only camelCase projection of ``ESP32ValveController`` for QML."""

    valvePositionChanged, valvePosition = _make_status_field("valve_position", float, 0.0)
    valveRateChanged, valveRate = _make_status_field("valve_rate", float, 0.0)
    totalVolumeChanged, totalVolume = _make_status_field("total_volume", float, 0.0)
    valveMotorCurrentChanged, valveMotorCurrent = _make_status_field("valve_motor_current", float, 0.0)
    valveMotorConnectedChanged, valveMotorConnected = _make_status_field("valve_motor_connected", bool, False)
    flowMeterConnectedChanged, flowMeterConnected = _make_status_field("flow_meter_connected", bool, False)
    connectedChanged, connected = _make_status_field("esp32_connected", bool, False)

    _STATUS_SCHEMA: tuple[tuple[str, str, str, type], ...] = (
        ("valve_position_changed", "valve_position", "valvePositionChanged", float),
        ("valve_rate_changed", "valve_rate", "valveRateChanged", float),
        ("total_volume_changed", "total_volume", "totalVolumeChanged", float),
        ("valve_motor_current_changed", "valve_motor_current", "valveMotorCurrentChanged", float),
        ("valve_motor_connected_changed", "valve_motor_connected", "valveMotorConnectedChanged", bool),
        ("flow_meter_connected_changed", "flow_meter_connected", "flowMeterConnectedChanged", bool),
        ("esp32_connected_changed", "esp32_connected", "connectedChanged", bool),
    )

    def __init__(self, valve_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(valve_controller, parent)

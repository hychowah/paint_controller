"""QML-facing ESP32 valve telemetry with per-property NOTIFY (TD-037 residual)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.models.status_wiring import connect_required

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


class ValveStatus(QObject):
    """Read-only camelCase projection of ``ESP32ValveController`` for QML."""

    valvePositionChanged = Signal()
    valveRateChanged = Signal()
    totalVolumeChanged = Signal()
    valveMotorCurrentChanged = Signal()
    valveMotorConnectedChanged = Signal()
    flowMeterConnectedChanged = Signal()
    connectedChanged = Signal()

    def __init__(self, valve_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = valve_controller
        connect_required(valve_controller, "valve_position_changed", self.valvePositionChanged.emit)
        connect_required(valve_controller, "valve_rate_changed", self.valveRateChanged.emit)
        connect_required(valve_controller, "total_volume_changed", self.totalVolumeChanged.emit)
        connect_required(valve_controller, "valve_motor_current_changed", self.valveMotorCurrentChanged.emit)
        connect_required(valve_controller, "valve_motor_connected_changed", self.valveMotorConnectedChanged.emit)
        connect_required(valve_controller, "flow_meter_connected_changed", self.flowMeterConnectedChanged.emit)
        connect_required(valve_controller, "esp32_connected_changed", self.connectedChanged.emit)

    def _bool(self, name: str, default: bool = False) -> bool:
        return bool(getattr(self._c, name, default))

    def _float(self, name: str, default: float = 0.0) -> float:
        value = getattr(self._c, name, default)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=valvePositionChanged)
    def valvePosition(self) -> float:
        return self._float("valve_position")

    @Property(float, notify=valveRateChanged)
    def valveRate(self) -> float:
        return self._float("valve_rate")

    @Property(float, notify=totalVolumeChanged)
    def totalVolume(self) -> float:
        return self._float("total_volume")

    @Property(float, notify=valveMotorCurrentChanged)
    def valveMotorCurrent(self) -> float:
        return self._float("valve_motor_current")

    @Property(bool, notify=valveMotorConnectedChanged)
    def valveMotorConnected(self) -> bool:
        return self._bool("valve_motor_connected")

    @Property(bool, notify=flowMeterConnectedChanged)
    def flowMeterConnected(self) -> bool:
        return self._bool("flow_meter_connected")

    @Property(bool, notify=connectedChanged)
    def connected(self) -> bool:
        return self._bool("esp32_connected")

"""QML-facing winch telemetry surface with per-property NOTIFY (TD-037 Slice A)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.models.status_wiring import connect_required

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


class WinchStatus(QObject):
    """Read-only camelCase projection of ``WinchController`` for QML.

    Each producer signal maps to exactly one property notify — no blanket ``changed``.
    """

    availableChanged = Signal()
    enabledChanged = Signal()
    loadDetectionEnabledChanged = Signal()
    cableLengthChanged = Signal()
    cableSpeedChanged = Signal()
    winchTorqueChanged = Signal()
    motorTemperatureChanged = Signal()
    motorVoltageChanged = Signal()
    motorBrakeChanged = Signal()
    unusualLoadDetectedChanged = Signal()

    def __init__(self, winch_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = winch_controller
        connect_required(winch_controller, "available_changed", self.availableChanged.emit)
        connect_required(winch_controller, "enabled_changed", self.enabledChanged.emit)
        connect_required(winch_controller, "load_detection_changed", self.loadDetectionEnabledChanged.emit)
        connect_required(winch_controller, "cable_length_changed", self.cableLengthChanged.emit)
        connect_required(winch_controller, "cable_speed_changed", self.cableSpeedChanged.emit)
        connect_required(winch_controller, "winch_torque_changed", self.winchTorqueChanged.emit)
        connect_required(winch_controller, "motor_temperature_changed", self.motorTemperatureChanged.emit)
        connect_required(winch_controller, "motor_voltage_changed", self.motorVoltageChanged.emit)
        connect_required(winch_controller, "motor_brake_changed", self.motorBrakeChanged.emit)
        connect_required(winch_controller, "unusual_load_detected_changed", self.unusualLoadDetectedChanged.emit)

    def _bool(self, name: str, default: bool = False) -> bool:
        return bool(getattr(self._c, name, default))

    def _float(self, name: str, default: float = 0.0) -> float:
        value = getattr(self._c, name, default)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(bool, notify=availableChanged)
    def available(self) -> bool:
        return self._bool("available")

    @Property(bool, notify=enabledChanged)
    def enabled(self) -> bool:
        return self._bool("enabled")

    @Property(bool, notify=loadDetectionEnabledChanged)
    def loadDetectionEnabled(self) -> bool:
        return self._bool("load_detection_enabled")

    @Property(float, notify=cableLengthChanged)
    def cableLength(self) -> float:
        return self._float("cable_length")

    @Property(float, notify=cableSpeedChanged)
    def cableSpeed(self) -> float:
        return self._float("cable_speed")

    @Property(float, notify=winchTorqueChanged)
    def winchTorque(self) -> float:
        return self._float("winch_torque")

    @Property(float, notify=motorTemperatureChanged)
    def motorTemperature(self) -> float:
        return self._float("motor_temperature")

    @Property(float, notify=motorVoltageChanged)
    def motorVoltage(self) -> float:
        return self._float("motor_voltage")

    @Property(bool, notify=motorBrakeChanged)
    def motorBrake(self) -> bool:
        return self._bool("motor_brake")

    @Property(bool, notify=unusualLoadDetectedChanged)
    def unusualLoadDetected(self) -> bool:
        return self._bool("unusual_load_detected")

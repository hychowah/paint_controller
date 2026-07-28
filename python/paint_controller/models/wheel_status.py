"""QML-facing wheel telemetry surface with per-property NOTIFY (TD-037 Slice B)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.models.status_wiring import connect_required

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


class WheelStatus(QObject):
    """Read-only camelCase projection of ``WheelController`` for QML."""

    availableChanged = Signal()
    enabledChanged = Signal()
    leftMotorAvailableChanged = Signal()
    rightMotorAvailableChanged = Signal()
    leftWheelSpeedChanged = Signal()
    rightWheelSpeedChanged = Signal()
    leftWheelCurrentChanged = Signal()
    rightWheelCurrentChanged = Signal()
    leftWheelPositionChanged = Signal()
    rightWheelPositionChanged = Signal()

    def __init__(self, wheel_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = wheel_controller
        connect_required(wheel_controller, "available_changed", self.availableChanged.emit)
        connect_required(wheel_controller, "enabled_changed", self.enabledChanged.emit)
        connect_required(
            wheel_controller, "left_motor_available_changed", self.leftMotorAvailableChanged.emit
        )
        connect_required(
            wheel_controller, "right_motor_available_changed", self.rightMotorAvailableChanged.emit
        )
        connect_required(wheel_controller, "left_wheel_speed_changed", self.leftWheelSpeedChanged.emit)
        connect_required(wheel_controller, "right_wheel_speed_changed", self.rightWheelSpeedChanged.emit)
        connect_required(wheel_controller, "left_wheel_current_changed", self.leftWheelCurrentChanged.emit)
        connect_required(
            wheel_controller, "right_wheel_current_changed", self.rightWheelCurrentChanged.emit
        )
        connect_required(
            wheel_controller, "left_wheel_position_changed", self.leftWheelPositionChanged.emit
        )
        connect_required(
            wheel_controller, "right_wheel_position_changed", self.rightWheelPositionChanged.emit
        )

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

    @Property(bool, notify=leftMotorAvailableChanged)
    def leftMotorAvailable(self) -> bool:
        return self._bool("left_motor_available")

    @Property(bool, notify=rightMotorAvailableChanged)
    def rightMotorAvailable(self) -> bool:
        return self._bool("right_motor_available")

    @Property(float, notify=leftWheelSpeedChanged)
    def leftWheelSpeed(self) -> float:
        return self._float("left_wheel_speed")

    @Property(float, notify=rightWheelSpeedChanged)
    def rightWheelSpeed(self) -> float:
        return self._float("right_wheel_speed")

    @Property(float, notify=leftWheelCurrentChanged)
    def leftWheelCurrent(self) -> float:
        return self._float("left_wheel_current")

    @Property(float, notify=rightWheelCurrentChanged)
    def rightWheelCurrent(self) -> float:
        return self._float("right_wheel_current")

    @Property(float, notify=leftWheelPositionChanged)
    def leftWheelPosition(self) -> float:
        return self._float("left_wheel_position")

    @Property(float, notify=rightWheelPositionChanged)
    def rightWheelPosition(self) -> float:
        return self._float("right_wheel_position")

"""Python-owned, feature-root action boundary for winch motion controls."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.action_schema import ActionSchema, schema_map
from paint_controller.models.gated_action_mixin import GatedActionMixin
from paint_controller.ports.winch import SupportsWinchMotion

ACTION_SCHEMAS = schema_map(
    ActionSchema(
        ActionKey.WINCH_MOVE_INCREMENT,
        "Winch Increment Move",
        "live-operational-motion",
        "winchActions.moveIncrement",
    ),
    ActionSchema(
        ActionKey.WINCH_MOVE_ABSOLUTE,
        "Winch Absolute Move",
        "live-operational-motion",
        "winchActions.moveAbsolute",
    ),
    ActionSchema(
        ActionKey.WINCH_RETRACT_FULL,
        "Winch Full Retract",
        "live-operational-motion",
        "winchActions.retractFull",
    ),
    ActionSchema(
        ActionKey.WINCH_EXTEND_ONE_METER,
        "Winch Extend 1m",
        "live-operational-motion",
        "winchActions.extendOneMeter",
    ),
    ActionSchema(
        ActionKey.WINCH_EMERGENCY_STOP,
        "Winch Emergency Stop",
        "emergency-exception",
        "winchActions.emergencyStop",
    ),
    ActionSchema(
        ActionKey.WINCH_LOAD_DETECTION,
        "Load Detection Toggle",
        "status-admin",
        "winchActions.setLoadDetectionEnabled",
    ),
    ActionSchema(
        ActionKey.STATUS_WINCH_ENABLE,
        "Winch Enable Toggle",
        "status-admin",
        "winchActions.setEnabled",
    ),
)


class _SupportsWinchActions(SupportsWinchMotion, Protocol):
    """Winch surface needed by page actions (motion + load detect + enable)."""

    def setLoadDetectionEnabled(self, enabled: bool) -> object: ...

    def setEnabled(self, enabled: bool) -> object: ...

    @property
    def load_detection_enabled(self) -> bool: ...

    @property
    def enabled(self) -> bool: ...


class WinchActions(QObject, GatedActionMixin):
    """Own page-level winch motion requests initiated from QML.

    TD-055: typed against winch capability ports; no stringly method-name dispatch.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        winch: _SupportsWinchActions | None,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._winch = winch
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(int, int, result=bool)
    def moveIncrement(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run_gated(
            action_key=ActionKey.WINCH_MOVE_INCREMENT,
            name="Winch increment move",
            controller=self._winch,
            invoke=lambda w: w.move_increment(length_mm, speed_mm_s),
        )

    @Slot(int, int, result=bool)
    def moveAbsolute(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run_gated(
            action_key=ActionKey.WINCH_MOVE_ABSOLUTE,
            name="Winch absolute move",
            controller=self._winch,
            invoke=lambda w: w.move_absolute(length_mm, speed_mm_s),
        )

    @Slot(result=bool)
    def retractFull(self) -> bool:
        return self._run_gated(
            action_key=ActionKey.WINCH_RETRACT_FULL,
            name="Winch full retract",
            controller=self._winch,
            invoke=lambda w: w.move_absolute(0, 500),
        )

    @Slot(result=bool)
    def extendOneMeter(self) -> bool:
        return self._run_gated(
            action_key=ActionKey.WINCH_EXTEND_ONE_METER,
            name="Winch extend 1m",
            controller=self._winch,
            invoke=lambda w: w.move_increment(1000, 500),
        )

    @Slot(result=bool)
    def emergencyStop(self) -> bool:
        return self._run_gated(
            action_key=ActionKey.WINCH_EMERGENCY_STOP,
            name="Winch emergency stop",
            controller=self._winch,
            invoke=lambda w: w.move_increment(0, 0),
        )

    @Slot(bool, result=bool)
    def setLoadDetectionEnabled(self, enabled: bool) -> bool:
        return self._run_gated(
            action_key=ActionKey.WINCH_LOAD_DETECTION,
            name="Load detection",
            controller=self._winch,
            invoke=lambda w: w.setLoadDetectionEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleLoadDetection(self) -> bool:
        current = False if self._winch is None else bool(self._winch.load_detection_enabled)
        return self.setLoadDetectionEnabled(not current)

    @Slot(bool, result=bool)
    def setEnabled(self, enabled: bool) -> bool:
        return self._run_gated(
            action_key=ActionKey.STATUS_WINCH_ENABLE,
            name="Winch enable",
            controller=self._winch,
            invoke=lambda w: w.setEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleWinchEnable(self) -> bool:
        current = False if self._winch is None else bool(self._winch.enabled)
        return self.setEnabled(not current)

"""Python-owned, feature-root action boundary for winch motion controls."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.ports.winch import SupportsWinchMotion


class _SupportsWinchActions(SupportsWinchMotion, Protocol):
    """Winch surface needed by page actions (motion + load detect + enable)."""

    def setLoadDetectionEnabled(self, enabled: bool) -> object: ...

    def setEnabled(self, enabled: bool) -> object: ...

    @property
    def load_detection_enabled(self) -> bool: ...

    @property
    def enabled(self) -> bool: ...


class WinchActions(QObject):
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
        return self._run(
            action_key=ActionKey.WINCH_MOVE_INCREMENT,
            name="Winch increment move",
            invoke=lambda w: w.move_increment(length_mm, speed_mm_s),
        )

    @Slot(int, int, result=bool)
    def moveAbsolute(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run(
            action_key=ActionKey.WINCH_MOVE_ABSOLUTE,
            name="Winch absolute move",
            invoke=lambda w: w.move_absolute(length_mm, speed_mm_s),
        )

    @Slot(result=bool)
    def retractFull(self) -> bool:
        return self._run(
            action_key=ActionKey.WINCH_RETRACT_FULL,
            name="Winch full retract",
            invoke=lambda w: w.move_absolute(0, 500),
        )

    @Slot(result=bool)
    def extendOneMeter(self) -> bool:
        return self._run(
            action_key=ActionKey.WINCH_EXTEND_ONE_METER,
            name="Winch extend 1m",
            invoke=lambda w: w.move_increment(1000, 500),
        )

    @Slot(result=bool)
    def emergencyStop(self) -> bool:
        return self._run(
            action_key=ActionKey.WINCH_EMERGENCY_STOP,
            name="Winch emergency stop",
            invoke=lambda w: w.move_increment(0, 0),
        )

    @Slot(bool, result=bool)
    def setLoadDetectionEnabled(self, enabled: bool) -> bool:
        return self._run(
            action_key=ActionKey.WINCH_LOAD_DETECTION,
            name="Load detection",
            invoke=lambda w: w.setLoadDetectionEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleLoadDetection(self) -> bool:
        current = False if self._winch is None else bool(self._winch.load_detection_enabled)
        return self.setLoadDetectionEnabled(not current)

    @Slot(bool, result=bool)
    def setEnabled(self, enabled: bool) -> bool:
        return self._run(
            action_key=ActionKey.STATUS_WINCH_ENABLE,
            name="Winch enable",
            invoke=lambda w: w.setEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleWinchEnable(self) -> bool:
        current = False if self._winch is None else bool(self._winch.enabled)
        return self.setEnabled(not current)

    def _run(self, *, action_key: str, name: str, invoke) -> bool:
        allowed, reason = self._admin_action_gate.check_action(action_key)
        if not allowed:
            return self._fail(reason)

        if self._winch is None:
            return self._fail(f"{name} is unavailable")

        try:
            result = invoke(self._winch)
        except Exception as exc:  # pragma: no cover - defensive boundary guard
            return self._fail(f"{name} failed: {exc}")

        if result is False:
            return self._fail(f"{name} was rejected by the backend")

        message = f"{name} requested"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

    def _fail(self, message: str) -> bool:
        self._logger.warning(message)
        self.operation_result.emit(False, message)
        return False

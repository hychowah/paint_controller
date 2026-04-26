"""Python-owned winch motion boundary for page-level winch controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class WinchMotionHandler(QObject):
    """Own page-level winch motion requests initiated from QML."""

    operation_result = Signal(bool, str)

    def __init__(
        self,
        winch: Any,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._winch = winch
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(int, int, result=bool)
    def requestMoveIncrement(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run_action(
            action_key="winch.move_increment",
            name="Winch increment move",
            method_name="move_increment",
            args=(length_mm, speed_mm_s),
        )

    @Slot(int, int, result=bool)
    def requestMoveAbsolute(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run_action(
            action_key="winch.move_absolute",
            name="Winch absolute move",
            method_name="move_absolute",
            args=(length_mm, speed_mm_s),
        )

    @Slot(result=bool)
    def requestRetractFull(self) -> bool:
        return self._run_action(
            action_key="winch.retract_full",
            name="Winch full retract",
            method_name="move_absolute",
            args=(0, 500),
        )

    @Slot(result=bool)
    def requestExtendOneMeter(self) -> bool:
        return self._run_action(
            action_key="winch.extend_one_meter",
            name="Winch extend 1m",
            method_name="move_increment",
            args=(1000, 500),
        )

    @Slot(result=bool)
    def requestEmergencyStop(self) -> bool:
        return self._run_action(
            action_key="winch.emergency_stop",
            name="Winch emergency stop",
            method_name="move_increment",
            args=(0, 0),
        )

    def _run_action(
        self,
        *,
        action_key: str,
        name: str,
        method_name: str,
        args: tuple[Any, ...],
    ) -> bool:
        allowed, reason = self._admin_action_gate.check_action(action_key)
        if not allowed:
            return self._fail(reason)

        if self._winch is None:
            return self._fail(f"{name} is unavailable")

        method = getattr(self._winch, method_name, None)
        if not callable(method):
            return self._fail(f"{name} is unavailable")

        try:
            result = method(*args)
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
"""Python-owned, feature-root action boundary for winch motion controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class WinchActions(QObject):
    """Own page-level winch motion requests initiated from QML.

    This model absorbs the policy previously held by ``WinchMotionHandler`` so
    that QML accesses winch motion through a single feature-root object rather
    than a handler-shaped global.
    """

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
    def moveIncrement(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run_action(
            action_key="winch.move_increment",
            name="Winch increment move",
            method_name="move_increment",
            args=(length_mm, speed_mm_s),
        )

    @Slot(int, int, result=bool)
    def moveAbsolute(self, length_mm: int, speed_mm_s: int) -> bool:
        return self._run_action(
            action_key="winch.move_absolute",
            name="Winch absolute move",
            method_name="move_absolute",
            args=(length_mm, speed_mm_s),
        )

    @Slot(result=bool)
    def retractFull(self) -> bool:
        return self._run_action(
            action_key="winch.retract_full",
            name="Winch full retract",
            method_name="move_absolute",
            args=(0, 500),
        )

    @Slot(result=bool)
    def extendOneMeter(self) -> bool:
        return self._run_action(
            action_key="winch.extend_one_meter",
            name="Winch extend 1m",
            method_name="move_increment",
            args=(1000, 500),
        )

    @Slot(result=bool)
    def emergencyStop(self) -> bool:
        return self._run_action(
            action_key="winch.emergency_stop",
            name="Winch emergency stop",
            method_name="move_increment",
            args=(0, 0),
        )

    @Slot(bool, result=bool)
    def setLoadDetectionEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="winch.load_detection",
            name="Load detection",
            method_name="setLoadDetectionEnabled",
            args=(enabled,),
        )

    @Slot(result=bool)
    def toggleLoadDetection(self) -> bool:
        return self.setLoadDetectionEnabled(not self._winch_echo("load_detection_enabled"))

    def _winch_echo(self, attribute: str) -> bool:
        """Read an echo-driven winch state attribute (False when missing)."""
        if self._winch is None:
            return False
        return bool(getattr(self._winch, attribute, False))

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

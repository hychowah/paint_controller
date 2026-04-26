"""Python-owned tuning boundary for page-level PID actions."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class TuningAdminHandler(QObject):
    """Own tuning actions initiated from QML."""

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: Any,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(float, float, float, result=bool)
    def requestShortYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run_action(
            action_key="tuning.short_yaw_pid",
            name="Short yaw PID",
            method_name="setShortParams",
            args=(p_value, i_value, d_value),
        )

    @Slot(float, float, float, result=bool)
    def requestLongYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run_action(
            action_key="tuning.long_yaw_pid",
            name="Long yaw PID",
            method_name="setLongParams",
            args=(p_value, i_value, d_value),
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

        if self._teensy is None:
            return self._fail(f"{name} is unavailable")

        method = getattr(self._teensy, method_name, None)
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

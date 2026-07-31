"""Python-owned, feature-root action boundary for tuning controls."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey


class SupportsTuningTeensy(Protocol):
    def setShortParams(self, p_value: float, i_value: float, d_value: float) -> object: ...

    def setLongParams(self, p_value: float, i_value: float, d_value: float) -> object: ...


class TuningActions(QObject):
    """Own page-level tuning requests initiated from QML.

    TD-055.7: typed invoke — no string method-name dispatch.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        teensy: SupportsTuningTeensy | None,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._teensy = teensy
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(float, float, float, result=bool)
    def setShortYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run(
            action_key=ActionKey.TUNING_SHORT_YAW_PID,
            name="Short yaw PID",
            invoke=lambda t: t.setShortParams(p_value, i_value, d_value),
        )

    @Slot(float, float, float, result=bool)
    def setLongYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run(
            action_key=ActionKey.TUNING_LONG_YAW_PID,
            name="Long yaw PID",
            invoke=lambda t: t.setLongParams(p_value, i_value, d_value),
        )

    def _run(self, *, action_key: str, name: str, invoke) -> bool:
        allowed, reason = self._admin_action_gate.check_action(action_key)
        if not allowed:
            return self._fail(reason)

        if self._teensy is None:
            return self._fail(f"{name} is unavailable")

        try:
            result = invoke(self._teensy)
        except Exception as exc:  # pragma: no cover
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

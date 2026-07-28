"""Python-owned, feature-root action boundary for wheel controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class WheelActions(QObject):
    """Own page-level wheel requests initiated from QML.

    This model absorbs the wheel policy previously held by
    ``DeviceActionHandler`` so that QML accesses wheel enable/reset through a
    single feature-root object rather than a handler-shaped global.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        wheel: Any,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._wheel = wheel
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(bool, result=bool)
    def setEnabled(self, enabled: bool) -> bool:
        return self._run_action(
            action_key="wheel.enable",
            name="Wheel enable",
            method_name="setEnabled",
            args=(enabled,),
        )

    @Slot(result=bool)
    def toggleEnabled(self) -> bool:
        current = self._wheel is not None and bool(getattr(self._wheel, "enabled", False))
        return self.setEnabled(not current)

    @Slot(result=bool)
    def resetPosition(self) -> bool:
        return self._run_action(
            action_key="wheel.reset_position",
            name="Reset wheel position",
            method_name="resetWheelPosition",
        )

    def _run_action(
        self,
        *,
        action_key: str,
        name: str,
        method_name: str,
        args: tuple[Any, ...] = (),
    ) -> bool:
        allowed, reason = self._admin_action_gate.check_action(action_key)
        if not allowed:
            return self._fail(reason)

        if self._wheel is None:
            return self._fail(f"{name} is unavailable")

        method = getattr(self._wheel, method_name, None)
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

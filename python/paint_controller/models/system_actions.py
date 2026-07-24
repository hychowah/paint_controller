"""Python-owned, feature-root action boundary for system-level actions."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class SystemActions(QObject):
    """Own system-level actions initiated from QML.

    This model absorbs the ``clearErrors`` policy previously held by
    ``DeviceOperationsHandler`` so that QML accesses it through a feature-root
    object rather than a handler-shaped global.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        heartbeat_handler: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._heartbeat_handler = heartbeat_handler
        self._logger = logger

    @Slot(result=bool)
    def clearErrors(self) -> bool:
        return self._run_action(
            name="Clear error states",
            controller=self._heartbeat_handler,
            method_name="clear_error_state",
        )

    def _run_action(
        self,
        *,
        name: str,
        controller: Any,
        method_name: str,
        args: tuple[Any, ...] = (),
    ) -> bool:
        if controller is None:
            return self._fail(f"{name} is unavailable")

        method = getattr(controller, method_name, None)
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

"""Python-owned, feature-root action boundary for system-level actions."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot


class SupportsClearErrors(Protocol):
    def clear_error_state(self) -> object: ...


class SystemActions(QObject):
    """Own system-level actions initiated from QML.

    TD-055.7: typed invoke — no string method-name dispatch.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        heartbeat_handler: SupportsClearErrors | None,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._heartbeat_handler = heartbeat_handler
        self._logger = logger

    @Slot(result=bool)
    def clearErrors(self) -> bool:
        if self._heartbeat_handler is None:
            return self._fail("Clear error states is unavailable")
        try:
            result = self._heartbeat_handler.clear_error_state()
        except Exception as exc:  # pragma: no cover
            return self._fail(f"Clear error states failed: {exc}")
        if result is False:
            return self._fail("Clear error states was rejected by the backend")
        message = "Clear error states requested"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

    def _fail(self, message: str) -> bool:
        self._logger.warning(message)
        self.operation_result.emit(False, message)
        return False

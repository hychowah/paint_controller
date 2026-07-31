"""Python-owned, feature-root action boundary for wheel controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.gated_action_mixin import GatedActionMixin
from paint_controller.ports.wheel import SupportsWheelCommands


class WheelActions(QObject, GatedActionMixin):
    """Own page-level wheel requests initiated from QML.

    TD-055: typed against ``SupportsWheelCommands``; no stringly method-name dispatch.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        wheel: SupportsWheelCommands | None,
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
        return self._run_gated(
            action_key=ActionKey.WHEEL_ENABLE,
            name="Wheel enable",
            controller=self._wheel,
            invoke=lambda w: w.setEnabled(enabled),
        )

    @Slot(result=bool)
    def toggleEnabled(self) -> bool:
        current = self._wheel is not None and bool(getattr(self._wheel, "enabled", False))
        return self.setEnabled(not current)

    @Slot(result=bool)
    def resetPosition(self) -> bool:
        return self._run_gated(
            action_key=ActionKey.WHEEL_RESET_POSITION,
            name="Reset wheel position",
            controller=self._wheel,
            invoke=lambda w: w.resetWheelPosition(),
        )

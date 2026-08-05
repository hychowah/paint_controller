"""Python-owned, feature-root action boundary for tuning controls."""

from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.action_schema import ActionSchema, schema_map
from paint_controller.models.gated_action_mixin import GatedActionMixin

ACTION_SCHEMAS = schema_map(
    ActionSchema(
        ActionKey.TUNING_SHORT_YAW_PID,
        "Short Yaw PID",
        "tuning-calibration",
        "tuningActions.setShortYawPid",
    ),
    ActionSchema(
        ActionKey.TUNING_LONG_YAW_PID,
        "Long Yaw PID",
        "tuning-calibration",
        "tuningActions.setLongYawPid",
    ),
)


class SupportsTuningTeensy(Protocol):
    def setShortParams(self, p_value: float, i_value: float, d_value: float) -> object: ...

    def setLongParams(self, p_value: float, i_value: float, d_value: float) -> object: ...


class TuningActions(QObject, GatedActionMixin):
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
        return self._run_gated(
            action_key=ActionKey.TUNING_SHORT_YAW_PID,
            name="Short yaw PID",
            controller=self._teensy,
            invoke=lambda t: t.setShortParams(p_value, i_value, d_value),
        )

    @Slot(float, float, float, result=bool)
    def setLongYawPid(self, p_value: float, i_value: float, d_value: float) -> bool:
        return self._run_gated(
            action_key=ActionKey.TUNING_LONG_YAW_PID,
            name="Long yaw PID",
            controller=self._teensy,
            invoke=lambda t: t.setLongParams(p_value, i_value, d_value),
        )

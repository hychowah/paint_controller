"""Python-owned, feature-root action boundary for base-top view calibration."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.gated_action_mixin import GatedActionMixin


class BaseTopViewActions(QObject, GatedActionMixin):
    """Own base-top view calibration requests initiated from QML.

    This model absorbs the policy previously held by ``BaseTopViewAdminHandler``
    so that QML accesses base-top view adjustments through a single feature-root
    object rather than a handler-shaped global.
    """

    operation_result = Signal(bool, str)

    def __init__(
        self,
        base_top_view_service: Any,
        admin_action_gate: Any,
        logger: Any,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._base_top_view_service = base_top_view_service
        self._admin_action_gate = admin_action_gate
        self._logger = logger

    @Slot(float, result=bool)
    def setZoom(self, value: float) -> bool:
        return self._set_property("Base top view zoom", "zoom", value)

    @Slot(float, result=bool)
    def setOffsetX(self, value: float) -> bool:
        return self._set_property("Base top view horizontal pan", "offsetX", value)

    @Slot(float, result=bool)
    def setOffsetY(self, value: float) -> bool:
        return self._set_property("Base top view vertical pan", "offsetY", value)

    @Slot(bool, result=bool)
    def setCropEnabled(self, value: bool) -> bool:
        return self._set_property("Base top view crop enabled", "cropEnabled", value)

    @Slot(float, result=bool)
    def setCropWidthRatio(self, value: float) -> bool:
        return self._set_property("Base top view crop width", "cropWidthRatio", value)

    @Slot(float, result=bool)
    def setCropCenterX(self, value: float) -> bool:
        return self._set_property("Base top view crop center", "cropCenterX", value)

    @Slot(float, result=bool)
    def setK1(self, value: float) -> bool:
        return self._set_property("Base top view distortion K1", "k1", value)

    @Slot(float, result=bool)
    def setK2(self, value: float) -> bool:
        return self._set_property("Base top view distortion K2", "k2", value)

    @Slot(float, result=bool)
    def setK3(self, value: float) -> bool:
        return self._set_property("Base top view distortion K3", "k3", value)

    @Slot(float, result=bool)
    def setK4(self, value: float) -> bool:
        return self._set_property("Base top view distortion K4", "k4", value)

    @Slot(result=bool)
    def saveSettings(self) -> bool:
        return self._run_gated(
            action_key=ActionKey.CAMERA_BASE_TOP_VIEW_SAVE,
            name="Base top view save",
            controller=self._base_top_view_service,
            invoke=lambda s: s.saveSettings(),
        )

    @Slot(result=bool)
    def resetToDefaults(self) -> bool:
        return self._run_gated(
            action_key=ActionKey.CAMERA_BASE_TOP_VIEW_RESET,
            name="Base top view reset",
            controller=self._base_top_view_service,
            invoke=lambda s: s.resetToDefaults(),
        )

    def _set_property(self, name: str, property_name: str, value: Any) -> bool:
        allowed, reason = self._admin_action_gate.check_action(ActionKey.CAMERA_BASE_TOP_VIEW_LIVE_ADJUSTMENTS)
        if not allowed:
            return self._fail(reason)

        if self._base_top_view_service is None:
            return self._fail(f"{name} is unavailable")

        try:
            setattr(self._base_top_view_service, property_name, value)
        except Exception as exc:  # pragma: no cover - defensive boundary guard
            return self._fail(f"{name} failed: {exc}")

        message = f"{name} requested"
        self._logger.info(message)
        self.operation_result.emit(True, message)
        return True

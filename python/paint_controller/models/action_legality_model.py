from __future__ import annotations

from copy import deepcopy
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot


class ActionLegalityModel(QObject):
    """Expose one QML-facing legality result seam for operator actions."""

    legalityChanged = Signal()

    def __init__(
        self,
        admin_action_gate: Any,
        capability_catalog: Any | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._admin_action_gate = admin_action_gate
        self._capability_catalog = capability_catalog

        gate_signal = getattr(admin_action_gate, "gate_state_changed", None)
        if callable(getattr(gate_signal, "connect", None)):
            gate_signal.connect(self.legalityChanged.emit)

    @Slot(str, result="QVariantMap")
    def getActionLegality(self, action_key: str):
        if not action_key:
            return {
                "actionKey": "",
                "allowed": True,
                "reason": "",
                "title": "",
                "legalStateClass": "",
                "surfaceKeys": [],
                "primarySurface": "",
            }

        evaluation = self._evaluate(action_key)
        metadata = self._metadata(action_key)

        result = deepcopy(evaluation)
        result.setdefault("actionKey", action_key)
        result.setdefault("allowed", True)
        result.setdefault("reason", "")
        result.setdefault("title", metadata.get("title", action_key))
        result["surfaceKeys"] = list(metadata.get("surfaceKeys", []))
        result["primarySurface"] = str(metadata.get("primarySurface", ""))
        result["authority"] = str(metadata.get("authority", ""))
        result["capabilityClass"] = str(metadata.get("capabilityClass", ""))
        result["immediateRuntimeSideEffect"] = bool(metadata.get("immediateRuntimeSideEffect", False))
        return result

    def _evaluate(self, action_key: str) -> dict[str, Any]:
        evaluate = getattr(self._admin_action_gate, "evaluate", None)
        if not callable(evaluate):
            return {
                "actionKey": action_key,
                "allowed": True,
                "reason": "",
                "title": action_key,
                "legalStateClass": "",
                "allowedHeartbeatStates": [],
            }

        evaluation = evaluate(action_key)
        if not isinstance(evaluation, dict):
            return {
                "actionKey": action_key,
                "allowed": True,
                "reason": "",
                "title": action_key,
                "legalStateClass": "",
                "allowedHeartbeatStates": [],
            }
        return deepcopy(evaluation)

    def _metadata(self, action_key: str) -> dict[str, Any]:
        if self._capability_catalog is None:
            return {}

        getter = getattr(self._capability_catalog, "getActionCapability", None)
        if not callable(getter):
            return {}

        metadata = getter(action_key)
        if not isinstance(metadata, dict):
            return {}
        return deepcopy(metadata)
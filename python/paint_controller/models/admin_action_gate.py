from __future__ import annotations

from copy import deepcopy
from typing import Any

from PySide6.QtCore import QObject, Property, Signal, Slot

from paint_controller.utils.constants import HeartbeatStatus


_LEGAL_STATE_ALLOWED_HEARTBEAT_STATES: dict[str, tuple[int, ...]] = {
    "overlay-primary-calibration": (HeartbeatStatus.IDLE.value,),
    "tuning-calibration": (HeartbeatStatus.IDLE.value,),
    "maintenance-preset": (HeartbeatStatus.IDLE.value,),
    "status-admin": (HeartbeatStatus.IDLE.value, HeartbeatStatus.ONTASK.value),
    "live-operational-motion": (HeartbeatStatus.IDLE.value, HeartbeatStatus.ONTASK.value),
    "emergency-exception": (
        HeartbeatStatus.IDLE.value,
        HeartbeatStatus.ONTASK.value,
        HeartbeatStatus.WARNING.value,
        HeartbeatStatus.ERROR.value,
    ),
}


_ACTION_METADATA_OVERRIDES: dict[str, dict[str, Any]] = {
    "wheel.enable": {
        "title": "Wheel Enable Toggle",
        "legalStateClass": "status-admin",
    },
    "wheel.reset_position": {
        "title": "Reset Wheel Position",
        "legalStateClass": "maintenance-preset",
    },
    "winch.load_detection": {
        "title": "Load Detection Toggle",
        "legalStateClass": "status-admin",
    },
    "winch.move_increment": {
        "title": "Winch Increment Move",
        "legalStateClass": "live-operational-motion",
    },
    "winch.move_absolute": {
        "title": "Winch Absolute Move",
        "legalStateClass": "live-operational-motion",
    },
    "winch.retract_full": {
        "title": "Winch Full Retract",
        "legalStateClass": "live-operational-motion",
    },
    "winch.extend_one_meter": {
        "title": "Winch Extend 1m",
        "legalStateClass": "live-operational-motion",
    },
    "winch.emergency_stop": {
        "title": "Winch Emergency Stop",
        "legalStateClass": "emergency-exception",
    },
}


class AdminActionGate(QObject):
    """Centralize Stage 4.5 action gating by runtime state."""

    gate_state_changed = Signal()

    def __init__(self, capability_catalog: Any, state_store: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._capability_catalog = capability_catalog
        self._state_store = state_store

        state_signal = getattr(state_store, "controller_heartbeat_state_changed", None)
        if callable(getattr(state_signal, "connect", None)):
            state_signal.connect(lambda *_args, **_kwargs: self.gate_state_changed.emit())

    @Property(int, notify=gate_state_changed)
    def heartbeatState(self) -> int:
        return self._heartbeat_state()

    @Property(bool, notify=gate_state_changed)
    def maintenanceSafeState(self) -> bool:
        return self._heartbeat_state() == HeartbeatStatus.IDLE.value

    @Slot(str, result="QVariantMap")
    def evaluate(self, action_key: str):
        metadata = self._action_metadata(action_key)
        legal_state_class = str(metadata.get("legalStateClass", "maintenance-preset"))
        allowed_states = _LEGAL_STATE_ALLOWED_HEARTBEAT_STATES.get(
            legal_state_class,
            (HeartbeatStatus.IDLE.value,),
        )
        heartbeat_state = self._heartbeat_state()
        allowed = heartbeat_state in allowed_states

        evaluation = {
            "actionKey": action_key,
            "allowed": allowed,
            "reason": "" if allowed else self._blocked_reason(metadata, heartbeat_state, allowed_states),
            "heartbeatState": heartbeat_state,
            "title": metadata.get("title", action_key),
            "legalStateClass": legal_state_class,
            "allowedHeartbeatStates": list(allowed_states),
        }
        return evaluation

    def check_action(self, action_key: str) -> tuple[bool, str]:
        evaluation = self.evaluate(action_key)
        return bool(evaluation["allowed"]), str(evaluation["reason"])

    def _heartbeat_state(self) -> int:
        return int(getattr(self._state_store, "controller_heartbeat_state", HeartbeatStatus.IDLE.value))

    def _action_metadata(self, action_key: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self._capability_catalog is not None:
            catalog_metadata = self._capability_catalog.getActionCapability(action_key)
            if isinstance(catalog_metadata, dict):
                metadata.update(deepcopy(catalog_metadata))

        metadata.update(deepcopy(_ACTION_METADATA_OVERRIDES.get(action_key, {})))
        metadata.setdefault("title", action_key)
        metadata.setdefault("legalStateClass", "maintenance-preset")
        return metadata

    def _blocked_reason(
        self,
        metadata: dict[str, Any],
        heartbeat_state: int,
        allowed_states: tuple[int, ...],
    ) -> str:
        title = str(metadata.get("title", "Action"))
        if heartbeat_state == HeartbeatStatus.ERROR.value:
            return f"{title} is blocked while the controller heartbeat is in ERROR"
        if heartbeat_state == HeartbeatStatus.WARNING.value:
            return f"{title} is blocked while the controller heartbeat is in WARNING"
        if allowed_states == (HeartbeatStatus.IDLE.value,):
            return f"{title} requires the system to be idle"
        return f"{title} is unavailable in the current runtime state"
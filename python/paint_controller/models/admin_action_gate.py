"""Discrete action legality for ``*Actions`` / settings-style slots.

Covers button and admin command slots only. Continuous stick/trigger teleop is
owned by ``ControlProcessor`` and does **not** consult this gate
(see ``ARCHITECTURE.md`` §7 and TD-046).
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from paint_controller.utils.constants import HeartbeatStatus

# Env override for lab/field (TD-036). Takes precedence over the settings flag.
_ENFORCEMENT_ENV_VAR = "PAINT_ACTION_LEGALITY_ENFORCED"
_ENV_FORCE_OFF = frozenset({"0", "false", "off", "no"})
_ENV_FORCE_ON = frozenset({"1", "true", "on", "yes"})

_LEGAL_STATE_ALLOWED_HEARTBEAT_STATES: dict[str, tuple[int, ...]] = {
    "overlay-primary-calibration": (HeartbeatStatus.IDLE.value,),
    "tuning-calibration": (HeartbeatStatus.IDLE.value,),
    "maintenance-preset": (HeartbeatStatus.IDLE.value,),
    # Settings-route / admin machine limits (TD-036): require idle for edits.
    "mixed-admin-route": (HeartbeatStatus.IDLE.value,),
    "safety-admin": (HeartbeatStatus.IDLE.value,),
    # System-control / device toggles: must remain usable in any heartbeat state
    # while field development continues (operator can re-enable devices after ERROR).
    "status-admin": (
        HeartbeatStatus.IDLE.value,
        HeartbeatStatus.ONTASK.value,
        HeartbeatStatus.WARNING.value,
        HeartbeatStatus.ERROR.value,
    ),
    "status-admin-warning-ok": (
        HeartbeatStatus.IDLE.value,
        HeartbeatStatus.ONTASK.value,
        HeartbeatStatus.WARNING.value,
        HeartbeatStatus.ERROR.value,
    ),
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
    "status.teensy_relay": {
        "title": "Teensy Relay Toggle",
        "legalStateClass": "status-admin-warning-ok",
    },
}


class AdminActionGate(QObject):
    """Centralize discrete action gating by runtime state (not continuous teleop)."""

    gate_state_changed = Signal()

    def __init__(
        self,
        capability_catalog: Any,
        state_store: Any,
        settings_manager: Any = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._capability_catalog = capability_catalog
        self._state_store = state_store
        self._settings_manager = settings_manager

        state_signal = getattr(state_store, "controller_heartbeat_state_changed", None)
        state_connect = getattr(state_signal, "connect", None)
        if callable(state_connect):
            state_connect(lambda *_args, **_kwargs: self.gate_state_changed.emit())

        enforcement_signal = getattr(settings_manager, "action_legality_enforced_changed", None)
        enforcement_connect = getattr(enforcement_signal, "connect", None)
        if callable(enforcement_connect):
            enforcement_connect(lambda *_args, **_kwargs: self.gate_state_changed.emit())

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

        if not self._enforcement_enabled():
            # Lab bypass: env PAINT_ACTION_LEGALITY_ENFORCED=0/false/off, or
            # settings action_legality_enforced=false when env is unset.
            return {
                "actionKey": action_key,
                "allowed": True,
                "reason": "",
                "heartbeatState": heartbeat_state,
                "title": metadata.get("title", action_key),
                "legalStateClass": legal_state_class,
                "allowedHeartbeatStates": list(allowed_states),
            }

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

    def _enforcement_enabled(self) -> bool:
        """Whether legality checks run.

        Precedence (TD-036):
        1. Env ``PAINT_ACTION_LEGALITY_ENFORCED`` force on/off
        2. Else settings ``action_legality_enforced`` (default True)
        """
        env_raw = os.environ.get(_ENFORCEMENT_ENV_VAR)
        if env_raw is not None:
            token = env_raw.strip().lower()
            if token in _ENV_FORCE_OFF:
                return False
            if token in _ENV_FORCE_ON:
                return True

        if self._settings_manager is None:
            # Align with schema development default (off until hardening is done).
            return False
        return bool(self._settings_manager.get("action_legality_enforced", False))

    def _action_metadata(self, action_key: str) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self._capability_catalog is not None:
            catalog_metadata = self._capability_catalog.getActionCapability(action_key)
            if isinstance(catalog_metadata, dict) and catalog_metadata:
                metadata.update(deepcopy(catalog_metadata))
            else:
                # Setting keys live in _SETTING_CAPABILITIES, not action map (TD-036).
                setting_getter = getattr(self._capability_catalog, "getSettingCapability", None)
                if callable(setting_getter):
                    setting_metadata = setting_getter(action_key)
                    if isinstance(setting_metadata, dict) and setting_metadata:
                        metadata.update(deepcopy(setting_metadata))

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

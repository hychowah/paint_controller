"""Pure discrete-action legality evaluation (TD-055 Phase 3).

No Qt / QObject. ``AdminActionGate`` is a thin shell over these functions.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any, Mapping, TypedDict

from paint_controller.utils.constants import HeartbeatStatus

_ENFORCEMENT_ENV_VAR = "PAINT_ACTION_LEGALITY_ENFORCED"
_ENV_FORCE_OFF = frozenset({"0", "false", "off", "no"})
_ENV_FORCE_ON = frozenset({"1", "true", "on", "yes"})

LEGAL_STATE_ALLOWED_HEARTBEAT_STATES: dict[str, tuple[int, ...]] = {
    "overlay-primary-calibration": (HeartbeatStatus.IDLE.value,),
    "tuning-calibration": (HeartbeatStatus.IDLE.value,),
    "maintenance-preset": (HeartbeatStatus.IDLE.value,),
    "mixed-admin-route": (HeartbeatStatus.IDLE.value,),
    "safety-admin": (HeartbeatStatus.IDLE.value,),
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

ACTION_METADATA_OVERRIDES: dict[str, dict[str, Any]] = {
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


class ActionLegalityEvaluation(TypedDict):
    actionKey: str
    allowed: bool
    reason: str
    heartbeatState: int
    title: str
    legalStateClass: str
    allowedHeartbeatStates: list[int]


def enforcement_enabled_from_env_and_settings(
    settings_get: Any | None,
    *,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Whether legality checks run.

    Precedence (TD-036):
    1. Env ``PAINT_ACTION_LEGALITY_ENFORCED`` force on/off
    2. Else settings ``action_legality_enforced`` (schema default False)
    """
    environ = os.environ if env is None else env
    env_raw = environ.get(_ENFORCEMENT_ENV_VAR)
    if env_raw is not None:
        token = env_raw.strip().lower()
        if token in _ENV_FORCE_OFF:
            return False
        if token in _ENV_FORCE_ON:
            return True

    if settings_get is None:
        return False
    if callable(settings_get):
        return bool(settings_get("action_legality_enforced", False))
    return bool(getattr(settings_get, "get", lambda *_a, **_k: False)("action_legality_enforced", False))


def resolve_action_metadata(
    action_key: str,
    *,
    catalog_action: Mapping[str, Any] | None = None,
    catalog_setting: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    if catalog_action:
        metadata.update(deepcopy(dict(catalog_action)))
    elif catalog_setting:
        metadata.update(deepcopy(dict(catalog_setting)))
    metadata.update(deepcopy(ACTION_METADATA_OVERRIDES.get(action_key, {})))
    metadata.setdefault("title", action_key)
    metadata.setdefault("legalStateClass", "maintenance-preset")
    return metadata


def blocked_reason(
    metadata: Mapping[str, Any],
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


def evaluate_action_legality(
    action_key: str,
    *,
    heartbeat_state: int,
    enforcement_enabled: bool,
    metadata: Mapping[str, Any] | None = None,
) -> ActionLegalityEvaluation:
    """Evaluate whether a discrete action is legal in the current heartbeat state."""
    meta = dict(metadata) if metadata is not None else resolve_action_metadata(action_key)
    legal_state_class = str(meta.get("legalStateClass", "maintenance-preset"))
    allowed_states = LEGAL_STATE_ALLOWED_HEARTBEAT_STATES.get(
        legal_state_class,
        (HeartbeatStatus.IDLE.value,),
    )
    title = str(meta.get("title", action_key))

    if not enforcement_enabled:
        return {
            "actionKey": action_key,
            "allowed": True,
            "reason": "",
            "heartbeatState": heartbeat_state,
            "title": title,
            "legalStateClass": legal_state_class,
            "allowedHeartbeatStates": list(allowed_states),
        }

    allowed = heartbeat_state in allowed_states
    return {
        "actionKey": action_key,
        "allowed": allowed,
        "reason": "" if allowed else blocked_reason(meta, heartbeat_state, allowed_states),
        "heartbeatState": heartbeat_state,
        "title": title,
        "legalStateClass": legal_state_class,
        "allowedHeartbeatStates": list(allowed_states),
    }

"""Discrete action legality for ``*Actions`` / settings-style slots.

Covers button and admin command slots only. Continuous stick/trigger teleop is
owned by ``ControlProcessor`` and does **not** consult this gate
(see ``ARCHITECTURE.md`` §7 and TD-046).

TD-055: pure evaluation lives in ``handlers.policy.action_legality``; this
module is a thin Qt shell for signals / QML.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal, Slot

from paint_controller.handlers.policy.action_legality import (
    LEGAL_STATE_ALLOWED_HEARTBEAT_STATES,
    evaluate_action_legality,
    enforcement_enabled_from_env_and_settings,
    resolve_action_metadata,
)
from paint_controller.utils.constants import HeartbeatStatus

# Re-export for existing tests that import the table from this module.
_LEGAL_STATE_ALLOWED_HEARTBEAT_STATES = LEGAL_STATE_ALLOWED_HEARTBEAT_STATES


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
        return evaluate_action_legality(
            action_key,
            heartbeat_state=self._heartbeat_state(),
            enforcement_enabled=self._enforcement_enabled(),
            metadata=metadata,
        )

    def check_action(self, action_key: str) -> tuple[bool, str]:
        evaluation = self.evaluate(action_key)
        return bool(evaluation["allowed"]), str(evaluation["reason"])

    def _heartbeat_state(self) -> int:
        return int(getattr(self._state_store, "controller_heartbeat_state", HeartbeatStatus.IDLE.value))

    def _enforcement_enabled(self) -> bool:
        settings_get = None
        if self._settings_manager is not None:
            settings_get = self._settings_manager.get
        return enforcement_enabled_from_env_and_settings(settings_get)

    def _action_metadata(self, action_key: str) -> dict[str, Any]:
        catalog_action = None
        catalog_setting = None
        if self._capability_catalog is not None:
            catalog_metadata = self._capability_catalog.getActionCapability(action_key)
            if isinstance(catalog_metadata, dict) and catalog_metadata:
                catalog_action = catalog_metadata
            else:
                setting_getter = getattr(self._capability_catalog, "getSettingCapability", None)
                if callable(setting_getter):
                    setting_metadata = setting_getter(action_key)
                    if isinstance(setting_metadata, dict) and setting_metadata:
                        catalog_setting = setting_metadata
        return resolve_action_metadata(
            action_key,
            catalog_action=catalog_action,
            catalog_setting=catalog_setting,
        )

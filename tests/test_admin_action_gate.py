"""Tests for AdminActionGate heartbeat gating and the development bypass flag."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from paint_controller.models.admin_action_gate import (
    _LEGAL_STATE_ALLOWED_HEARTBEAT_STATES,
    AdminActionGate,
)
from paint_controller.utils.constants import HeartbeatStatus


class _FakeStateStore(QObject):
    controller_heartbeat_state_changed = Signal()

    def __init__(self, state: int) -> None:
        super().__init__()
        self.controller_heartbeat_state = state


class _FakeSettingsManager(QObject):
    action_legality_enforced_changed = Signal(bool)

    def __init__(self, values: dict) -> None:
        super().__init__()
        self._values = dict(values)

    def get(self, key: str, default=None):
        return self._values.get(key, default)


class _FakeCatalog:
    def __init__(self, actions: dict | None = None, settings: dict | None = None) -> None:
        self._actions = dict(actions or {})
        self._settings = dict(settings or {})

    def getActionCapability(self, key: str) -> dict:
        return dict(self._actions.get(key, {}))

    def getSettingCapability(self, key: str) -> dict:
        return dict(self._settings.get(key, {}))


def _gate(
    state: int,
    settings: _FakeSettingsManager | None = None,
    catalog=None,
) -> AdminActionGate:
    return AdminActionGate(
        capability_catalog=catalog,
        state_store=_FakeStateStore(state),
        settings_manager=settings,
    )


def test_status_admin_toggles_allowed_in_error_when_enforced(qt_app) -> None:
    """System-control toggles (status-admin) are not heartbeat-blocked."""
    settings = _FakeSettingsManager({"action_legality_enforced": True})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    allowed, reason = gate.check_action("wheel.enable")

    assert allowed is True
    assert reason == ""


def test_maintenance_action_still_blocked_in_error_when_enforced(qt_app) -> None:
    settings = _FakeSettingsManager({"action_legality_enforced": True})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    allowed, reason = gate.check_action("wheel.reset_position")

    assert allowed is False
    assert "ERROR" in reason


def test_enforcement_disabled_allows_action_in_error_state(qt_app) -> None:
    settings = _FakeSettingsManager({"action_legality_enforced": False})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    evaluation = gate.evaluate("wheel.reset_position")

    assert evaluation["allowed"] is True
    assert evaluation["reason"] == ""
    assert evaluation["heartbeatState"] == HeartbeatStatus.ERROR.value


def test_enforcement_enabled_flag_preserves_blocking(qt_app) -> None:
    settings = _FakeSettingsManager({"action_legality_enforced": True})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    allowed, reason = gate.check_action("wheel.reset_position")

    assert allowed is False
    assert "ERROR" in reason


def test_flag_flip_emits_gate_state_changed(qt_app) -> None:
    settings = _FakeSettingsManager({"action_legality_enforced": False})
    gate = _gate(HeartbeatStatus.IDLE.value, settings=settings)
    emissions: list[bool] = []
    gate.gate_state_changed.connect(lambda: emissions.append(True))

    settings.action_legality_enforced_changed.emit(True)

    assert emissions == [True]


def test_emergency_exception_still_allowed_in_error_without_flag(qt_app) -> None:
    gate = _gate(HeartbeatStatus.ERROR.value)

    allowed, reason = gate.check_action("winch.emergency_stop")

    assert allowed is True
    assert reason == ""


def test_setting_key_uses_setting_capability_metadata(qt_app) -> None:
    catalog = _FakeCatalog(
        settings={
            "winch_max_speed_mmps": {
                "title": "Maximum Speed",
                "legalStateClass": "mixed-admin-route",
            }
        }
    )
    gate = _gate(HeartbeatStatus.IDLE.value, catalog=catalog)
    evaluation = gate.evaluate("winch_max_speed_mmps")

    assert evaluation["allowed"] is True
    assert evaluation["legalStateClass"] == "mixed-admin-route"
    assert evaluation["title"] == "Maximum Speed"


def test_mixed_admin_route_and_safety_admin_are_registered() -> None:
    assert "mixed-admin-route" in _LEGAL_STATE_ALLOWED_HEARTBEAT_STATES
    assert "safety-admin" in _LEGAL_STATE_ALLOWED_HEARTBEAT_STATES
    assert _LEGAL_STATE_ALLOWED_HEARTBEAT_STATES["mixed-admin-route"] == (HeartbeatStatus.IDLE.value,)


def test_env_forces_enforcement_off_despite_settings_true(monkeypatch, qt_app) -> None:
    monkeypatch.setenv("PAINT_ACTION_LEGALITY_ENFORCED", "0")
    settings = _FakeSettingsManager({"action_legality_enforced": True})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    allowed, _ = gate.check_action("wheel.reset_position")
    assert allowed is True


def test_env_forces_enforcement_on_despite_settings_false(monkeypatch, qt_app) -> None:
    monkeypatch.setenv("PAINT_ACTION_LEGALITY_ENFORCED", "1")
    settings = _FakeSettingsManager({"action_legality_enforced": False})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    allowed, reason = gate.check_action("wheel.reset_position")
    assert allowed is False
    assert "ERROR" in reason


def test_env_unset_defers_to_settings_flag(monkeypatch, qt_app) -> None:
    monkeypatch.delenv("PAINT_ACTION_LEGALITY_ENFORCED", raising=False)
    settings = _FakeSettingsManager({"action_legality_enforced": False})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)
    assert gate.check_action("wheel.reset_position")[0] is True

    settings_on = _FakeSettingsManager({"action_legality_enforced": True})
    gate_on = _gate(HeartbeatStatus.ERROR.value, settings=settings_on)
    assert gate_on.check_action("wheel.reset_position")[0] is False

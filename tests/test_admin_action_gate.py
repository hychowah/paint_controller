"""Tests for AdminActionGate heartbeat gating and the development bypass flag."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from paint_controller.models.admin_action_gate import AdminActionGate
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


def _gate(state: int, settings: _FakeSettingsManager | None = None) -> AdminActionGate:
    return AdminActionGate(
        capability_catalog=None,
        state_store=_FakeStateStore(state),
        settings_manager=settings,
    )


def test_blocks_status_admin_action_in_error_state(qt_app) -> None:
    gate = _gate(HeartbeatStatus.ERROR.value)

    allowed, reason = gate.check_action("wheel.enable")

    assert allowed is False
    assert "ERROR" in reason


def test_enforcement_disabled_allows_action_in_error_state(qt_app) -> None:
    settings = _FakeSettingsManager({"action_legality_enforced": False})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    evaluation = gate.evaluate("wheel.enable")

    assert evaluation["allowed"] is True
    assert evaluation["reason"] == ""
    assert evaluation["heartbeatState"] == HeartbeatStatus.ERROR.value


def test_enforcement_enabled_flag_preserves_blocking(qt_app) -> None:
    settings = _FakeSettingsManager({"action_legality_enforced": True})
    gate = _gate(HeartbeatStatus.ERROR.value, settings=settings)

    allowed, reason = gate.check_action("wheel.enable")

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

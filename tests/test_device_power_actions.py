"""TD-032: power/home slots absorbed into teensyActions / winchActions."""

from __future__ import annotations

from paint_controller.models.admin_action_gate import AdminActionGate
from paint_controller.models.teensy_actions import TeensyActions
from paint_controller.models.winch_actions import WinchActions
from paint_controller.utils.constants import HeartbeatStatus
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self) -> None:
        self._status = {"relay_on": False, "enabled": False}
        self.relay_calls: list[bool] = []
        self.enable_calls: list[bool] = []
        self.home_top_calls: list[bool] = []
        self.home_arm_calls: list[bool] = []

    def get_status(self) -> dict:
        return dict(self._status)

    def setRelayEnabled(self, enabled: bool) -> None:
        self.relay_calls.append(enabled)
        self._status["relay_on"] = enabled

    def setEnabled(self, enabled: bool) -> None:
        self.enable_calls.append(enabled)
        self._status["enabled"] = enabled

    def homeTopRail(self, home: bool) -> None:
        self.home_top_calls.append(home)

    def homeArm(self, home: bool) -> None:
        self.home_arm_calls.append(home)


class FakeWinch:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.enabled = False
        self.enable_calls: list[bool] = []

    def setEnabled(self, enabled: bool) -> bool:
        self.enable_calls.append(enabled)
        self.enabled = enabled
        return self.result


class FakeAdminActionGate:
    def __init__(self) -> None:
        self.results: dict[str, tuple[bool, str]] = {}
        self.calls: list[str] = []

    def set_result(self, action_key: str, allowed: bool, reason: str = "") -> None:
        self.results[action_key] = (allowed, reason)

    def check_action(self, action_key: str) -> tuple[bool, str]:
        self.calls.append(action_key)
        return self.results.get(action_key, (True, ""))


def test_toggle_methods_negate_backend_state() -> None:
    teensy = FakeTeensy()
    winch = FakeWinch()
    gate = FakeAdminActionGate()
    logger = FakeLogger()
    teensy_actions = TeensyActions(teensy=teensy, logger=logger, admin_action_gate=gate)
    winch_actions = WinchActions(winch=winch, admin_action_gate=gate, logger=logger)

    assert teensy_actions.toggleTeensyRelay() is True
    assert teensy_actions.toggleTeensyEnable() is True
    assert winch_actions.toggleWinchEnable() is True

    assert teensy.relay_calls == [True]
    assert teensy.enable_calls == [True]
    assert winch.enable_calls == [True]
    assert gate.calls == [
        "status.teensy_relay",
        "status.teensy_enable",
        "status.winch_enable",
    ]

    assert teensy_actions.toggleTeensyRelay() is True
    assert teensy_actions.toggleTeensyEnable() is True
    assert winch_actions.toggleWinchEnable() is True
    assert teensy.relay_calls == [True, False]
    assert teensy.enable_calls == [True, False]
    assert winch.enable_calls == [True, False]


def test_home_actions_remain_ungated() -> None:
    teensy = FakeTeensy()
    gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = TeensyActions(teensy=teensy, logger=logger, admin_action_gate=gate)

    assert actions.homeTopRail() is True
    assert actions.homeArm() is True
    assert teensy.home_top_calls == [True]
    assert teensy.home_arm_calls == [True]
    assert gate.calls == []


def test_winch_enable_rejection_is_reported() -> None:
    gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = WinchActions(winch=FakeWinch(result=False), admin_action_gate=gate, logger=logger)
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda ok, msg: results.append((ok, msg)))

    assert actions.toggleWinchEnable() is False
    assert results[-1] == (False, "Winch enable was rejected by the backend")


def test_teensy_relay_toggle_is_allowed_in_warning_heartbeat() -> None:
    teensy = FakeTeensy()
    logger = FakeLogger()
    state_store = type("S", (), {"controller_heartbeat_state": HeartbeatStatus.WARNING.value})()
    gate = AdminActionGate(capability_catalog=None, state_store=state_store)
    # Force enforcement on for this regression.
    gate._settings_manager = type("M", (), {"get": lambda self, k, d=None: True})()
    actions = TeensyActions(teensy=teensy, logger=logger, admin_action_gate=gate)

    assert actions.requestTeensyRelayEnabled(True) is True
    assert teensy.relay_calls == [True]

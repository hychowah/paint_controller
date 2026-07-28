"""Focused tests for the Python-owned hard device-action boundary."""

from __future__ import annotations

from paint_controller.handlers.device_actions import DeviceActionHandler
from paint_controller.models.admin_action_gate import AdminActionGate
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


def _build_handler(winch_result: bool = True) -> tuple[DeviceActionHandler, FakeTeensy, FakeWinch, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy()
    winch = FakeWinch(result=winch_result)
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    handler = DeviceActionHandler(
        teensy=teensy,
        winch=winch,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))
    return handler, teensy, winch, admin_action_gate, logger, results


def test_toggle_methods_negate_backend_state() -> None:
    handler, teensy, winch, admin_action_gate, logger, results = _build_handler()

    assert handler.toggleTeensyRelay() is True
    assert handler.toggleTeensyEnable() is True
    assert handler.toggleWinchEnable() is True

    assert teensy.relay_calls == [True]
    assert teensy.enable_calls == [True]
    assert winch.enable_calls == [True]
    assert admin_action_gate.calls == [
        "status.teensy_relay",
        "status.teensy_enable",
        "status.winch_enable",
    ]
    assert [message for _success, message in results] == [
        "Teensy relay requested",
        "Teensy enable requested",
        "Winch enable requested",
    ]
    assert logger.records[-1].message == "Winch enable requested"

    # State-driven inversion: a second toggle flips back
    assert handler.toggleTeensyRelay() is True
    assert handler.toggleTeensyEnable() is True
    assert handler.toggleWinchEnable() is True

    assert teensy.relay_calls == [True, False]
    assert teensy.enable_calls == [True, False]
    assert winch.enable_calls == [True, False]


def test_explicit_enable_request_methods_dispatch_desired_state() -> None:
    handler, teensy, winch, _gate, logger, results = _build_handler()

    assert handler.requestTeensyRelayEnabled(True) is True
    assert handler.requestTeensyEnabled(False) is True
    assert handler.requestWinchEnabled(True) is True

    assert teensy.relay_calls == [True]
    assert teensy.enable_calls == [False]
    assert winch.enable_calls == [True]
    assert [message for _success, message in results] == [
        "Teensy relay requested",
        "Teensy enable requested",
        "Winch enable requested",
    ]
    assert logger.records[-1].message == "Winch enable requested"


def test_home_actions_dispatch_to_backend() -> None:
    handler, teensy, _winch, _gate, logger, results = _build_handler()

    assert handler.homeTopRail() is True
    assert handler.homeArm() is True

    assert teensy.home_top_calls == [True]
    assert teensy.home_arm_calls == [True]
    assert [message for _success, message in results] == [
        "Home top rail requested",
        "Home arm rail requested",
    ]
    assert logger.records[-1].message == "Home arm rail requested"


def test_backend_rejection_is_reported() -> None:
    handler, _teensy, winch, _gate, logger, results = _build_handler(winch_result=False)

    assert handler.toggleWinchEnable() is False

    assert winch.enable_calls == [True]
    assert results[-1] == (False, "Winch enable was rejected by the backend")
    assert logger.records[-1].message == "Winch enable was rejected by the backend"


def test_missing_controller_is_reported() -> None:
    logger = FakeLogger()
    admin_action_gate = FakeAdminActionGate()
    handler = DeviceActionHandler(
        teensy=None,
        winch=None,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))

    assert handler.homeTopRail() is False

    assert results[-1] == (False, "Home top rail is unavailable")
    assert logger.records[-1].message == "Home top rail is unavailable"


class _FakeStateStore:
    def __init__(self, heartbeat_state: int) -> None:
        self.controller_heartbeat_state = heartbeat_state


def test_teensy_relay_toggle_is_allowed_in_warning_heartbeat() -> None:
    teensy = FakeTeensy()
    logger = FakeLogger()
    state_store = _FakeStateStore(HeartbeatStatus.WARNING.value)
    admin_action_gate = AdminActionGate(capability_catalog=None, state_store=state_store)
    handler = DeviceActionHandler(
        teensy=teensy,
        winch=None,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))

    assert handler.requestTeensyRelayEnabled(True) is True

    assert teensy.relay_calls == [True]
    assert results[-1] == (True, "Teensy relay requested")
    assert logger.records[-1].message == "Teensy relay requested"

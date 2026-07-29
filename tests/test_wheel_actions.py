"""Focused tests for the feature-root wheel action boundary."""

from __future__ import annotations

from paint_controller.models.wheel_actions import WheelActions
from tests.fakes import FakeLogger


class FakeWheel:
    def __init__(self, enabled_result: bool = True, reset_result: bool = True) -> None:
        self.enabled_result = enabled_result
        self.reset_result = reset_result
        self.enabled = False
        self.enable_calls: list[bool] = []
        self.reset_calls = 0

    def setEnabled(self, enabled: bool) -> bool:
        self.enable_calls.append(enabled)
        self.enabled = enabled
        return self.enabled_result

    def resetWheelPosition(self) -> bool:
        self.reset_calls += 1
        return self.reset_result


class FakeAdminActionGate:
    def __init__(self) -> None:
        self.results: dict[str, tuple[bool, str]] = {}
        self.calls: list[str] = []

    def set_result(self, action_key: str, allowed: bool, reason: str = "") -> None:
        self.results[action_key] = (allowed, reason)

    def check_action(self, action_key: str) -> tuple[bool, str]:
        self.calls.append(action_key)
        return self.results.get(action_key, (True, ""))


def _build_actions(
    enabled_result: bool = True, reset_result: bool = True
) -> tuple[WheelActions, FakeWheel, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    wheel = FakeWheel(enabled_result=enabled_result, reset_result=reset_result)
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = WheelActions(
        wheel=wheel,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, wheel, admin_action_gate, logger, results


def test_set_enabled_dispatches_desired_state() -> None:
    actions, wheel, admin_action_gate, logger, results = _build_actions()

    assert actions.setEnabled(True) is True
    assert actions.setEnabled(False) is True

    assert wheel.enable_calls == [True, False]
    assert admin_action_gate.calls == ["wheel.enable", "wheel.enable"]
    assert [message for _success, message in results] == [
        "Wheel enable requested",
        "Wheel enable requested",
    ]
    assert logger.records[-1].message == "Wheel enable requested"


def test_toggle_enabled_negates_backend_intent() -> None:
    actions, wheel, _gate, _logger, _results = _build_actions()

    assert actions.toggleEnabled() is True
    assert actions.toggleEnabled() is True

    assert wheel.enable_calls == [True, False]


def test_reset_position_dispatches_to_backend() -> None:
    actions, wheel, admin_action_gate, logger, results = _build_actions()

    assert actions.resetPosition() is True

    assert wheel.reset_calls == 1
    assert admin_action_gate.calls == ["wheel.reset_position"]
    assert results[-1] == (True, "Reset wheel position requested")
    assert logger.records[-1].message == "Reset wheel position requested"


def test_gate_denial_blocks_enable_before_backend_call() -> None:
    actions, wheel, admin_action_gate, _logger, results = _build_actions()
    admin_action_gate.set_result("wheel.enable", False, "Wheel enable denied")

    assert actions.setEnabled(True) is False

    assert wheel.enable_calls == []
    assert results[-1] == (False, "Wheel enable denied")


def test_gate_denial_blocks_reset_before_backend_call() -> None:
    actions, wheel, admin_action_gate, _logger, results = _build_actions()
    admin_action_gate.set_result("wheel.reset_position", False, "Reset Wheel Position requires the system to be idle")

    assert actions.resetPosition() is False

    assert wheel.reset_calls == 0
    assert results[-1] == (False, "Reset Wheel Position requires the system to be idle")


def test_backend_rejection_is_reported() -> None:
    actions, wheel, _gate, _logger, results = _build_actions(enabled_result=False)

    assert actions.setEnabled(True) is False

    assert wheel.enable_calls == [True]
    assert results[-1] == (False, "Wheel enable was rejected by the backend")


def test_missing_controller_is_reported() -> None:
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = WheelActions(
        wheel=None,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))

    assert actions.resetPosition() is False

    assert results[-1] == (False, "Reset wheel position is unavailable")
    assert logger.records[-1].message == "Reset wheel position is unavailable"

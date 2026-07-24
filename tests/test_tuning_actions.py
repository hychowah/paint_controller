"""Focused tests for the feature-root tuning action boundary."""

from __future__ import annotations

from paint_controller.models.tuning_actions import TuningActions
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self, short_result: bool = True, long_result: bool = True) -> None:
        self.short_result = short_result
        self.long_result = long_result
        self.short_calls: list[tuple[float, float, float]] = []
        self.long_calls: list[tuple[float, float, float]] = []

    def setShortParams(self, p_value: float, i_value: float, d_value: float) -> bool:
        self.short_calls.append((p_value, i_value, d_value))
        return self.short_result

    def setLongParams(self, p_value: float, i_value: float, d_value: float) -> bool:
        self.long_calls.append((p_value, i_value, d_value))
        return self.long_result


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
    short_result: bool = True,
    long_result: bool = True,
) -> tuple[TuningActions, FakeTeensy, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy(short_result=short_result, long_result=long_result)
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = TuningActions(
        teensy=teensy,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, teensy, admin_action_gate, logger, results


def test_short_yaw_pid_dispatches_to_backend() -> None:
    actions, teensy, admin_action_gate, logger, results = _build_actions()

    assert actions.setShortYawPid(1.0, 2.0, 3.0) is True

    assert teensy.short_calls == [(1.0, 2.0, 3.0)]
    assert admin_action_gate.calls == ["tuning.short_yaw_pid"]
    assert results[-1] == (True, "Short yaw PID requested")
    assert logger.records[-1].message == "Short yaw PID requested"


def test_long_yaw_pid_dispatches_to_backend() -> None:
    actions, teensy, admin_action_gate, logger, results = _build_actions()

    assert actions.setLongYawPid(4.0, 5.0, 6.0) is True

    assert teensy.long_calls == [(4.0, 5.0, 6.0)]
    assert admin_action_gate.calls == ["tuning.long_yaw_pid"]
    assert results[-1] == (True, "Long yaw PID requested")
    assert logger.records[-1].message == "Long yaw PID requested"


def test_gate_denial_blocks_short_pid_before_backend_call() -> None:
    actions, teensy, admin_action_gate, _logger, results = _build_actions()
    admin_action_gate.set_result("tuning.short_yaw_pid", False, "Short Yaw PID requires the system to be idle")

    assert actions.setShortYawPid(1.0, 2.0, 3.0) is False

    assert teensy.short_calls == []
    assert results[-1] == (False, "Short Yaw PID requires the system to be idle")


def test_gate_denial_blocks_long_pid_before_backend_call() -> None:
    actions, teensy, admin_action_gate, _logger, results = _build_actions()
    admin_action_gate.set_result("tuning.long_yaw_pid", False, "Long Yaw PID requires the system to be idle")

    assert actions.setLongYawPid(4.0, 5.0, 6.0) is False

    assert teensy.long_calls == []
    assert results[-1] == (False, "Long Yaw PID requires the system to be idle")


def test_backend_rejection_is_reported() -> None:
    actions, teensy, _gate, _logger, results = _build_actions(short_result=False)

    assert actions.setShortYawPid(1.0, 2.0, 3.0) is False

    assert teensy.short_calls == [(1.0, 2.0, 3.0)]
    assert results[-1] == (False, "Short yaw PID was rejected by the backend")


def test_missing_controller_is_reported() -> None:
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = TuningActions(
        teensy=None,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))

    assert actions.setShortYawPid(1.0, 2.0, 3.0) is False

    assert results[-1] == (False, "Short yaw PID is unavailable")
    assert logger.records[-1].message == "Short yaw PID is unavailable"

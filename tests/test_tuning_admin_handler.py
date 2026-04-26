"""Focused tests for the Python-owned tuning boundary."""

from __future__ import annotations

from paint_controller.handlers.tuning_admin import TuningAdminHandler
from tests.fakes import FakeLogger


class FakeTeensy:
    def __init__(self) -> None:
        self.short_calls: list[tuple[float, float, float]] = []
        self.long_calls: list[tuple[float, float, float]] = []

    def setShortParams(self, p_value: float, i_value: float, d_value: float) -> None:
        self.short_calls.append((p_value, i_value, d_value))

    def setLongParams(self, p_value: float, i_value: float, d_value: float) -> None:
        self.long_calls.append((p_value, i_value, d_value))


class FakeAdminActionGate:
    def __init__(self) -> None:
        self.results: dict[str, tuple[bool, str]] = {}
        self.calls: list[str] = []

    def set_result(self, action_key: str, allowed: bool, reason: str = "") -> None:
        self.results[action_key] = (allowed, reason)

    def check_action(self, action_key: str) -> tuple[bool, str]:
        self.calls.append(action_key)
        return self.results.get(action_key, (True, ""))


def _build_handler() -> tuple[TuningAdminHandler, FakeTeensy, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    teensy = FakeTeensy()
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    handler = TuningAdminHandler(
        teensy=teensy,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    handler.operation_result.connect(lambda success, message: results.append((success, message)))
    return handler, teensy, admin_action_gate, logger, results


def test_tuning_requests_dispatch_to_backend() -> None:
    handler, teensy, admin_action_gate, logger, results = _build_handler()

    assert handler.requestShortYawPid(1.0, 2.0, 3.0) is True
    assert handler.requestLongYawPid(4.0, 5.0, 6.0) is True

    assert teensy.short_calls == [(1.0, 2.0, 3.0)]
    assert teensy.long_calls == [(4.0, 5.0, 6.0)]
    assert admin_action_gate.calls == ["tuning.short_yaw_pid", "tuning.long_yaw_pid"]
    assert results[-1] == (True, "Long yaw PID requested")
    assert logger.records[-1].message == "Long yaw PID requested"


def test_tuning_gate_denial_blocks_backend_call() -> None:
    handler, teensy, admin_action_gate, logger, results = _build_handler()
    admin_action_gate.set_result("tuning.short_yaw_pid", False, "Short Yaw PID requires the system to be idle")

    assert handler.requestShortYawPid(1.0, 2.0, 3.0) is False

    assert teensy.short_calls == []
    assert results[-1] == (False, "Short Yaw PID requires the system to be idle")
    assert logger.records[-1].message == "Short Yaw PID requires the system to be idle"

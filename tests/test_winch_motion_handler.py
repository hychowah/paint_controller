"""Focused tests for the Python-owned winch motion boundary."""

from __future__ import annotations

from paint_controller.models.winch_actions import WinchActions
from tests.fakes import FakeLogger


class FakeWinch:
    def __init__(self, result: bool = True) -> None:
        self.result = result
        self.increment_calls: list[tuple[int, int]] = []
        self.absolute_calls: list[tuple[int, int]] = []

    def move_increment(self, length_mm: int, speed_mm_s: int) -> bool:
        self.increment_calls.append((length_mm, speed_mm_s))
        return self.result

    def move_absolute(self, length_mm: int, speed_mm_s: int) -> bool:
        self.absolute_calls.append((length_mm, speed_mm_s))
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


def _build_actions(result: bool = True) -> tuple[WinchActions, FakeWinch, FakeAdminActionGate, FakeLogger, list[tuple[bool, str]]]:
    winch = FakeWinch(result=result)
    admin_action_gate = FakeAdminActionGate()
    logger = FakeLogger()
    actions = WinchActions(
        winch=winch,
        admin_action_gate=admin_action_gate,
        logger=logger,
    )
    results: list[tuple[bool, str]] = []
    actions.operation_result.connect(lambda success, message: results.append((success, message)))
    return actions, winch, admin_action_gate, logger, results


def test_winch_motion_requests_dispatch_to_backend() -> None:
    actions, winch, admin_action_gate, logger, results = _build_actions()

    assert actions.moveIncrement(120, 450) is True
    assert actions.moveAbsolute(800, 500) is True
    assert actions.retractFull() is True
    assert actions.extendOneMeter() is True
    assert actions.emergencyStop() is True

    assert winch.increment_calls == [(120, 450), (1000, 500), (0, 0)]
    assert winch.absolute_calls == [(800, 500), (0, 500)]
    assert admin_action_gate.calls == [
        "winch.move_increment",
        "winch.move_absolute",
        "winch.retract_full",
        "winch.extend_one_meter",
        "winch.emergency_stop",
    ]
    assert results[-1] == (True, "Winch emergency stop requested")
    assert logger.records[-1].message == "Winch emergency stop requested"


def test_winch_motion_gate_denial_blocks_backend_call() -> None:
    actions, winch, admin_action_gate, logger, results = _build_actions()
    admin_action_gate.set_result("winch.move_absolute", False, "Winch Absolute Move requires the system to be idle")

    assert actions.moveAbsolute(500, 300) is False

    assert winch.absolute_calls == []
    assert results[-1] == (False, "Winch Absolute Move requires the system to be idle")
    assert logger.records[-1].message == "Winch Absolute Move requires the system to be idle"


def test_winch_motion_backend_rejection_is_reported() -> None:
    actions, winch, _gate, logger, results = _build_actions(result=False)

    assert actions.moveIncrement(120, 450) is False

    assert winch.increment_calls == [(120, 450)]
    assert results[-1] == (False, "Winch increment move was rejected by the backend")
    assert logger.records[-1].message == "Winch increment move was rejected by the backend"
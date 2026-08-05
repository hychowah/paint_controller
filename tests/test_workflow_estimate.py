"""Unit tests for the shared workflow duration estimate SOT."""

from __future__ import annotations

from paint_controller.services.workflow.document_compile import _estimate_duration_ms
from paint_controller.services.workflow.estimate import estimate_duration_ms, estimate_duration_s
from paint_controller.services.workflow.scheduler import ActionScheduler


class _Winch:
    def __init__(self, length: float) -> None:
        self._length = length

    def get_cable_length(self) -> float:
        return self._length


class _Hardware:
    def __init__(self, length: float = 0.0) -> None:
        self.winch = _Winch(length)


def test_estimate_winch_absolute_without_hardware() -> None:
    # |1000| / 100 = 10s
    seconds = estimate_duration_s(
        "winch_absolute",
        {"length": 1000, "speed": 100, "acceleration": 10},
    )
    assert abs(seconds - 10.0) < 1e-6
    assert abs(estimate_duration_ms("winch_absolute", {"length": 1000, "speed": 100}) - 10000.0) < 1e-3


def test_estimate_winch_uses_hardware_delta_when_available() -> None:
    hardware = _Hardware(length=200.0)
    # target 1000, current 200 → distance 800 / 100 = 8s
    seconds = estimate_duration_s(
        "winch_absolute",
        {"length": 1000, "speed": 100},
        hardware=hardware,
    )
    assert abs(seconds - 8.0) < 1e-6


def test_estimate_time_wait_and_valve_fixed() -> None:
    assert abs(estimate_duration_s("time_wait", {"duration_ms": 1500}) - 1.5) < 1e-6
    assert abs(estimate_duration_s("valve_turn", {"turn_value": 1.0}) - 0.5) < 1e-6


def test_explicit_estimated_duration_ms_wins() -> None:
    assert abs(estimate_duration_s("valve_turn", {"turn_value": 1.0}, explicit_estimated_duration_ms=900) - 0.9) < 1e-6


def test_compile_and_scheduler_share_estimate_path() -> None:
    params = {"length": 500, "speed": 50, "acceleration": 10}
    compile_ms = _estimate_duration_ms("winch_increment", params)
    assert compile_ms is not None
    # Scheduler without explicit stamp uses same SOT
    sched = ActionScheduler()
    actions = [
        {
            "id": "m",
            "type": "winch_increment",
            "params": params,
            "wait_for_completion": True,
        }
    ]
    built = sched.build_schedule(actions)
    assert len(built) == 1
    assert abs(built[0].estimated_duration - (compile_ms / 1000.0)) < 1e-6


def test_scheduler_honors_explicit_estimated_duration_ms() -> None:
    sched = ActionScheduler()
    built = sched.build_schedule(
        [
            {
                "id": "v",
                "type": "valve_turn",
                "params": {"turn_value": 1.0},
                "estimated_duration": 250,
                "wait_for_completion": True,
            }
        ]
    )
    assert abs(built[0].estimated_duration - 0.25) < 1e-6

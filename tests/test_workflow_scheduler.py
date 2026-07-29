"""Direct tests for the live workflow scheduler/action/hardware slice."""

from __future__ import annotations

from paint_controller.services.workflow.actions import ActionRegistry
from paint_controller.services.workflow.hardware import (
    ControllerNotAvailable,
    HardwareControllers,
)
from paint_controller.services.workflow.scheduler import ActionScheduler
from tests.fakes import FakeLogger


class StubValveController:
    def __init__(self) -> None:
        self.turn_values: list[float] = []

    def setValveTurn(self, value: float) -> None:
        self.turn_values.append(value)


class StubTeensyController:
    """Implements SupportsTeensyWorkflowBody (production pitch-angle name)."""

    def __init__(self) -> None:
        self.gimbal_calls: list[tuple[float, float]] = []
        self.arm_distances: list[int] = []
        self.force_calls: list[tuple[float, float]] = []

    def setSprayGunPitchAngle(self, angle: float, speed: float) -> None:
        self.gimbal_calls.append((angle, speed))

    def extendArm(self, distance: int) -> None:
        self.arm_distances.append(distance)

    def set_ef_force(self, fx: float, fy: float) -> None:
        self.force_calls.append((fx, fy))


class StubWinchController:
    def __init__(self, cable_length: float = 250.0) -> None:
        self._cable_length = cable_length
        self.increment_calls: list[tuple[int, int, int]] = []
        self.absolute_calls: list[tuple[int, int, int]] = []

    def move_increment_with_accel(self, length: int, speed: int, acceleration: int) -> None:
        self.increment_calls.append((length, speed, acceleration))

    def move_absolute_with_accel(self, length: int, speed: int, acceleration: int) -> None:
        self.absolute_calls.append((length, speed, acceleration))

    def get_cable_length(self) -> float:
        return self._cable_length


def _hardware(
    *,
    cable_length: float = 250.0,
) -> tuple[HardwareControllers, StubTeensyController, StubWinchController, StubValveController]:
    teensy = StubTeensyController()
    winch = StubWinchController(cable_length=cable_length)
    valve = StubValveController()
    return HardwareControllers.from_controllers(teensy, winch, valve), teensy, winch, valve


def test_hardware_from_controllers_routes_calls_to_underlying_controllers() -> None:
    hardware, teensy, winch, valve = _hardware()

    hardware.teensy.setValveTurn(12.5)
    hardware.teensy.setSprayGunPitchAngle(8, 2)
    hardware.teensy.extendArm(120)
    hardware.teensy.set_ef_force(1.5, -0.5)
    hardware.winch.move_increment_with_accel(50, 10, 20)
    hardware.winch.move_absolute_with_accel(400, 25, 15)

    assert valve.turn_values == [12.5]
    assert teensy.gimbal_calls == [(8.0, 2.0)]
    assert teensy.arm_distances == [120]
    assert teensy.force_calls == [(1.5, -0.5)]
    assert winch.increment_calls == [(50, 10, 20)]
    assert winch.absolute_calls == [(400, 25, 15)]


def test_hardware_adapter_raises_when_valve_controller_is_missing() -> None:
    hardware = HardwareControllers.from_controllers(StubTeensyController(), StubWinchController(), None)

    assert hardware.teensy is not None

    try:
        hardware.teensy.setValveTurn(5.0)
    except ControllerNotAvailable as exc:
        assert "ESP32 valve controller not available" in str(exc)
    else:
        raise AssertionError("expected ControllerNotAvailable")


def test_action_registry_registers_default_handlers_and_legacy_aliases() -> None:
    hardware, _, _, _ = _hardware()
    registry = ActionRegistry(hardware, logger=FakeLogger())

    for action_name in (
        "winch_increment",
        "winch_absolute",
        "winch_move_absolute",
        "valve_turn",
        "spray_gimbal",
        "arm_extend",
        "ef_force",
        "teensy_gimbal",
        "teensy_arm_extend",
    ):
        assert registry.has_handler(action_name) is True
        assert registry.get_handler(action_name) is not None


def test_winch_increment_handler_clamps_acceleration_before_dispatch() -> None:
    hardware, _, winch, _ = _hardware()
    registry = ActionRegistry(hardware, logger=FakeLogger())

    registry.get_handler("winch_increment").execute({"length": 80, "speed": 12, "acceleration": 999})

    assert winch.increment_calls == [(80, 12, 30)]


def test_scheduler_uses_current_winch_position_for_absolute_duration() -> None:
    hardware, _, _, _ = _hardware(cable_length=250.0)
    scheduler = ActionScheduler(logger=FakeLogger(), hardware=hardware)

    scheduled = scheduler.build_schedule(
        [
            {
                "id": "move_winch",
                "name": "Move Winch",
                "type": "winch_absolute",
                "params": {"length": 400, "speed": 50},
            }
        ]
    )

    assert len(scheduled) == 1
    assert scheduled[0].estimated_duration == 3.0
    assert scheduled[0].is_winch_action is True
    assert scheduled[0].winch_target_mm == 400


def test_scheduler_marks_reference_action_as_must_complete_for_position_trigger() -> None:
    hardware, _, _, _ = _hardware(cable_length=100.0)
    scheduler = ActionScheduler(logger=FakeLogger(), hardware=hardware)

    scheduled = scheduler.build_schedule(
        [
            {
                "id": "move_winch",
                "name": "Move Winch",
                "type": "winch_absolute",
                "params": {"length": 300, "speed": 50},
            },
            {
                "id": "open_valve",
                "name": "Open Valve",
                "type": "valve_turn",
                "params": {"turn_value": 25.0},
                "trigger": {
                    "timing_mode": "at_position",
                    "position_mm": 220,
                    "reference_action": "move_winch",
                },
            },
        ]
    )

    by_id = {action.action_id: action for action in scheduled}

    assert by_id["move_winch"].must_complete_before_workflow_end is True
    assert by_id["open_valve"].is_position_triggered is True
    assert by_id["open_valve"].scheduled_time == -1.0
    assert by_id["open_valve"].position_trigger_mm == 220
    assert by_id["open_valve"].position_reference_action == "move_winch"

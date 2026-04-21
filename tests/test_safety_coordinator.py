"""Tests for paint_controller.handlers.safety_coordinator.SafetyCoordinator."""

from paint_controller.handlers.safety_coordinator import SafetyCoordinator
from paint_controller.utils.constants import HeartbeatStatus
from tests.fakes import FakeEsp32Valve, FakeLogger, FakeStateStore, FakeTeensy, FakeWheel, FakeWinch


def test_halt_all_effectors_stops_all_outputs_and_sets_runtime_error(qt_core_app):
    state_store = FakeStateStore()
    coordinator = SafetyCoordinator(
        winch=FakeWinch(),
        teensy=FakeTeensy(),
        wheel=FakeWheel(),
        esp32_valve=FakeEsp32Valve(),
        state_store=state_store,
        logger=FakeLogger(),
    )

    coordinator.halt_all_effectors("test emergency")

    assert coordinator._winch.rpm_commands == [0]
    assert coordinator._teensy.trigger_values == [1000]
    assert coordinator._wheel.emergency_stop_calls == 1
    assert coordinator._esp32_valve.valve_turn_commands == [0.0]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.ERROR.value


def test_halt_all_effectors_continues_when_one_effector_raises(qt_core_app):
    class FailingWinch:
        def command_speed_rpm(self, value: float) -> None:
            raise RuntimeError("winch jam")

    logger = FakeLogger()
    state_store = FakeStateStore()
    coordinator = SafetyCoordinator(
        winch=FailingWinch(),
        teensy=FakeTeensy(),
        wheel=FakeWheel(),
        esp32_valve=FakeEsp32Valve(),
        state_store=state_store,
        logger=logger,
    )

    coordinator.halt_all_effectors("heartbeat loss", heartbeat_state=HeartbeatStatus.WARNING)

    assert coordinator._teensy.trigger_values == [1000]
    assert coordinator._wheel.emergency_stop_calls == 1
    assert coordinator._esp32_valve.valve_turn_commands == [0.0]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.WARNING.value
    assert any("winch jam" in record.message for record in logger.records if record.level == "error")


def test_clear_error_state_allows_runtime_state_reset(qt_core_app):
    state_store = FakeStateStore()
    state_store.controller_heartbeat_state = HeartbeatStatus.ERROR.value
    coordinator = SafetyCoordinator(state_store=state_store)

    coordinator.clear_error_state()

    assert state_store.controller_heartbeat_state == HeartbeatStatus.IDLE.value
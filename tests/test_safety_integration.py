"""Integration coverage for real safety-handler wiring."""

from __future__ import annotations

from unittest.mock import patch

from std_msgs.msg import UInt8

from paint_controller.handlers.heartbeat import UIHeartbeatHandler
from paint_controller.handlers.safety_coordinator import SafetyCoordinator
from paint_controller.utils.constants import HeartbeatStatus
from tests.fakes import FakeEsp32Valve, FakeNode, FakeStateStore, FakeTeensy, FakeWheel, FakeWinch


def _heartbeat_msg(value: int) -> UInt8:
    msg = UInt8()
    msg.data = value
    return msg


def test_base_heartbeat_loss_flows_through_real_safety_coordinator(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    winch = FakeWinch()
    teensy = FakeTeensy()
    wheel = FakeWheel()
    esp32_valve = FakeEsp32Valve()
    coordinator = SafetyCoordinator(
        winch=winch,
        teensy=teensy,
        wheel=wheel,
        esp32_valve=esp32_valve,
        state_store=state_store,
        logger=node.get_logger(),
    )
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)
    handler._availability_timer.stop()

    with patch("paint_controller.handlers.heartbeat.time.time", side_effect=[1.0, 1.0, 1.0]):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value

    handler._controller_last_seen = 1.8
    handler._base_last_seen = 0.0
    handler._ef_last_seen = 1.8

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=2.2):
        handler._check_availability()

    assert handler.controller_online is True
    assert handler.base_online is False
    assert handler.ef_online is True
    assert handler.status_message == "Base robot heartbeat lost"
    assert winch.rpm_commands == [0]
    assert teensy.trigger_values == [1000]
    assert wheel.emergency_stop_calls == 1
    assert esp32_valve.valve_turn_commands == [0.0]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.WARNING.value

    warning_messages = [record.message for record in node.logger.records if record.level == "warning"]
    assert "Base robot heartbeat lost" in warning_messages
    assert "Safety halt executed: Base robot heartbeat lost" in warning_messages
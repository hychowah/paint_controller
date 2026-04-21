"""Tests for paint_controller.handlers.heartbeat.UIHeartbeatHandler."""

from __future__ import annotations

from unittest.mock import patch

from std_msgs.msg import UInt8

from paint_controller.handlers.heartbeat import UIHeartbeatHandler
from paint_controller.utils.constants import HeartbeatStatus
from tests.fakes import FakeNode, FakeStateStore


class FakeSafetyCoordinator:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []
        self.clear_calls = 0

    def halt_all_effectors(self, reason: str, *, heartbeat_state=HeartbeatStatus.ERROR) -> None:
        self.calls.append((reason, int(heartbeat_state)))

    def clear_error_state(self) -> None:
        self.clear_calls += 1


def _heartbeat_msg(value: int) -> UInt8:
    msg = UInt8()
    msg.data = value
    return msg


def test_all_components_online_promotes_runtime_state_to_ontask(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    handler = UIHeartbeatHandler(node, state_store=state_store)

    with patch("paint_controller.handlers.heartbeat.time.time", side_effect=[1.0, 1.0, 1.0]):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value
    assert handler.controller_online is True
    assert handler.base_online is True
    assert handler.ef_online is True


def test_base_heartbeat_loss_halts_and_sets_warning(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)

    handler.set_controller_online(True)
    handler.set_base_online(True)
    handler.set_ef_online(True)
    handler._controller_last_seen = 1.5
    handler._base_last_seen = 0.0
    handler._ef_last_seen = 1.5

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=2.2):
        handler._check_availability()

    assert handler.base_online is False
    assert coordinator.calls == [("Base robot heartbeat lost", HeartbeatStatus.WARNING.value)]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.IDLE.value


def test_clear_error_state_publishes_and_resets_runtime_state(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    state_store.controller_heartbeat_state = HeartbeatStatus.ERROR.value
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)

    handler.clear_error_state()

    assert coordinator.clear_calls == 1
    assert handler.status_message == "Clearing errors..."
    assert node.publishers[0].published_messages[-1].data == HeartbeatStatus.CLEAR_ERROR.value
    assert node.publishers[1].published_messages[-1].__class__.__name__ == "Empty"
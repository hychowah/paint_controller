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


def test_ef_heartbeat_loss_halts_and_sets_warning(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)
    handler.cleanup()  # stop the real 200 ms availability timer

    handler.set_controller_online(True)
    handler.set_base_online(True)
    handler.set_ef_online(True)
    handler._controller_last_seen = 1.5
    handler._base_last_seen = 1.5
    handler._ef_last_seen = 0.0

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=2.2):
        handler._check_availability()

    assert handler.ef_online is False
    assert coordinator.calls == [("End effector heartbeat lost", HeartbeatStatus.WARNING.value)]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.IDLE.value


def test_controller_heartbeat_loss_halts_and_sets_warning(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)
    handler.cleanup()  # stop the real 200 ms availability timer

    handler.set_controller_online(True)
    handler.set_base_online(True)
    handler.set_ef_online(True)
    handler._controller_last_seen = 0.0
    handler._base_last_seen = 1.5
    handler._ef_last_seen = 1.5

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=2.2):
        handler._check_availability()

    assert handler.controller_online is False
    assert coordinator.calls == [("Controller heartbeat lost", HeartbeatStatus.WARNING.value)]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.IDLE.value


def test_base_heartbeat_recovery_promotes_runtime_state_to_ontask(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    handler = UIHeartbeatHandler(node, state_store=state_store)
    handler.cleanup()  # stop the real 200 ms availability timer

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.0):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value

    # Inject base loss: without a coordinator the handler drops the runtime
    # state to WARNING itself.
    handler._controller_last_seen = 200.0
    handler._base_last_seen = 0.0
    handler._ef_last_seen = 200.0

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=200.0):
        handler._check_availability()

    assert handler.base_online is False
    assert state_store.controller_heartbeat_state == HeartbeatStatus.WARNING.value

    # A fresh base heartbeat restores the component and, with all three
    # components online again, promotes the runtime state back to ONTASK.
    with patch("paint_controller.handlers.heartbeat.time.time", return_value=200.5):
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert handler.base_online is True
    assert "restored" in handler.status_message
    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value


def test_base_heartbeat_recovery_with_coordinator_leaves_state_store_untouched(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)
    handler.cleanup()  # stop the real 200 ms availability timer

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.0):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value

    # Inject base loss: with a coordinator the loss routes to
    # halt_all_effectors and the runtime state is left to the coordinator.
    handler._controller_last_seen = 200.0
    handler._base_last_seen = 0.0
    handler._ef_last_seen = 200.0

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=200.0):
        handler._check_availability()

    assert handler.base_online is False
    assert coordinator.calls == [("Base robot heartbeat lost", HeartbeatStatus.WARNING.value)]
    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value

    # Recovery restores the online flag and status message; the runtime
    # state stays owned by the coordinator and is not re-driven to WARNING.
    with patch("paint_controller.handlers.heartbeat.time.time", return_value=200.5):
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert handler.base_online is True
    assert "restored" in handler.status_message
    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value


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

def test_error_state_latches_and_clear_error_state_resets_without_coordinator(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    handler = UIHeartbeatHandler(node, state_store=state_store)
    handler.cleanup()  # stop the real 200 ms availability timer

    # Force ERROR via a controller error heartbeat.
    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.0):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.ERROR.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ERROR.value

    # Healthy heartbeats afterwards must not auto-downgrade the latched ERROR.
    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.5):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert handler.controller_online is True
    assert handler.base_online is True
    assert handler.ef_online is True
    assert state_store.controller_heartbeat_state == HeartbeatStatus.ERROR.value

    # Without a coordinator, clear_error_state resets the runtime state and
    # publishes CLEAR_ERROR on both topics.
    handler.clear_error_state()

    assert state_store.controller_heartbeat_state == HeartbeatStatus.IDLE.value
    assert handler.status_message == "Clearing errors..."
    assert node.publishers[0].published_messages[-1].data == HeartbeatStatus.CLEAR_ERROR.value
    assert node.publishers[1].published_messages[-1].__class__.__name__ == "Empty"


def test_error_state_latches_and_clear_error_state_delegates_with_coordinator(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)
    handler.cleanup()  # stop the real 200 ms availability timer

    # Force ERROR via a controller error heartbeat.
    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.0):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.ERROR.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ERROR.value

    # Healthy heartbeats afterwards must not auto-downgrade the latched ERROR.
    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.5):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ERROR.value

    # With a coordinator, clear_error_state delegates the reset and leaves
    # the runtime state untouched (still ERROR), while still publishing.
    handler.clear_error_state()

    assert coordinator.clear_calls == 1
    assert state_store.controller_heartbeat_state == HeartbeatStatus.ERROR.value
    assert node.publishers[0].published_messages[-1].data == HeartbeatStatus.CLEAR_ERROR.value
    assert node.publishers[1].published_messages[-1].__class__.__name__ == "Empty"


def test_base_heartbeat_flap_halts_once_per_loss_edge_and_recovers(qt_app):
    node = FakeNode()
    state_store = FakeStateStore()
    coordinator = FakeSafetyCoordinator()
    handler = UIHeartbeatHandler(node, state_store=state_store, safety_coordinator=coordinator)
    handler.cleanup()  # stop the real 200 ms availability timer

    with patch("paint_controller.handlers.heartbeat.time.time", return_value=100.0):
        handler._controller_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))
        handler._ef_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

    assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value

    for cycle in range(3):
        t = 200.0 + cycle * 10.0

        # Loss edge: base goes stale while controller/ef stay fresh.
        handler._controller_last_seen = t
        handler._base_last_seen = t - 5.0
        handler._ef_last_seen = t

        with patch("paint_controller.handlers.heartbeat.time.time", return_value=t):
            handler._check_availability()

        assert handler.base_online is False
        assert len(coordinator.calls) == cycle + 1

        # Online-guard: repeated availability checks while already offline
        # must not re-halt.
        with patch("paint_controller.handlers.heartbeat.time.time", return_value=t + 0.5):
            handler._check_availability()

        assert handler.base_online is False
        assert len(coordinator.calls) == cycle + 1

        # Restore edge: fresh heartbeat brings the component back and the
        # runtime state stays cleanly at ONTASK.
        with patch("paint_controller.handlers.heartbeat.time.time", return_value=t + 0.5):
            handler._base_heartbeat_callback(_heartbeat_msg(HeartbeatStatus.IDLE.value))

        assert handler.base_online is True
        assert "restored" in handler.status_message
        assert state_store.controller_heartbeat_state == HeartbeatStatus.ONTASK.value

    # Exactly one halt per loss edge across all three flap cycles.
    assert coordinator.calls == [("Base robot heartbeat lost", HeartbeatStatus.WARNING.value)] * 3

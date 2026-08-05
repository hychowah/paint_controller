"""Tests for paint_controller.core.ros_node.PaintRosNode."""

from __future__ import annotations

import importlib

from paint_controller.utils.constants import HeartbeatStatus


class FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def error(self, *args, **kwargs):
        pass


class FakePublisher:
    def __init__(self) -> None:
        self.published_messages = []

    def publish(self, message) -> None:
        self.published_messages.append(message)


class FakeNode:
    def __init__(self, *args, **kwargs) -> None:
        self.publishers = []
        self.timers = []
        self.destroyed_publishers = []
        self.destroyed_timers = []
        self.logger = FakeLogger()

    def create_publisher(self, msg_type, topic, qos):
        publisher = FakePublisher()
        self.publishers.append(publisher)
        return publisher

    def destroy_publisher(self, publisher) -> None:
        self.destroyed_publishers.append(publisher)

    def create_timer(self, interval, callback):
        timer = {"interval": interval, "callback": callback}
        self.timers.append(timer)
        return timer

    def destroy_timer(self, timer) -> None:
        self.destroyed_timers.append(timer)

    def get_logger(self):
        return self.logger


def _ros_node_module(monkeypatch):
    import rclpy.node

    import paint_controller.core.ros_node as ros_node_module

    monkeypatch.setattr(rclpy.node, "Node", FakeNode)
    return importlib.reload(ros_node_module)


class FakeStateStore:
    def __init__(self, heartbeat_state: int) -> None:
        self.controller_heartbeat_state = heartbeat_state


def test_publish_heartbeat_uses_state_store_value(monkeypatch):
    PaintRosNode = _ros_node_module(monkeypatch).PaintRosNode
    node = PaintRosNode(state_store=FakeStateStore(HeartbeatStatus.WARNING.value))

    node.publish_heartbeat()

    assert node.publishers[0].published_messages[-1].data == HeartbeatStatus.WARNING.value


def test_cleanup_is_idempotent_and_destroys_publisher_once(monkeypatch):
    PaintRosNode = _ros_node_module(monkeypatch).PaintRosNode
    node = PaintRosNode(state_store=FakeStateStore(HeartbeatStatus.IDLE.value))

    node.cleanup()
    node.cleanup()

    assert len(node.destroyed_publishers) == 1
    assert len(node.destroyed_timers) == 1


def test_ros_thread_pumps_command_bus_before_spin(monkeypatch, qt_core_app):
    """TD-054: RosThread drains the command bus on each loop and on exit."""
    import time

    import rclpy

    from paint_controller.core.ros_io import ImmediatePumpBus, RosCommandBus, TrafficKind

    # ImmediatePump would double-publish if used here; use deferred bus.
    bus = RosCommandBus()
    raw = FakePublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)
    handle.publish("cmd")

    mod = _ros_node_module(monkeypatch)
    node = mod.PaintRosNode(state_store=FakeStateStore(HeartbeatStatus.IDLE.value))
    thread = mod.RosThread(node, command_bus=bus)

    spin_calls = {"n": 0}

    def fake_spin_once(_node, timeout_sec=0.05):
        spin_calls["n"] += 1
        # After first spin iteration, bus should already have been pumped.
        if spin_calls["n"] == 1:
            assert raw.published_messages == ["cmd"]
        thread.request_shutdown()

    monkeypatch.setattr(rclpy, "ok", lambda: True)
    monkeypatch.setattr(rclpy, "spin_once", fake_spin_once)

    thread.start()
    assert thread.wait(2000)
    assert spin_calls["n"] >= 1
    assert raw.published_messages == ["cmd"]


def test_ros_thread_final_drain_delivers_oneshot_after_shutdown_request(monkeypatch, qt_core_app):
    """TD-054: final pump on exit must deliver oneshots enqueued late in the loop."""
    import rclpy

    from paint_controller.core.ros_io import RosCommandBus, TrafficKind

    bus = RosCommandBus()
    raw = FakePublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)

    mod = _ros_node_module(monkeypatch)
    node = mod.PaintRosNode(state_store=FakeStateStore(HeartbeatStatus.IDLE.value))
    thread = mod.RosThread(node, command_bus=bus)

    spin_calls = {"n": 0}

    def fake_spin_once(_node, timeout_sec=0.05):
        spin_calls["n"] += 1
        if spin_calls["n"] == 1:
            # Enqueue after first pump+spin iteration, then request shutdown.
            # Final drain after loop break must publish this oneshot.
            handle.publish("late_halt")
            thread.request_shutdown()

    monkeypatch.setattr(rclpy, "ok", lambda: True)
    monkeypatch.setattr(rclpy, "spin_once", fake_spin_once)

    thread.start()
    assert thread.wait(2000)
    assert spin_calls["n"] >= 1
    assert "late_halt" in raw.published_messages


def test_ros_thread_close_rejects_new_enqueues_but_final_pump_drains_pending(monkeypatch, qt_core_app):
    """close() drops new enqueues; pending traffic still drains on RosThread exit."""
    import rclpy

    from paint_controller.core.ros_io import RosCommandBus, TrafficKind

    bus = RosCommandBus()
    raw = FakePublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)
    handle.publish("pending_before_close")
    bus.close()
    handle.publish("after_close_dropped")

    mod = _ros_node_module(monkeypatch)
    node = mod.PaintRosNode(state_store=FakeStateStore(HeartbeatStatus.IDLE.value))
    thread = mod.RosThread(node, command_bus=bus)

    def fake_spin_once(_node, timeout_sec=0.05):
        thread.request_shutdown()

    monkeypatch.setattr(rclpy, "ok", lambda: True)
    monkeypatch.setattr(rclpy, "spin_once", fake_spin_once)

    thread.start()
    assert thread.wait(2000)
    assert raw.published_messages == ["pending_before_close"]
    assert "after_close_dropped" not in raw.published_messages

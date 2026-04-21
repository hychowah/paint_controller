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
        self.destroyed_publishers = []
        self.logger = FakeLogger()

    def create_publisher(self, msg_type, topic, qos):
        publisher = FakePublisher()
        self.publishers.append(publisher)
        return publisher

    def destroy_publisher(self, publisher) -> None:
        self.destroyed_publishers.append(publisher)

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
"""ROS pub/sub integration tests for paint_controller.controllers.winch."""

from __future__ import annotations

import importlib
import time
import uuid

import pytest

rclpy = pytest.importorskip("rclpy")
from rclpy.node import Node
from std_msgs.msg import Float64


def _winch_controller_class():
    return importlib.import_module("paint_controller.controllers.winch").WinchController


@pytest.fixture
def ros_context():
    if not rclpy.ok():
        rclpy.init()
    yield
    if rclpy.ok():
        rclpy.shutdown()


def test_speed_command_reaches_real_ros_subscriber(qt_app, ros_context):
    controller_node = Node(f"winch_controller_test_pub_{uuid.uuid4().hex}")
    subscriber_node = Node(f"winch_controller_test_sub_{uuid.uuid4().hex}")
    controller = _winch_controller_class()(controller_node)
    controller.set_available(True)
    received = []

    subscription = subscriber_node.create_subscription(
        Float64,
        "winch/move/speed/mmps/cmd",
        lambda message: received.append(message.data),
        10,
    )

    try:
        assert controller.command_speed_mmps(125.0) is True

        deadline = time.monotonic() + 1.0
        while not received and time.monotonic() < deadline:
            rclpy.spin_once(controller_node, timeout_sec=0.05)
            rclpy.spin_once(subscriber_node, timeout_sec=0.05)

        assert received == [125.0]
    finally:
        controller._availability_timer.stop()
        controller.deleteLater()
        subscriber_node.destroy_subscription(subscription)
        controller_node.destroy_node()
        subscriber_node.destroy_node()

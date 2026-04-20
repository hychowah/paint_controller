"""Harness validation tests for shared fake ROS/Qt test primitives."""

import py_compile
import sys
from pathlib import Path

from tests.fakes import FakeNode, FakeRosBus


def test_package_init_has_no_syntax_errors() -> None:
    """Catch SyntaxError in __init__.py (conftest stubs bypass real import)."""
    init_path = Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "__init__.py"
    py_compile.compile(str(init_path), doraise=True)


def test_fake_node_tracks_publishers_subscriptions_and_timers() -> None:
    node = FakeNode()

    publisher = node.create_publisher(int, "/topic", 10)
    subscription = node.create_subscription(int, "/topic", lambda _msg: None, 10)

    triggered = []
    timer = node.create_timer(0.1, lambda: triggered.append(True))
    timer.trigger()

    publisher.publish(123)

    assert publisher.published_messages == [123]
    assert subscription.topic == "/topic"
    assert triggered == [True]

    node.destroy_publisher(publisher)
    node.destroy_subscription(subscription)
    node.destroy_timer(timer)

    assert publisher in node.destroyed_publishers
    assert subscription in node.destroyed_subscriptions
    assert timer in node.destroyed_timers
    assert timer.cancelled is True


def test_fake_ros_bus_delivers_messages_between_nodes() -> None:
    bus = FakeRosBus()
    publisher_node = FakeNode(bus=bus)
    subscriber_node = FakeNode(bus=bus)
    received = []

    publisher = publisher_node.create_publisher(int, "/topic", 10)
    subscriber_node.create_subscription(int, "/topic", received.append, 10)

    publisher.publish(123)

    assert received == [123]


def test_stub_modules_expose_expected_attributes() -> None:
    """Verify that conftest stub modules still match the production interface.

    When production code adds a new message type or rclpy submodule, this test
    will fail immediately rather than letting the real module silently load and
    produce confusing errors later.
    """
    # rclpy stub
    import rclpy.node as rclpy_node
    assert hasattr(rclpy_node, "Node"), "rclpy.node.Node missing from stub"

    # std_msgs stub
    import std_msgs.msg as std_msgs_msg
    assert hasattr(std_msgs_msg, "Float64"), "std_msgs.msg.Float64 missing from stub"
    assert hasattr(std_msgs_msg, "Bool"), "std_msgs.msg.Bool missing from stub"
    f = std_msgs_msg.Float64()
    assert hasattr(f, "data"), "std_msgs.msg.Float64 must have .data field"

    # paint_interfaces stub
    import paint_interfaces.msg as paint_interfaces_msg
    assert hasattr(paint_interfaces_msg, "WinchStatus"), "paint_interfaces.msg.WinchStatus missing"
    assert hasattr(paint_interfaces_msg, "MoveWinchLength"), "paint_interfaces.msg.MoveWinchLength missing"
    ws = paint_interfaces_msg.WinchStatus()
    for field in ("enabled", "cable_length", "cable_speed", "motor_brake"):
        assert hasattr(ws, field), f"WinchStatus must have .{field} field"
    ml = paint_interfaces_msg.MoveWinchLength()
    for field in ("length_mm", "speed_mm_s", "acceleration_rpm_s"):
        assert hasattr(ml, field), f"MoveWinchLength must have .{field} field"


def test_fake_publisher_rejects_wrong_message_type() -> None:
    """FakePublisher must raise AssertionError for type-mismatched messages.

    This mirrors real DDS middleware which rejects type mismatches at the
    serialisation boundary.  Catching the assertion in tests reveals production
    bugs where the wrong message type is published on a topic.
    """
    import pytest

    node = FakeNode()

    class MsgA:
        pass

    class MsgB:
        pass

    publisher = node.create_publisher(MsgA, "/typed_topic", 10)
    publisher.publish(MsgA())  # correct type — must succeed

    with pytest.raises(AssertionError, match="FakePublisher"):
        publisher.publish(MsgB())  # wrong type — must fail


def test_fake_ros_bus_delivers_copy_not_reference() -> None:
    """FakeRosBus must deliver a copy of each message, not the original object.

    Real DDS serialises/deserialises messages so publisher and subscriber get
    independent objects.  Sharing a reference allows subscriber mutations to
    appear to affect the publisher's copy, which hides production bugs.
    """
    bus = FakeRosBus()
    publisher_node = FakeNode(bus=bus)
    subscriber_node = FakeNode(bus=bus)

    received = []
    publisher_node.create_publisher(object, "/copy_topic", 10)
    subscriber_node.create_subscription(object, "/copy_topic", received.append, 10)

    original = object.__new__(object)
    # Bypass FakePublisher type check by publishing via bus directly
    bus.publish("/copy_topic", original)

    assert len(received) == 1
    assert received[0] is not original, "FakeRosBus must deliver a copy, not the original object"
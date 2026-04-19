"""Harness validation tests for shared fake ROS/Qt test primitives."""

from tests.fakes import FakeNode, FakeRosBus


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
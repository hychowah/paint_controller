"""Reusable test doubles for ROS-like interfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List


@dataclass
class FakeLogRecord:
    level: str
    message: str


@dataclass
class FakeLogger:
    records: List[FakeLogRecord] = field(default_factory=list)

    def debug(self, message: str) -> None:
        self.records.append(FakeLogRecord("debug", message))

    def info(self, message: str) -> None:
        self.records.append(FakeLogRecord("info", message))

    def warning(self, message: str) -> None:
        self.records.append(FakeLogRecord("warning", message))

    def error(self, message: str) -> None:
        self.records.append(FakeLogRecord("error", message))


@dataclass
class FakePublisher:
    msg_type: Any
    topic: str
    qos: int
    bus: "FakeRosBus | None" = None
    published_messages: List[Any] = field(default_factory=list)

    def publish(self, message: Any) -> None:
        self.published_messages.append(message)
        if self.bus is not None:
            self.bus.publish(self.topic, message)


@dataclass
class FakeSubscription:
    msg_type: Any
    topic: str
    callback: Callable[[Any], None]
    qos: int


@dataclass
class FakeRosBus:
    subscriptions_by_topic: dict[str, List[FakeSubscription]] = field(default_factory=dict)

    def register_subscription(self, subscription: FakeSubscription) -> None:
        self.subscriptions_by_topic.setdefault(subscription.topic, []).append(subscription)

    def unregister_subscription(self, subscription: FakeSubscription) -> None:
        subscriptions = self.subscriptions_by_topic.get(subscription.topic)
        if subscriptions is None:
            return
        if subscription in subscriptions:
            subscriptions.remove(subscription)
        if not subscriptions:
            del self.subscriptions_by_topic[subscription.topic]

    def publish(self, topic: str, message: Any) -> None:
        for subscription in list(self.subscriptions_by_topic.get(topic, [])):
            subscription.callback(message)


@dataclass
class FakeTimer:
    interval_sec: float
    callback: Callable[[], None]
    cancelled: bool = False

    def trigger(self) -> None:
        if not self.cancelled:
            self.callback()

    def cancel(self) -> None:
        self.cancelled = True


class FakeNode:
    """Small ROS-node-like test double for controller tests."""

    def __init__(self, bus: FakeRosBus | None = None) -> None:
        self.bus = bus
        self.logger = FakeLogger()
        self.publishers: List[FakePublisher] = []
        self.subscriptions: List[FakeSubscription] = []
        self.timers: List[FakeTimer] = []
        self.destroyed_publishers: List[FakePublisher] = []
        self.destroyed_subscriptions: List[FakeSubscription] = []
        self.destroyed_timers: List[FakeTimer] = []

    def get_logger(self) -> FakeLogger:
        return self.logger

    def create_publisher(self, msg_type: Any, topic: str, qos: int) -> FakePublisher:
        publisher = FakePublisher(msg_type=msg_type, topic=topic, qos=qos, bus=self.bus)
        self.publishers.append(publisher)
        return publisher

    def create_subscription(
        self,
        msg_type: Any,
        topic: str,
        callback: Callable[[Any], None],
        qos: int,
    ) -> FakeSubscription:
        subscription = FakeSubscription(
            msg_type=msg_type,
            topic=topic,
            callback=callback,
            qos=qos,
        )
        self.subscriptions.append(subscription)
        if self.bus is not None:
            self.bus.register_subscription(subscription)
        return subscription

    def create_timer(self, interval_sec: float, callback: Callable[[], None]) -> FakeTimer:
        timer = FakeTimer(interval_sec=interval_sec, callback=callback)
        self.timers.append(timer)
        return timer

    def destroy_publisher(self, publisher: FakePublisher) -> None:
        self.destroyed_publishers.append(publisher)
        if publisher in self.publishers:
            self.publishers.remove(publisher)

    def destroy_subscription(self, subscription: FakeSubscription) -> None:
        self.destroyed_subscriptions.append(subscription)
        if self.bus is not None:
            self.bus.unregister_subscription(subscription)
        if subscription in self.subscriptions:
            self.subscriptions.remove(subscription)

    def destroy_timer(self, timer: FakeTimer) -> None:
        timer.cancel()
        self.destroyed_timers.append(timer)
        if timer in self.timers:
            self.timers.remove(timer)
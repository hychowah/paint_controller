"""Unit tests for RosCommandBus (TD-054 Option A2)."""

from __future__ import annotations

import threading

from paint_controller.core.ros_io import ImmediatePumpBus, RosCommandBus, TrafficKind


class SpyPublisher:
    def __init__(self) -> None:
        self.messages: list[object] = []

    def publish(self, message: object) -> None:
        self.messages.append(message)


def test_only_pump_calls_raw_publish() -> None:
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)

    handle.publish("a")
    assert raw.messages == []
    assert bus.pending_counts() == (1, 0)

    assert bus.pump() == 1
    assert raw.messages == ["a"]
    assert bus.pending_counts() == (0, 0)


def test_continuous_last_wins() -> None:
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.CONTINUOUS)

    handle.publish("v1")
    handle.publish("v2")
    handle.publish("v3")
    assert bus.pending_counts() == (0, 1)

    assert bus.pump() == 1
    assert raw.messages == ["v3"]


def test_oneshot_fifo_then_continuous() -> None:
    bus = RosCommandBus()
    raw_stop = SpyPublisher()
    raw_motion = SpyPublisher()
    stop = bus.bind(raw_stop, kind=TrafficKind.ONESHOT)
    motion = bus.bind(raw_motion, kind=TrafficKind.CONTINUOUS)

    motion.publish("stale")
    stop.publish("halt")
    motion.publish("latest")

    assert bus.pump() == 2
    assert raw_stop.messages == ["halt"]
    assert raw_motion.messages == ["latest"]


def test_invalidate_continuous_drops_pending_motion() -> None:
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.CONTINUOUS)
    handle.publish("motion")

    cleared = bus.invalidate_continuous()
    assert cleared == 1
    assert bus.pump() == 0
    assert raw.messages == []


def test_invalidate_does_not_drop_oneshots() -> None:
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)
    handle.publish("stop")

    assert bus.invalidate_continuous() == 0
    assert bus.pump() == 1
    assert raw.messages == ["stop"]


def test_close_drops_new_enqueues_but_pump_drains_pending() -> None:
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)
    handle.publish("before_close")
    bus.close()
    handle.publish("after_close")

    assert bus.closed
    assert bus.pump() == 1
    assert raw.messages == ["before_close"]


def test_immediate_pump_bus_for_unit_tests() -> None:
    bus = ImmediatePumpBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.CONTINUOUS)
    handle.publish("sync")
    assert raw.messages == ["sync"]


def test_enqueue_from_multiple_threads() -> None:
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.ONESHOT)
    errors: list[BaseException] = []

    def worker(n: int) -> None:
        try:
            for i in range(20):
                handle.publish((n, i))
        except BaseException as exc:  # noqa: BLE001 — collect for assert
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    count = bus.pump()
    assert count == 80
    assert len(raw.messages) == 80


def test_separate_continuous_handles_are_independent_slots() -> None:
    bus = RosCommandBus()
    left_raw = SpyPublisher()
    right_raw = SpyPublisher()
    left = bus.bind(left_raw, kind=TrafficKind.CONTINUOUS)
    right = bus.bind(right_raw, kind=TrafficKind.CONTINUOUS)

    left.publish(1)
    right.publish(2)
    left.publish(3)

    assert bus.pump() == 2
    assert left_raw.messages == [3]
    assert right_raw.messages == [2]

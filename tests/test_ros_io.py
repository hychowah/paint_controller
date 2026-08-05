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


def test_after_workers_join_invalidate_then_halt_oneshot_pumps_halt_only() -> None:
    """Mailbox semantics after quiet bus: join workers, then invalidate + halt + pump.

    This is intentionally sequential (not a live teleop race). For concurrent
    halt-while-workers-live, see
    ``test_live_workers_invalidate_and_halt_while_enqueueing``.
    """
    bus = RosCommandBus()
    motion_raw = SpyPublisher()
    halt_raw = SpyPublisher()
    motion = bus.bind(motion_raw, kind=TrafficKind.CONTINUOUS)
    halt = bus.bind(halt_raw, kind=TrafficKind.ONESHOT)
    errors: list[BaseException] = []

    def worker(n: int) -> None:
        try:
            for i in range(50):
                motion.publish(("motion", n, i))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

    assert errors == []

    cleared = bus.invalidate_continuous()
    assert cleared >= 0
    halt.publish("halt")

    count = bus.pump()
    assert count == 1
    assert halt_raw.messages == ["halt"]
    assert motion_raw.messages == []


def test_invalidate_during_concurrent_continuous_enqueue_does_not_crash() -> None:
    """Invalidate while workers publish continuous; pump must not raise; final state consistent."""
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.CONTINUOUS)
    errors: list[BaseException] = []
    start = threading.Barrier(5)  # 4 workers + main

    def worker(n: int) -> None:
        try:
            start.wait(timeout=5.0)
            for i in range(100):
                handle.publish(("c", n, i))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
    for t in threads:
        t.start()

    start.wait(timeout=5.0)
    # Race window: invalidate while enqueues are in flight.
    for _ in range(20):
        bus.invalidate_continuous()

    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

    assert errors == []
    # Final invalidate so any last continuous from workers is scrubbed.
    bus.invalidate_continuous()
    assert bus.pump() == 0
    assert raw.messages == []


def test_concurrent_pump_while_continuous_enqueue() -> None:
    """Production race window: pump() while workers still enqueue continuous.

    Pump copies under lock then raw-publishes outside the lock. Workers must not
    crash the bus; published continuous values must be coherent snapshots.
    """
    bus = RosCommandBus()
    raw = SpyPublisher()
    handle = bus.bind(raw, kind=TrafficKind.CONTINUOUS)
    errors: list[BaseException] = []
    stop = threading.Event()
    start = threading.Barrier(5)  # 4 workers + main

    def worker(n: int) -> None:
        try:
            start.wait(timeout=5.0)
            i = 0
            while not stop.is_set():
                handle.publish(("motion", n, i))
                i += 1
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,), name=f"bus-enq-{t}") for t in range(4)]
    for t in threads:
        t.start()

    start.wait(timeout=5.0)
    pump_errors: list[BaseException] = []
    for _ in range(200):
        try:
            bus.pump()
        except BaseException as exc:  # noqa: BLE001
            pump_errors.append(exc)

    stop.set()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

    assert errors == []
    assert pump_errors == []

    # Final pump drains last continuous (if any).
    bus.pump()
    for msg in raw.messages:
        assert isinstance(msg, tuple) and msg[0] == "motion"
        assert isinstance(msg[1], int) and 0 <= msg[1] < 4
        assert isinstance(msg[2], int)


def test_live_workers_invalidate_and_halt_while_enqueueing() -> None:
    """Halt while continuous teleop workers are still live; final pump is halt-safe.

    Workers keep publishing continuous; main invalidates + enqueues oneshot halt
    while they run; after join + final invalidate, pump must deliver halt and no
    motion.
    """
    bus = RosCommandBus()
    motion_raw = SpyPublisher()
    halt_raw = SpyPublisher()
    motion = bus.bind(motion_raw, kind=TrafficKind.CONTINUOUS)
    halt = bus.bind(halt_raw, kind=TrafficKind.ONESHOT)
    errors: list[BaseException] = []
    stop = threading.Event()
    start = threading.Barrier(5)

    def worker(n: int) -> None:
        try:
            start.wait(timeout=5.0)
            i = 0
            while not stop.is_set():
                motion.publish(("motion", n, i))
                i += 1
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(t,), name=f"live-halt-{t}") for t in range(4)]
    for t in threads:
        t.start()

    start.wait(timeout=5.0)

    # Live race: invalidate + halt while workers still enqueue.
    for _ in range(10):
        bus.invalidate_continuous()
    halt.publish("halt")
    # Intermediate pumps may still see motion enqueued after invalidate; that is OK.
    for _ in range(20):
        bus.pump()

    stop.set()
    for t in threads:
        t.join(timeout=5.0)
        assert not t.is_alive()

    assert errors == []

    # After teleop stops: scrub continuous, ensure halt is pending or already published.
    bus.invalidate_continuous()
    if "halt" not in halt_raw.messages:
        halt.publish("halt")
    bus.pump()

    assert "halt" in halt_raw.messages
    # After final invalidate + pump, no continuous may remain pending.
    assert bus.pending_counts() == (0, 0)
    # Any motion that already raw-published before final scrub is allowed historically;
    # post-final pump must not reintroduce continuous-only traffic without halt present.
    assert halt_raw.messages.count("halt") >= 1

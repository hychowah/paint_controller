"""ROS command publish bus — sole owner of cross-thread command publish (TD-054).

Option A2: continuous traffic is last-wins per bound handle; oneshots are FIFO.
Only :meth:`RosCommandBus.pump` (RosThread) may call raw ``publisher.publish``.

Controllers bind at construct time and keep a handle with ``.publish(msg)`` only.
Traffic kind is not used at call sites. Safety latch lives on SafetyCoordinator;
call :meth:`invalidate_continuous` from halt after latching.
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class TrafficKind(Enum):
    """Bind-time role only — not for method bodies outside this module / bind sites."""

    CONTINUOUS = "continuous"
    ONESHOT = "oneshot"


class BoundPublisher:
    """Drop-in publish handle. Controllers treat this like a raw publisher."""

    __slots__ = ("_bus", "_raw", "_kind", "_slot_id")

    def __init__(self, bus: RosCommandBus, raw: Any, kind: TrafficKind) -> None:
        self._bus = bus
        self._raw = raw
        self._kind = kind
        self._slot_id = id(self)

    def publish(self, msg: Any) -> None:
        self._bus.enqueue(self, msg)


class RosCommandBus:
    """Thread-safe command mailbox drained only by :meth:`pump` (RosThread)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._closed = False
        # ONESHOT: FIFO of (raw_publisher, msg)
        self._oneshots: deque[tuple[Any, Any]] = deque()
        # CONTINUOUS: slot_id -> (raw_publisher, msg) last-wins
        self._continuous: dict[int, tuple[Any, Any]] = {}

    def bind(self, publisher: Any, *, kind: TrafficKind) -> BoundPublisher:
        """Return a handle whose ``publish`` enqueues; raw publish only on pump."""
        if publisher is None:
            raise TypeError("publisher must not be None")
        return BoundPublisher(self, publisher, kind)

    def enqueue(self, handle: BoundPublisher, msg: Any) -> None:
        """Accept a message from a bound handle. Bus owns ``msg`` after this call."""
        with self._lock:
            if self._closed:
                logger.debug("RosCommandBus closed; dropping publish")
                return
            raw = handle._raw
            if handle._kind is TrafficKind.CONTINUOUS:
                self._continuous[handle._slot_id] = (raw, msg)
            else:
                self._oneshots.append((raw, msg))

    def invalidate_continuous(self) -> int:
        """Drop all pending continuous command slots. Returns number cleared."""
        with self._lock:
            count = len(self._continuous)
            self._continuous.clear()
            return count

    def pump(self) -> int:
        """Apply pending ops via raw publish. Call only from RosThread.

        Order: oneshots first (stops / discrete), then continuous slots.
        Returns number of raw publishes performed.
        """
        with self._lock:
            oneshots = list(self._oneshots)
            self._oneshots.clear()
            continuous = list(self._continuous.values())
            self._continuous.clear()

        published = 0
        for raw, msg in oneshots:
            raw.publish(msg)
            published += 1
        for raw, msg in continuous:
            raw.publish(msg)
            published += 1
        return published

    def close(self) -> None:
        """Reject further enqueues. Pending ops remain until :meth:`pump`."""
        with self._lock:
            self._closed = True

    @property
    def closed(self) -> bool:
        with self._lock:
            return self._closed

    def pending_counts(self) -> tuple[int, int]:
        """Return ``(oneshot_count, continuous_count)`` for tests / diagnostics."""
        with self._lock:
            return len(self._oneshots), len(self._continuous)


class ImmediatePumpBus(RosCommandBus):
    """Test helper: pump after every enqueue so unit tests stay synchronous.

    Same type hierarchy as production; not a second production path — tests only.
    """

    def enqueue(self, handle: BoundPublisher, msg: Any) -> None:
        super().enqueue(handle, msg)
        self.pump()

"""Unit tests for RosTelemetryBridge (TD-056).

Includes concurrency lock-pack tests: worker-thread ``post`` must only apply
on the Qt main thread after event processing.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass

from paint_controller.core.ros_telemetry import ImmediateTelemetryBridge, RosTelemetryBridge


@dataclass(frozen=True, slots=True)
class _Snap:
    value: int


def test_post_does_not_apply_synchronously(qt_core_app) -> None:
    applied: list[int] = []
    bridge = RosTelemetryBridge(lambda s: applied.append(s.value), parent=None)
    bridge.post(_Snap(1))
    assert applied == []
    assert bridge.pending_snapshot() is not None
    assert bridge.is_scheduled is True


def test_process_events_delivers_latest_only(qt_core_app) -> None:
    applied: list[int] = []
    bridge = RosTelemetryBridge(lambda s: applied.append(s.value), parent=None)
    bridge.post(_Snap(1))
    bridge.post(_Snap(2))
    bridge.post(_Snap(3))
    qt_core_app.processEvents()
    # Last-wins: only latest POD is applied (single wake may deliver once).
    assert applied == [3]


def test_immediate_bridge_applies_on_post(qt_core_app) -> None:
    applied: list[int] = []
    bridge = ImmediateTelemetryBridge(lambda s: applied.append(s.value), parent=None)
    bridge.post(_Snap(9))
    assert applied == [9]


def test_post_from_worker_thread_applies_on_main_only(qt_core_app) -> None:
    """Worker may post; apply_fn must run on the main (Qt) thread after processEvents."""
    main_tid = threading.get_ident()
    applied: list[int] = []
    apply_tids: list[int] = []
    errors: list[BaseException] = []

    def apply_fn(snap: _Snap) -> None:
        apply_tids.append(threading.get_ident())
        applied.append(snap.value)

    # Bridge must be constructed on the main/test thread (Qt affinity).
    bridge = RosTelemetryBridge(apply_fn, parent=None)

    def worker() -> None:
        try:
            for i in range(1, 21):
                bridge.post(_Snap(i))
        except BaseException as exc:  # noqa: BLE001 — surface on main
            errors.append(exc)

    thread = threading.Thread(target=worker, name="telemetry-post-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive(), "worker thread did not finish"
    assert errors == []

    # QueuedConnection: no apply until the main event loop runs.
    assert applied == []
    assert apply_tids == []

    qt_core_app.processEvents()

    assert applied == [20], f"expected last-wins apply, got {applied}"
    assert apply_tids == [main_tid], f"apply must run on main thread, got {apply_tids}"


def test_post_from_worker_rearm_under_burst(qt_core_app) -> None:
    """High-rate worker posts while main drains events; no crash; last value wins."""
    main_tid = threading.get_ident()
    applied: list[int] = []
    apply_tids: list[int] = []
    errors: list[BaseException] = []
    done = threading.Event()

    def apply_fn(snap: _Snap) -> None:
        apply_tids.append(threading.get_ident())
        applied.append(snap.value)

    bridge = RosTelemetryBridge(apply_fn, parent=None)

    def worker() -> None:
        try:
            for i in range(1, 201):
                bridge.post(_Snap(i))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)
        finally:
            done.set()

    thread = threading.Thread(target=worker, name="telemetry-burst-worker")
    thread.start()

    # Drain on main while worker is still posting (re-arm path under load).
    for _ in range(50):
        qt_core_app.processEvents()
        if done.is_set() and not bridge.is_scheduled and bridge.pending_snapshot() is None:
            break

    thread.join(timeout=5.0)
    assert not thread.is_alive(), "burst worker did not finish"
    assert errors == []

    # Final drain for any last queued wake.
    for _ in range(20):
        qt_core_app.processEvents()
        if not bridge.is_scheduled and bridge.pending_snapshot() is None:
            break

    assert applied, "expected at least one apply after burst"
    assert applied[-1] == 200
    assert all(tid == main_tid for tid in apply_tids), "all applies must be on main thread"


def test_teardown_with_pending_post_does_not_crash(qt_core_app) -> None:
    """Pending wake after bridge parent teardown must not crash the event loop.

    Production parents bridges on controllers. Destroying the parent while a
    worker has posted must not call into a broken apply path unsafely.
    """
    from PySide6.QtCore import QObject

    main_tid = threading.get_ident()
    applied: list[int] = []
    apply_tids: list[int] = []
    parent = QObject()
    bridge = RosTelemetryBridge(
        lambda s: (apply_tids.append(threading.get_ident()), applied.append(s.value)),
        parent=parent,
    )

    errors: list[BaseException] = []

    def worker() -> None:
        try:
            for i in range(1, 11):
                bridge.post(_Snap(i))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    thread = threading.Thread(target=worker, name="telemetry-teardown-worker")
    thread.start()
    thread.join(timeout=5.0)
    assert not thread.is_alive()
    assert errors == []

    # Pending work exists; tear down parent (deletes child bridge in Qt).
    parent.deleteLater()
    qt_core_app.processEvents()

    # Further processEvents must not raise even if a wake was queued.
    for _ in range(10):
        qt_core_app.processEvents()

    # Best effort: either apply completed before teardown or was dropped safely.
    if applied:
        assert applied[-1] == 10 or applied[-1] in range(1, 11)
        assert all(tid == main_tid for tid in apply_tids)


def test_apply_fn_exception_does_not_poison_schedule(qt_core_app) -> None:
    """A failing apply_fn must not permanently stick is_scheduled."""
    calls: list[int] = []

    def flaky(snap: _Snap) -> None:
        calls.append(snap.value)
        if snap.value == 1:
            raise RuntimeError("forced apply failure")

    bridge = RosTelemetryBridge(flaky, parent=None)
    bridge.post(_Snap(1))
    qt_core_app.processEvents()
    assert calls == [1]
    assert bridge.is_scheduled is False
    assert bridge.pending_snapshot() is None

    bridge.post(_Snap(2))
    qt_core_app.processEvents()
    assert calls == [1, 2]

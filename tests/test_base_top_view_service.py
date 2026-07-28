"""Regression tests for BaseTopViewService shutdown cleanup and TD-039 map ownership."""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from paint_controller.services.base_top_view_service import BaseTopViewService
from paint_controller.services.video_stream import CameraType


class _FakeBaseTopStream(QObject):
    frameReady = Signal(object, object)


class _FakeVideoStreamHandler(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.camera_streams = {CameraType.BASE_TOP: _FakeBaseTopStream()}


class _TrackedSignal:
    def __init__(self) -> None:
        self.slots: list[object] = []
        self.connect_calls: list[object] = []
        self.disconnect_calls: list[object] = []

    def connect(self, slot: object) -> None:
        self.slots.append(slot)
        self.connect_calls.append(slot)

    def disconnect(self, slot: object) -> None:
        if slot in self.slots:
            self.slots.remove(slot)
        self.disconnect_calls.append(slot)


class _FakeBaseTopStreamTracked:
    def __init__(self) -> None:
        self.frameReady = _TrackedSignal()


class _FakeVideoStreamHandlerTracked:
    def __init__(self) -> None:
        self.camera_streams = {CameraType.BASE_TOP: _FakeBaseTopStreamTracked()}


def test_cleanup_quits_worker_thread(qt_app) -> None:
    handler = _FakeVideoStreamHandler()
    service = BaseTopViewService(video_handler=handler)

    assert service.worker_thread.isRunning()

    service.cleanup()

    assert service.worker_thread.isFinished()

    # Cleanup must be idempotent.
    service.cleanup()
    assert service.worker_thread.isFinished()


def test_cleanup_disconnects_frame_ready_before_quitting_worker_thread(qt_app) -> None:
    handler = _FakeVideoStreamHandlerTracked()
    service = BaseTopViewService(video_handler=handler)
    stream = handler.camera_streams[CameraType.BASE_TOP]

    # Enable processing so the signal is connected.
    service.enabled = True
    assert len(stream.frameReady.slots) == 1

    call_log: list[str] = []
    original_quit = service.worker_thread.quit

    def tracked_quit() -> None:
        call_log.append("quit")
        original_quit()

    service.worker_thread.quit = tracked_quit

    service.cleanup()

    assert len(stream.frameReady.disconnect_calls) == 1
    assert "quit" in call_log
    # The disconnect must happen before the worker thread is asked to quit.
    assert stream.frameReady.disconnect_calls
    assert call_log.index("quit") == 0
    assert service.worker_thread.isFinished()


def test_map_recompute_runs_on_worker_thread_not_gui(qt_app, monkeypatch) -> None:
    """TD-039: GUI k/zoom changes must not call _compute_remap_tables on the GUI thread."""
    handler = _FakeVideoStreamHandler()
    service = BaseTopViewService(video_handler=handler)
    worker_thread = service.worker_thread
    gui_thread = QThread.currentThread()

    compute_threads: list[QThread] = []
    original = service.worker.transformer._compute_remap_tables

    def tracking_compute() -> None:
        compute_threads.append(QThread.currentThread())
        # Avoid real OpenCV work when input dims are synthetic.
        if service.worker.transformer._input_width <= 0:
            return
        original()

    monkeypatch.setattr(service.worker.transformer, "_compute_remap_tables", tracking_compute)

    # Pretend the worker has already seen a frame.
    service.worker.transformer._input_width = 640
    service.worker.transformer._input_height = 480
    service.worker._initialized = True

    service.k1 = -0.25
    # Coalesce timer is single-shot 0ms — drain the GUI event loop then the worker.
    for _ in range(50):
        qt_app.processEvents()
        if compute_threads:
            break
        worker_thread.msleep(5)
        qt_app.processEvents()

    assert compute_threads, "expected worker recompute after k1 change"
    assert all(thread is worker_thread for thread in compute_threads)
    assert gui_thread not in compute_threads
    # Setters must not poke dist_coeffs on the GUI path.
    # dist_coeffs is rebuilt inside recompute; length is 4 when maps exist.
    service.cleanup()


def test_k_setters_do_not_write_dist_coeffs_on_gui(qt_app, monkeypatch) -> None:
    handler = _FakeVideoStreamHandler()
    service = BaseTopViewService(video_handler=handler)
    service.worker.transformer._input_width = 320
    service.worker.transformer._input_height = 240
    service.worker._initialized = True
    # Seed dist_coeffs so we can detect in-place GUI writes.
    service.worker.transformer.dist_coeffs = __import__("numpy").array(
        [[0.0], [0.0], [0.0], [0.0]], dtype="float64"
    )
    dist_before = service.worker.transformer.dist_coeffs.copy()

    # Block the real recompute so only the setter side effects run synchronously.
    monkeypatch.setattr(service, "_reinitialize_maps", lambda: None)
    service.k1 = -0.5
    service.k2 = 0.1

    assert service.worker.transformer.k1 == -0.5
    assert service.worker.transformer.k2 == 0.1
    assert (service.worker.transformer.dist_coeffs == dist_before).all()
    service.cleanup()

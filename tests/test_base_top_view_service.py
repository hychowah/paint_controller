"""Regression tests for BaseTopViewService shutdown cleanup."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

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

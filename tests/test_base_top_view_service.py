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


def test_cleanup_quits_worker_thread(qt_app) -> None:
    handler = _FakeVideoStreamHandler()
    service = BaseTopViewService(video_handler=handler)

    assert service.worker_thread.isRunning()

    service.cleanup()

    assert service.worker_thread.isFinished()

    # Cleanup must be idempotent.
    service.cleanup()
    assert service.worker_thread.isFinished()

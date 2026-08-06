"""ImageProvider / CameraStream cleanup and EF/base feed liveness (3s stale rule)."""

from __future__ import annotations

import time

from PySide6.QtCore import QMutexLocker, QSize
from PySide6.QtGui import QImage

from paint_controller.services.video_stream import (
    STREAM_FRAME_TIMEOUT_S,
    CameraConfig,
    CameraStream,
    CameraType,
    ImageProvider,
    VideoStreamHandler,
)


def test_image_provider_request_image_returns_copy(qt_app) -> None:
    provider = ImageProvider(CameraType.BASE_FRONT, width=32, height=16)
    image = provider.requestImage("frame", QSize(), QSize())
    assert isinstance(image, QImage)
    assert not image.isNull()
    assert image.width() == 32
    assert image.height() == 16


def test_image_provider_request_image_tolerates_null_image(qt_app) -> None:
    provider = ImageProvider(CameraType.BASE_FRONT, width=8, height=8)
    provider.image = None  # type: ignore[assignment]
    image = provider.requestImage("frame", QSize(), QSize())
    assert isinstance(image, QImage)
    assert not image.isNull()


def test_camera_stream_cleanup_keeps_non_null_image(qt_app) -> None:
    config = CameraConfig(
        camera_type=CameraType.BASE_FRONT,
        port=5001,
        name="test",
        enabled=False,
        width=64,
        height=48,
    )
    stream = CameraStream(config)
    assert stream.pipeline is None

    # Simulate a live frame then cleanup while QML may still requestImage.
    painted = QImage(64, 48, QImage.Format_RGB888)
    painted.fill(0x112233)
    with QMutexLocker(stream.image_provider._image_lock):
        stream.image_provider.image = painted

    stream.cleanup()

    assert stream.image_provider.image is not None
    assert not stream.image_provider.image.isNull()
    requested = stream.image_provider.requestImage("frame", QSize(), QSize())
    assert isinstance(requested, QImage)
    assert not requested.isNull()


def test_camera_stream_cleanup_is_idempotent(qt_app) -> None:
    config = CameraConfig(
        camera_type=CameraType.END_EFFECTOR,
        port=5000,
        name="ef",
        enabled=False,
    )
    stream = CameraStream(config)
    stream.cleanup()
    stream.cleanup()
    assert stream.image_provider.image is not None
    assert not stream.image_provider.requestImage("frame", QSize(), QSize()).isNull()


def test_feed_liveness_defaults_unavailable_and_recovers(qt_app) -> None:
    """Never-framed feeds are unavailable; a frame marks available; stale clears pixels."""
    handler = VideoStreamHandler(ros_node=None)
    try:
        assert handler.endEffectorStreamAvailable is False
        assert handler.baseFrontStreamAvailable is False
        assert handler.baseRearStreamAvailable is False

        now = time.time()
        handler._note_feed_frame(CameraType.END_EFFECTOR, now=now)
        handler._note_feed_frame(CameraType.BASE_FRONT, now=now)
        assert handler.endEffectorStreamAvailable is True
        assert handler.baseFrontStreamAvailable is True

        # Simulate a painted base frame then stale timeout.
        painted = QImage(16, 16, QImage.Format_RGB888)
        painted.fill(0xABCDEF)
        base = handler._get_stream(CameraType.BASE_FRONT)
        assert base is not None
        with QMutexLocker(base.image_provider._image_lock):
            base.image_provider.image = painted

        state = handler._feed_availability[CameraType.BASE_FRONT]
        state.last_status_update_time = now - (STREAM_FRAME_TIMEOUT_S + 0.5)
        handler._check_feed_availability()

        assert handler.baseFrontStreamAvailable is False
        # Stale path clears frozen pixels (black placeholder), not the EF freeze.
        cleared = base.image_provider.requestImage("frame", QSize(), QSize())
        assert not cleared.isNull()
        # Placeholder is black RGB888; original paint was non-black.
        assert cleared.pixel(0, 0) != painted.pixel(0, 0)

        # Fresh frame restores availability.
        handler._note_feed_frame(CameraType.BASE_FRONT, now=time.time())
        assert handler.baseFrontStreamAvailable is True
    finally:
        handler.cleanup()


def test_feed_liveness_ignores_untracked_camera_types(qt_app) -> None:
    handler = VideoStreamHandler(ros_node=None)
    try:
        handler._note_feed_frame(CameraType.BASE_TOP, now=time.time())
        handler._note_feed_frame(CameraType.CONFIGURABLE, now=time.time())
        assert handler.endEffectorStreamAvailable is False
        assert handler.baseFrontStreamAvailable is False
    finally:
        handler.cleanup()

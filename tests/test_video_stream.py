"""TD-039: ImageProvider / CameraStream cleanup must never expose a null QImage."""

from __future__ import annotations

from PySide6.QtCore import QMutexLocker, QSize
from PySide6.QtGui import QImage

from paint_controller.services.video_stream import CameraConfig, CameraStream, CameraType, ImageProvider


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

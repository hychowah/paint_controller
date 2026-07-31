"""QML-facing lidar telemetry with per-property NOTIFY (TD-037 residual)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject

from paint_controller.models.simple_device_status import SimpleDeviceStatus, _make_status_field

LIDAR_STATUS_SIGNAL_MAP: tuple[tuple[str, str], ...] = (
    ("distance_changed", "distanceChanged"),
    ("angle_changed", "angleChanged"),
)

LIDAR_STATUS_PROPERTY_NAMES: tuple[str, ...] = ("distance", "angle")


class LidarStatus(SimpleDeviceStatus):
    """Read-only camelCase projection of ``LidarController`` for QML.

    Note: any QML that listened to a blanket ``changed`` signal must use
    ``distanceChanged`` / ``angleChanged`` instead.
    """

    distanceChanged, distance = _make_status_field("distance", float, 0.0)
    angleChanged, angle = _make_status_field("angle", float, 0.0)

    _STATUS_SCHEMA: tuple[tuple[str, str, str, type], ...] = (
        ("distance_changed", "distance", "distanceChanged", float),
        ("angle_changed", "angle", "angleChanged", float),
    )

    def __init__(self, lidar_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(lidar_controller, parent)

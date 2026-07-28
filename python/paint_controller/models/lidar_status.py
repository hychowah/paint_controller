"""QML-facing lidar telemetry with per-property NOTIFY (TD-037 residual)."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.models.status_wiring import connect_required

LIDAR_STATUS_SIGNAL_MAP: tuple[tuple[str, str], ...] = (
    ("distance_changed", "distanceChanged"),
    ("angle_changed", "angleChanged"),
)

LIDAR_STATUS_PROPERTY_NAMES: tuple[str, ...] = ("distance", "angle")


class LidarStatus(QObject):
    """Read-only camelCase projection of ``LidarController`` for QML.

    Note: any QML that listened to a blanket ``changed`` signal must use
    ``distanceChanged`` / ``angleChanged`` instead.
    """

    distanceChanged = Signal()
    angleChanged = Signal()

    def __init__(self, lidar_controller: Any, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._c = lidar_controller
        connect_required(lidar_controller, "distance_changed", self.distanceChanged.emit)
        connect_required(lidar_controller, "angle_changed", self.angleChanged.emit)

    def _float(self, name: str, default: float = 0.0) -> float:
        value = getattr(self._c, name, default)
        try:
            return float(value or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @Property(float, notify=distanceChanged)
    def distance(self) -> float:
        return self._float("distance")

    @Property(float, notify=angleChanged)
    def angle(self) -> float:
        return self._float("angle")

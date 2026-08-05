#!/usr/bin/env python3
"""Qt I/O shell for pure :class:`~paint_controller.controllers.lidar.LidarHal` (Level C P1).

Owns Signals, RosTelemetryBridge lifetime, and DeviceNotifier mapping.
``LidarStatus`` wires to this shell (signals + field getattr).
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal
from rclpy.node import Node

from paint_controller.controllers.lidar import LidarHal
from paint_controller.core.device_notifier import SignalDeviceNotifier
from paint_controller.core.ros_telemetry import RosTelemetryBridge

logger = logging.getLogger(__name__)


class LidarController(QObject):
    """Presentation/I/O shell for wall-detection lidar (QML via ``LidarStatus``)."""

    distance_changed = Signal()
    angle_changed = Signal()

    def __init__(self, node: Node, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._notifier = SignalDeviceNotifier(self, parent=self)
        # Bridges parented to this shell (not the pure HAL).
        self._distance_bridge = RosTelemetryBridge(self._apply_distance, parent=self)
        self._angle_bridge = RosTelemetryBridge(self._apply_angle, parent=self)
        self._hal = LidarHal(
            node,
            notifier=self._notifier,
            post_distance=self._distance_bridge.post,
            post_angle=self._angle_bridge.post,
        )

    def _apply_distance(self, snap: object) -> None:
        self._hal.apply_distance(snap)

    def _apply_angle(self, snap: object) -> None:
        self._hal.apply_angle(snap)

    @property
    def hal(self) -> LidarHal:
        return self._hal

    def get_distance(self) -> float:
        return self._hal.get_distance()

    def set_distance(self, value: float) -> None:
        self._hal.set_distance(value)

    def get_angle(self) -> float:
        return self._hal.get_angle()

    def set_angle(self, value: float) -> None:
        self._hal.set_angle(value)

    @property
    def distance(self) -> float:
        return self._hal.distance

    @distance.setter
    def distance(self, value: float) -> None:
        self._hal.distance = value

    @property
    def angle(self) -> float:
        return self._hal.angle

    @angle.setter
    def angle(self, value: float) -> None:
        self._hal.angle = value

    def getDistance(self) -> float:
        return self._hal.getDistance()

    def getAngle(self) -> float:
        return self._hal.getAngle()

    def cleanup(self) -> None:
        logger.info("Cleaning up LidarController shell...")
        self._hal.cleanup()

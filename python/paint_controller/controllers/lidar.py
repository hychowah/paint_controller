#!/usr/bin/env python3

from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from rclpy.node import Node
from std_msgs.msg import Float32

from paint_controller.core.ros_telemetry import RosTelemetryBridge

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LidarDistanceSnapshot:
    distance: float


@dataclass(frozen=True, slots=True)
class LidarAngleSnapshot:
    angle: float


class LidarController(QObject):
    """Wall-detection lidar telemetry (TD-056 pattern).

    QML surface is ``LidarStatus``; public names + Signals for getattr projectors.
    """

    distance_changed = Signal()
    angle_changed = Signal()

    def __init__(self, node: Node) -> None:
        super().__init__()
        self._node = node
        self._distance = 0.0
        self._angle = 0.0

        self._distance_bridge = RosTelemetryBridge(self._apply_distance, parent=self)
        self._angle_bridge = RosTelemetryBridge(self._apply_angle, parent=self)

        self._setup_subscribers()

    def _setup_subscribers(self) -> None:
        self._distance_sub = self._node.create_subscription(
            Float32, "/ef/lidar/wall_detection/distance", self._distance_callback, 10
        )
        self._angle_sub = self._node.create_subscription(
            Float32, "/ef/lidar/wall_detection/filtered_angle", self._angle_callback, 10
        )
        logger.info("Subscribed to /ef/lidar/wall_detection/distance and /ef/lidar/wall_detection/filtered_angle")

    def get_distance(self) -> float:
        return self._distance

    def set_distance(self, value: float) -> None:
        if self._distance != value:
            self._distance = value
            self.distance_changed.emit()

    def get_angle(self) -> float:
        return self._angle

    def set_angle(self, value: float) -> None:
        if self._angle != value:
            self._angle = value
            self.angle_changed.emit()

    def _distance_callback(self, msg: Float32) -> None:
        """ROS spin: post POD only."""
        self._distance_bridge.post(LidarDistanceSnapshot(distance=float(msg.data)))

    def _angle_callback(self, msg: Float32) -> None:
        """ROS spin: post POD only."""
        self._angle_bridge.post(LidarAngleSnapshot(angle=float(msg.data)))

    def _apply_distance(self, snap: object) -> None:
        if isinstance(snap, LidarDistanceSnapshot):
            self.set_distance(snap.distance)

    def _apply_angle(self, snap: object) -> None:
        if isinstance(snap, LidarAngleSnapshot):
            self.set_angle(snap.angle)

    # Plain Python properties (Level B) — not Qt Property; QML uses LidarStatus.
    @property
    def distance(self) -> float:
        return self.get_distance()

    @distance.setter
    def distance(self, value: float) -> None:
        self.set_distance(value)

    @property
    def angle(self) -> float:
        return self.get_angle()

    @angle.setter
    def angle(self, value: float) -> None:
        self.set_angle(value)

    def getDistance(self) -> float:
        return self.get_distance()

    def getAngle(self) -> float:
        return self.get_angle()

    def cleanup(self) -> None:
        logger.info("Cleaning up LidarController...")

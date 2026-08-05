#!/usr/bin/env python3
"""Pure lidar HAL (Level C P1) — no PySide6.

ROS spin posts POD via injected bridge ``post`` callables; main-thread
``apply_*`` mutates state and notifies through :class:`DeviceNotifier`.
Presentation Signals and bridge lifetime live on :class:`LidarController`
(``lidar_shell``).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rclpy.node import Node
from std_msgs.msg import Float32

from paint_controller.ports.notifier import DeviceNotifier, NullDeviceNotifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class LidarDistanceSnapshot:
    distance: float


@dataclass(frozen=True, slots=True)
class LidarAngleSnapshot:
    angle: float


class LidarHal:
    """Wall-detection lidar state + ROS subscribe (Qt-free)."""

    def __init__(
        self,
        node: Node,
        *,
        notifier: DeviceNotifier | None = None,
        post_distance: Callable[[object], None] | None = None,
        post_angle: Callable[[object], None] | None = None,
    ) -> None:
        self._node = node
        self._notifier: DeviceNotifier = notifier if notifier is not None else NullDeviceNotifier()
        self._post_distance = post_distance
        self._post_angle = post_angle
        self._distance = 0.0
        self._angle = 0.0
        self._setup_subscribers()

    def _setup_subscribers(self) -> None:
        self._distance_sub = self._node.create_subscription(
            Float32, "/ef/lidar/wall_detection/distance", self._distance_callback, 10
        )
        self._angle_sub = self._node.create_subscription(
            Float32, "/ef/lidar/wall_detection/filtered_angle", self._angle_callback, 10
        )
        logger.info(
            "Subscribed to /ef/lidar/wall_detection/distance and "
            "/ef/lidar/wall_detection/filtered_angle"
        )

    def get_distance(self) -> float:
        return self._distance

    def set_distance(self, value: float) -> None:
        if self._distance != value:
            self._distance = value
            self._notifier.notify("distance_changed")

    def get_angle(self) -> float:
        return self._angle

    def set_angle(self, value: float) -> None:
        if self._angle != value:
            self._angle = value
            self._notifier.notify("angle_changed")

    def _distance_callback(self, msg: Float32) -> None:
        """ROS spin: post POD only."""
        snap = LidarDistanceSnapshot(distance=float(msg.data))
        if self._post_distance is not None:
            self._post_distance(snap)
        else:
            self.apply_distance(snap)

    def _angle_callback(self, msg: Float32) -> None:
        """ROS spin: post POD only."""
        snap = LidarAngleSnapshot(angle=float(msg.data))
        if self._post_angle is not None:
            self._post_angle(snap)
        else:
            self.apply_angle(snap)

    def apply_distance(self, snap: object) -> None:
        if isinstance(snap, LidarDistanceSnapshot):
            self.set_distance(snap.distance)

    def apply_angle(self, snap: object) -> None:
        if isinstance(snap, LidarAngleSnapshot):
            self.set_angle(snap.angle)

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
        logger.info("Cleaning up LidarHal...")


# Back-compat alias for pure-unit imports that still say LidarController on HAL.
# Production composition uses lidar_shell.LidarController (QObject shell).
LidarController = LidarHal  # type: ignore[misc,assignment]

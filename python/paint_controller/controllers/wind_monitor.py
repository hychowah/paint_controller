#!/usr/bin/env python3

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from rclpy.node import Node
from std_msgs.msg import Float32


class WindMonitor(QObject):
    """Wind telemetry adapter. Not currently on production QML context."""

    windSpeedChanged = Signal()
    windDirectionChanged = Signal()

    def __init__(self, node: Node) -> None:
        super().__init__()
        self._node = node
        self._speed = 0.0
        self._direction = 0.0
        self._setup_subscribers()

    def _speed_callback(self, msg: Float32) -> None:
        self._speed = msg.data
        self.windSpeedChanged.emit()

    def _direction_callback(self, msg: Float32) -> None:
        self._direction = msg.data
        self.windDirectionChanged.emit()

    def get_speed(self) -> float:
        return self._speed

    def get_direction(self) -> float:
        return self._direction

    def _setup_subscribers(self) -> None:
        self._node.create_subscription(Float32, "/wind/speed", self._speed_callback, 10)
        self._node.create_subscription(Float32, "/wind/direction", self._direction_callback, 10)

    # Plain Python properties (Level B consistency).
    @property
    def windSpeed(self) -> float:
        return self.get_speed()

    @property
    def windDirection(self) -> float:
        return self.get_direction()

    def cleanup(self) -> None:
        """Clean up wind monitor resources"""
        # No specific cleanup needed for this component
        pass

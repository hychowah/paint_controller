#!/usr/bin/env python3
import time
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import Float64, Bool, Float32
from paint_interfaces.msg import WinchStatus, MoveWinchLength
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer


class WindMonitor(QObject):
    windSpeedChanged = Signal()
    windDirectionChanged = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self._node = node
        self._speed = 0
        self._direction = 0
        self._setup_subscribers()

    def _speed_callback(self, msg: Float32):
        self._speed = msg.data
        self.windSpeedChanged.emit()

    def _direction_callback(self, msg: Float32):
        self._direction = msg.data
        self.windDirectionChanged.emit()

    def get_speed(self) -> float:
        return self._speed
    
    def get_direction(self) -> float:
        return self._direction
    
    def _setup_subscribers(self):   
        self._node.create_subscription(Float32, '/wind/speed', self._speed_callback, 10)
        self._node.create_subscription(Float32, '/wind/direction', self._direction_callback, 10)

    windSpeed = Property(float, get_speed, notify=windSpeedChanged)
    windDirection = Property(float, get_direction, notify=windDirectionChanged)
    
    def cleanup(self):
        """Clean up wind monitor resources"""
        # No specific cleanup needed for this component
        pass
#!/usr/bin/env python3

from std_msgs.msg import Float32
from PySide6.QtCore import QObject, Signal, Property, Slot


class LidarController(QObject):
    # Define Qt signals
    distance_changed = Signal()
    angle_changed = Signal()
    
    def __init__(self, robot_controller):
        super().__init__()
        self._robot_controller = robot_controller  # Store reference to the robot controller
        
        # Wall detection values
        self._distance = 0.0
        self._angle = 0.0
        
        # Configure subscribers
        self._setup_subscribers()
        
    def _setup_subscribers(self):
        """Set up ROS subscribers for wall detection data"""
        self._distance_sub = self._robot_controller.create_subscription(
            Float32,
            '/ef/lidar/wall_detection/distance',
            self._distance_callback,
            10
        )
        self._angle_sub = self._robot_controller.create_subscription(
            Float32,
            '/ef/lidar/wall_detection/filtered_angle',
            self._angle_callback,
            10
        )
        print('LidarController: Subscribed to /ef/lidar/wall_detection/distance and /ef/lidar/wall_detection/filtered_angle')
    
    def get_distance(self) -> float:
        return self._distance
    
    def set_distance(self, value: float):
        if self._distance != value:
            self._distance = value
            self.distance_changed.emit()
    
    def get_angle(self) -> float:
        return self._angle
    
    def set_angle(self, value: float):
        if self._angle != value:
            self._angle = value
            self.angle_changed.emit()
    
    def _distance_callback(self, msg: Float32):
        """Process incoming distance messages from wall detection"""
        self.set_distance(msg.data)
    
    def _angle_callback(self, msg: Float32):
        """Process incoming angle messages from wall detection"""
        self.set_angle(msg.data)
    
    # Qt Properties for QML access
    distance = Property(float, get_distance, set_distance, notify=distance_changed)
    angle = Property(float, get_angle, set_angle, notify=angle_changed)
    
    @Slot(result=float)
    def getDistance(self):
        """Get current wall detection distance"""
        return self.get_distance()
    
    @Slot(result=float)
    def getAngle(self):
        """Get current wall detection angle"""
        return self.get_angle()
    
    def cleanup(self):
        """Cleanup controller resources"""
        print('Cleaning up LidarController...')


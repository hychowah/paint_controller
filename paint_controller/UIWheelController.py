#!/usr/bin/env python3
import time
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import Bool, Float32
from towngas_interfaces.msg import WheelStatus
from PySide6.QtCore import QObject, Signal, Property, Slot

class WheelController(QObject):
    # Signals for property changed notifications
    left_wheel_speed_changed = Signal()
    right_wheel_speed_changed = Signal()
    left_wheel_current_changed = Signal()
    right_wheel_current_changed = Signal()
    left_wheel_position_changed = Signal()
    right_wheel_position_changed = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self._node = node
        
        # Initialize property values
        self._left_wheel_speed = 0.0
        self._right_wheel_speed = 0.0
        self._left_wheel_current = 0.0
        self._right_wheel_current = 0.0
        self._left_wheel_position = 0.0
        self._right_wheel_position = 0.0
        
        self._enabled = False
        self._last_command_time = time.time()
        
        # Throttle variables
        self._last_update_time = 0
        self._min_update_interval = 0.05  # 50ms minimum between UI updates
        
        # Setup publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()

    def _setup_publishers(self):
        """Setup ROS publishers for wheel control"""
        self._left_wheel_speed_pub = self._node.create_publisher(Float32, 'wheel/left/speed/cmd', 1)
        self._right_wheel_speed_pub = self._node.create_publisher(Float32, 'wheel/right/speed/cmd', 1)
        self._disable_pub = self._node.create_publisher(Bool, 'wheel/disable/cmd', 1)
        self._set_zero = self._node.create_publisher(Bool, 'wheel/set_zero/cmd', 1)

    def _setup_subscribers(self):
        """Setup ROS subscribers for wheel status"""
        self._status_sub = self._node.create_subscription(
            WheelStatus,
            'wheel_motor_status',  
            self._status_callback,
            10  
        )

    def _status_callback(self, msg: WheelStatus):
        """Callback function for wheel status messages"""
        try:
            self.update_status(msg)
        except Exception as e:
            print(f"Error in wheel status callback: {e}")

    def command_left_wheel_speed(self, speed: float):
        msg = Float32()
        msg.data = speed
        self._left_wheel_speed_pub.publish(msg)
        self._last_command_time = time.time()

    def command_right_wheel_speed(self, speed: float): 
        msg = Float32()
        msg.data = speed
        self._right_wheel_speed_pub.publish(msg)
        self._last_command_time = time.time()

    def update_status(self, msg: WheelStatus):
        """
        Process incoming wheel status messages and update properties with throttling
        """
        current_time = time.time()
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            
            # Update property values
            self.set_left_wheel_speed(msg.left_wheel_speed)
            self.set_right_wheel_speed(msg.right_wheel_speed)
            self.set_left_wheel_current(msg.left_wheel_current)
            self.set_right_wheel_current(msg.right_wheel_current)
            self.set_left_wheel_position(msg.left_wheel_pos)
            self.set_right_wheel_position(msg.right_wheel_pos)

    # Property getters and setters
    def get_left_wheel_speed(self) -> float:
        return self._left_wheel_speed
        
    def set_left_wheel_speed(self, value: float):
        if self._left_wheel_speed != value:
            self._left_wheel_speed = value
            self.left_wheel_speed_changed.emit()
            
    def get_right_wheel_speed(self) -> float:
        return self._right_wheel_speed
        
    def set_right_wheel_speed(self, value: float):
        if self._right_wheel_speed != value:
            self._right_wheel_speed = value
            self.right_wheel_speed_changed.emit()
            
    def get_left_wheel_current(self) -> float:
        return self._left_wheel_current
        
    def set_left_wheel_current(self, value: float):
        if self._left_wheel_current != value:
            self._left_wheel_current = value
            self.left_wheel_current_changed.emit()
            
    def get_right_wheel_current(self) -> float:
        return self._right_wheel_current
        
    def set_right_wheel_current(self, value: float):
        if self._right_wheel_current != value:
            self._right_wheel_current = value
            self.right_wheel_current_changed.emit()
            
    def get_left_wheel_position(self) -> float:
        return self._left_wheel_position
        
    def set_left_wheel_position(self, value: float):
        if self._left_wheel_position != value:
            self._left_wheel_position = value
            self.left_wheel_position_changed.emit()
            
    def get_right_wheel_position(self) -> float:
        return self._right_wheel_position
        
    def set_right_wheel_position(self, value: float):
        if self._right_wheel_position != value:
            self._right_wheel_position = value
            self.right_wheel_position_changed.emit()
    
    # Define Qt properties
    left_wheel_speed = Property(float, get_left_wheel_speed, set_left_wheel_speed, notify=left_wheel_speed_changed)
    right_wheel_speed = Property(float, get_right_wheel_speed, set_right_wheel_speed, notify=right_wheel_speed_changed)
    left_wheel_current = Property(float, get_left_wheel_current, set_left_wheel_current, notify=left_wheel_current_changed)
    right_wheel_current = Property(float, get_right_wheel_current, set_right_wheel_current, notify=right_wheel_current_changed)
    left_wheel_position = Property(float, get_left_wheel_position, set_left_wheel_position, notify=left_wheel_position_changed)
    right_wheel_position = Property(float, get_right_wheel_position, set_right_wheel_position, notify=right_wheel_position_changed)
    
    @Slot(bool)
    def set_enabled(self, enabled: bool):
        """
        Enable or disable wheel control
        
        Args:
            enabled (bool): True to enable, False to disable
        """
        self._enabled = enabled
        msg = Bool()
        msg.data = not enabled
        self._disable_pub.publish(msg)
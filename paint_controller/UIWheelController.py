#!/usr/bin/env python3
import time
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import Bool, Float32
from paint_interfaces.msg import WheelStatus
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer

class WheelController(QObject):
    # Signals for property changed notifications
    left_wheel_speed_changed = Signal()
    right_wheel_speed_changed = Signal()
    left_wheel_current_changed = Signal()
    right_wheel_current_changed = Signal()
    left_wheel_position_changed = Signal()
    right_wheel_position_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()

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
        
        # Connection status
        self._available = False
        self._enabled = False
        self._last_command_time = time.time()
        self._last_status_update_time = 0
        self._connection_timeout = 1.0  # Time in seconds before considering disconnected
        
        # Throttle variables
        self._last_update_time = 0
        self._min_update_interval = 0.05  # 50ms minimum between UI updates
        
        # Setup publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()
        
        # Create availability check timer
        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)  # Check every 200ms

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
        print(f"Wheel status subscriber set up on topic 'wheel_motor_status'")

    def _check_availability(self):
        """
        Periodically check if wheel controller is still connected based on time since last message
        This runs on a timer to ensure we detect disconnections even when no new messages arrive
        """
        current_time = time.time()
        
        # Calculate time since last status update
        time_since_last_update = current_time - self._last_status_update_time
        
        # If it's been too long since the last update, consider disconnected
        if time_since_last_update > self._connection_timeout:
            # Only emit if there's a change in availability
            if self._available:
                self._available = False
                self.available_changed.emit()
                print(f"Wheel controller considered disconnected: {time_since_last_update:.1f}s since last message")

    def _status_callback(self, msg: WheelStatus):
        """Callback function for wheel status messages"""
        try:
            # Update the last status time when any message is received
            current_time = time.time()
            self._last_status_update_time = current_time
            
            # If message is received, the device is considered connected
            was_available = self._available
            self._available = True
            if not was_available:
                self.available_changed.emit()
                print("Wheel controller connection restored")
            
            # Process the status update
            self.update_status(msg)
        except Exception as e:
            print(f"Error in wheel status callback: {e}")

    def command_left_wheel_speed(self, speed: float):
        if not self._available:
            print("Cannot command left wheel: Controller not available")
            return False
            
        msg = Float32()
        msg.data = speed
        self._left_wheel_speed_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def command_right_wheel_speed(self, speed: float): 
        if not self._available:
            print("Cannot command right wheel: Controller not available")
            return False
            
        msg = Float32()
        msg.data = speed
        self._right_wheel_speed_pub.publish(msg)
        self._last_command_time = time.time()
        return True

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
            self.set_enabled(msg.enabled)

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
            
    def get_available(self) -> bool:
        return self._available
    
    def set_available(self, value: bool):
        if self._available != value:
            self._available = value
            self.available_changed.emit()
    
    def get_enabled(self) -> bool:
        return self._enabled
    
    def set_enabled(self, value: bool):
        if self._enabled != value:
            self._enabled = value
            self.enabled_changed.emit()
    
    # Define Qt properties
    left_wheel_speed = Property(float, get_left_wheel_speed, set_left_wheel_speed, notify=left_wheel_speed_changed)
    right_wheel_speed = Property(float, get_right_wheel_speed, set_right_wheel_speed, notify=right_wheel_speed_changed)
    left_wheel_current = Property(float, get_left_wheel_current, set_left_wheel_current, notify=left_wheel_current_changed)
    right_wheel_current = Property(float, get_right_wheel_current, set_right_wheel_current, notify=right_wheel_current_changed)
    left_wheel_position = Property(float, get_left_wheel_position, set_left_wheel_position, notify=left_wheel_position_changed)
    right_wheel_position = Property(float, get_right_wheel_position, set_right_wheel_position, notify=right_wheel_position_changed)
    available = Property(bool, get_available, notify=available_changed)
    enabled = Property(bool, get_enabled, set_enabled, notify=enabled_changed)
    
    @Slot(bool)
    def setEnabled(self, enabled: bool):
        """
        Enable or disable wheel control
        
        Args:
            enabled (bool): True to enable, False to disable
        """
        msg = Bool()
        msg.data = not enabled
        self._disable_pub.publish(msg)
        print(f'Wheel controller {"enabled" if enabled else "disabled"}')
        
    @Slot(float)
    def setLeftSpeed(self, speed: float):
        """Set left wheel speed from QML"""
        return self.command_left_wheel_speed(speed)
    
    @Slot(float)
    def setRightSpeed(self, speed: float):
        """Set right wheel speed from QML"""
        return self.command_right_wheel_speed(speed)
        
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()
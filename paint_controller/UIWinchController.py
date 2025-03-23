#!/usr/bin/env python3
import time
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import Float64, Bool
from towngas_interfaces.msg import WinchStatus, MoveWinchLength
from PySide6.QtCore import QObject, Signal, Property, Slot

class WinchController(QObject):
    # Define signals for property changes
    cable_length_changed = Signal()
    cable_speed_changed = Signal()
    winch_torque_changed = Signal()
    motor_temperature_changed = Signal()
    motor_voltage_changed = Signal()
    motor_brake_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self._node = node
        
        # Initialize property values
        self._max_speed = 40.0 # output rpm

        self._cable_length = 0.0
        self._cable_speed = 0.0
        self._winch_torque = 0.0
        self._motor_temperature = 0.0
        self._motor_voltage = 0.0
        self._motor_brake = True
        self._available = False
        self._enabled = False
        
        # Status tracking
        self._last_command_time = time.time()
        self._last_status_update_time = 0
        self._connection_timeout = 1.0
        self._watchdog_timeout = 1.0
        
        # Throttle variables
        self._last_update_time = 0
        self._min_update_interval = 0.05  # 50ms minimum between UI updates
        
        # Setup publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()
    
    def _setup_publishers(self):
        """Setup ROS publishers for winch control"""
        self._speed_pub = self._node.create_publisher(Float64, 'winch/move/speed/rpm/cmd', 1)
        self._enable_pub = self._node.create_publisher(Bool, 'winch/enable/cmd', 1)
        self._move_increment_pub = self._node.create_publisher(MoveWinchLength, 'winch/move/increment/cmd', 1)
    
    def _setup_subscribers(self):
        """Setup ROS subscribers for winch status"""
        self._status_sub = self._node.create_subscription(
            WinchStatus,
            'winch/status', 
            self._status_callback,
            10
        )
        print(f"Winch status subscriber set up on topic 'winch/status'")
    
    def _status_callback(self, msg: WinchStatus):
        """Callback function for winch status messages"""
        try:
            self.update_status(msg)
        except Exception as e:
            print(f"Error in winch status callback: {e}")
    
    def update_status(self, msg: WinchStatus):
        """Update property values from incoming status message"""
        current_time = time.time()
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            self._last_status_update_time = current_time
            
            # Update property values
            self.set_cable_length(msg.cable_length)
            self.set_cable_speed(msg.cable_speed)
            self.set_winch_torque(msg.winch_torque)
            self.set_motor_temperature(msg.motor_temperature)
            self.set_motor_voltage(msg.motor_voltage)
            self.set_motor_brake(msg.motor_brake)
            self.set_available(msg.available)
            # print(f"Winch status updated: {msg}")
    
    def command_speed(self, speed: float) -> bool:
        """Command winch speed with safety limits"""
        safe_speed = self._apply_safety_limits(speed)
        msg = Float64()
        msg.data = safe_speed
        self._speed_pub.publish(msg)
        self._last_command_time = time.time()
        return True
    
    def move_increment(self, length_mm: int, speed_mm_s: int) -> bool:
        """Move winch by an increment"""
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            self._move_increment_pub.publish(msg)
            print(f'Moving winch by: {length_mm} mm at {speed_mm_s} mm/s')
            return True
        except Exception as e:
            print(f'Error moving winch: {e}')
            return False
    
    def _apply_safety_limits(self, speed: float) -> float:
        """Apply safety limits to winch speed"""
        return max(min(speed, self._max_speed), -self._max_speed)
    
    @property
    def is_connected(self) -> bool:
        """Check if winch is connected based on recent status updates"""
        return time.time() - self._last_status_update_time < self._connection_timeout
    
    @property
    def is_enabled(self) -> bool:
        """Check if winch is enabled and watchdog is alive"""
        return self._enabled and self._check_watchdog()
    
    def _check_watchdog(self) -> bool:
        """Check if commands have been sent recently enough to keep watchdog alive"""
        return time.time() - self._last_command_time < self._watchdog_timeout
    
    # Property getters and setters
    def get_cable_length(self) -> float:
        return self._cable_length
    
    def set_cable_length(self, value: float):
        if self._cable_length != value:
            self._cable_length = value
            self.cable_length_changed.emit()
    
    def get_cable_speed(self) -> float:
        return self._cable_speed
    
    def set_cable_speed(self, value: float):
        if self._cable_speed != value:
            self._cable_speed = value
            self.cable_speed_changed.emit()
    
    def get_winch_torque(self) -> float:
        return self._winch_torque
    
    def set_winch_torque(self, value: float):
        if self._winch_torque != value:
            self._winch_torque = value
            self.winch_torque_changed.emit()
    
    def get_motor_temperature(self) -> float:
        return self._motor_temperature
    
    def set_motor_temperature(self, value: float):
        if self._motor_temperature != value:
            self._motor_temperature = value
            self.motor_temperature_changed.emit()
    
    def get_motor_voltage(self) -> float:
        return self._motor_voltage
    
    def set_motor_voltage(self, value: float):
        if self._motor_voltage != value:
            self._motor_voltage = value
            self.motor_voltage_changed.emit()
    
    def get_motor_brake(self) -> bool:
        return self._motor_brake
    
    def set_motor_brake(self, value: bool):
        if self._motor_brake != value:
            self._motor_brake = value
            self.motor_brake_changed.emit()
    
    def get_available(self) -> bool:
        return self._available and self.is_connected
    
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
            
            # Send command to enable/disable winch
            msg = Bool()
            msg.data = value
            self._enable_pub.publish(msg)
            print(f'Winch {"enabled" if value else "disabled"}')
    
    # Define Qt properties
    cable_length = Property(float, get_cable_length, set_cable_length, notify=cable_length_changed)
    cable_speed = Property(float, get_cable_speed, set_cable_speed, notify=cable_speed_changed)
    winch_torque = Property(float, get_winch_torque, set_winch_torque, notify=winch_torque_changed)
    motor_temperature = Property(float, get_motor_temperature, set_motor_temperature, notify=motor_temperature_changed)
    motor_voltage = Property(float, get_motor_voltage, set_motor_voltage, notify=motor_voltage_changed)
    motor_brake = Property(bool, get_motor_brake, set_motor_brake, notify=motor_brake_changed)
    available = Property(bool, get_available, set_available, notify=available_changed)
    enabled = Property(bool, get_enabled, set_enabled, notify=enabled_changed)
    
    # Slot methods for QML
    @Slot(float)
    def setSpeed(self, speed: float):
        """Set winch speed from QML"""
        return self.command_speed(speed)
    
    @Slot(int, int)
    def moveIncrement(self, length_mm: int, speed_mm_s: int):
        """Move winch by increment from QML"""
        return self.move_increment(length_mm, speed_mm_s)
    
    @Slot(bool)
    def setEnabled(self, enabled: bool):
        """Enable/disable winch from QML"""
        self.set_enabled(enabled)
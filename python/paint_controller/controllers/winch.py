#!/usr/bin/env python3
import time
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import Float64, Bool
from paint_interfaces.msg import WinchStatus, MoveWinchLength
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer

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
    load_detection_changed = Signal()  
    unusual_load_detected_changed = Signal()  

    def __init__(self, node: Node):
        super().__init__()
        self._node = node
        
        # Initialize property values
        # Get max_speed from settings_manager if available, otherwise use default
        if hasattr(node, 'settings_manager'):
            self._max_speed = node.settings_manager.get('winch_max_speed_mmps') or 400.0
            # Subscribe to settings changes
            node.settings_manager.winch_max_speed_mmps_changed.connect(self._on_max_speed_changed)
        else:
            self._max_speed = 400.0  # default output mm/s

        self._cable_length = 0.0
        self._cable_speed = 0.0
        self._winch_torque = 0.0
        self._motor_temperature = 0.0
        self._motor_voltage = 0.0
        self._motor_brake = True
        self._available = False
        self._enabled = False
        self._load_detection_enabled = False 
        self._unusual_load_detected = False  
        
        # Status tracking
        self._last_command_time = time.time()
        self._last_status_update_time = 0
        self._connection_timeout = 1.0  # Time in seconds before considering the winch disconnected
        self._watchdog_timeout = 1.0
        
        # Throttle variables
        self._last_update_time = 0
        self._min_update_interval = 0.1  # 50ms minimum between UI updates
        
        # Setup publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()
        
        # Create availability check timer
        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)  # Check every 200ms
    
    def _setup_publishers(self):
        """Setup ROS publishers for winch control"""
        self._speed_rpm_pub = self._node.create_publisher(Float64, 'winch/move/speed/rpm/cmd', 1)
        self._speed_mmps_pub = self._node.create_publisher(Float64, 'winch/move/speed/mmps/cmd', 1)
        self._enable_pub = self._node.create_publisher(Bool, 'winch/enable/cmd', 1)
        self._move_increment_pub = self._node.create_publisher(MoveWinchLength, 'winch/move/increment/cmd', 1)
        self._move_absolute_pub = self._node.create_publisher(MoveWinchLength, 'winch/move/absolute/cmd', 1)
        self._load_detection_pub = self._node.create_publisher(Bool, 'winch/load_detection/cmd', 1)
    
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
    
    def _check_availability(self):
        """
        Periodically check if winch is still connected based on time since last message
        This runs on a timer to ensure we detect disconnections even when no new messages arrive
        """
        current_time = time.time()
        
        # Calculate time since last status update
        time_since_last_update = current_time - self._last_status_update_time
        
        # If it's been too long since the last update, consider the winch disconnected
        if time_since_last_update > self._connection_timeout:
            # Only emit if there's a change in availability
            if self._available:
                self._available = False
                self.available_changed.emit()
                print(f"Winch considered disconnected: {time_since_last_update:.1f}s since last message")
    
    def update_status(self, msg: WinchStatus):
        """Update property values from incoming status message"""
        current_time = time.time()
        self._last_status_update_time = current_time
        
        # If message is received, the device is considered connected
        # even if msg.available is False (that would indicate a connected device in error state)
        was_available = self._available
        self._available = True
        if not was_available:
            self.available_changed.emit()
            print("Winch connection restored")
        
        # Update other properties with throttling
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            
            # Update property values
            self.set_enabled(msg.enabled)
            self.set_cable_length(msg.cable_length)
            self.set_cable_speed(msg.cable_speed)
            self.set_winch_torque(msg.winch_torque)
            self.set_motor_temperature(msg.motor_temperature)
            self.set_motor_voltage(msg.motor_voltage)
            self.set_motor_brake(msg.motor_brake)
            self.set_load_detection_enabled(msg.load_detection_mode)  
            self.set_unusual_load_detected(msg.unusual_load_detected)  
    
    def command_speed_rpm(self, speed: float) -> bool:
        """Command winch speed with safety limits (RPM)"""
        if not self._available:
            print("Cannot command speed: Winch not available")
            return False
        safe_speed = float(self._apply_safety_limits(speed))
        msg = Float64()
        msg.data = safe_speed
        self._speed_rpm_pub.publish(msg)
        self._last_command_time = time.time()
        return True
    
    def command_speed_mmps(self, speed: float) -> bool:
        """Command winch speed in mm/s with clamping to ±max_speed"""
        if not self._available:
            print("Cannot command speed: Winch not available")
            return False
        clamped_speed = float(self._apply_safety_limits(speed))
        msg = Float64()
        msg.data = clamped_speed
        self._speed_mmps_pub.publish(msg)
        self._last_command_time = time.time()
        return True
    
    def move_increment(self, length_mm: int, speed_mm_s: int) -> bool:
        """Move winch by an increment (uses default acceleration of 30 RPM/s)"""
        if not self._available:
            print("Cannot move increment: Winch not available")
            return False
            
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            # acceleration_rpm_s will use message default (30 RPM/s)
            self._move_increment_pub.publish(msg)
            print(f'Moving winch by: {length_mm} mm at {speed_mm_s} mm/s')
            return True
        except Exception as e:
            print(f'Error moving winch: {e}')
            return False
    
    def move_increment_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        """Move winch by an increment with custom acceleration"""
        if not self._available:
            print("Cannot move increment: Winch not available")
            return False
            
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            msg.acceleration_rpm_s = int(acceleration_rpm_s)
            self._move_increment_pub.publish(msg)
            print(f'Moving winch by: {length_mm} mm at {speed_mm_s} mm/s with acceleration {acceleration_rpm_s} RPM/s')
            return True
        except Exception as e:
            print(f'Error moving winch: {e}')
            return False
        
    def move_absolute(self, length_mm: int, speed_mm_s: int) -> bool:
        """Move winch to an absolute position (uses default acceleration of 30 RPM/s)"""
        if not self._available:
            print("Cannot move absolute: Winch not available")
            return False
            
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            # acceleration_rpm_s will use message default (30 RPM/s)
            self._move_absolute_pub.publish(msg)
            print(f'Moving winch to: {length_mm} mm at {speed_mm_s} mm/s')
            return True
        except Exception as e:
            print(f'Error moving winch: {e}')
            return False
    
    def move_absolute_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int) -> bool:
        """Move winch to an absolute position with custom acceleration"""
        if not self._available:
            print("Cannot move absolute: Winch not available")
            return False
            
        try:
            msg = MoveWinchLength()
            msg.length_mm = int(length_mm)
            msg.speed_mm_s = int(speed_mm_s)
            msg.acceleration_rpm_s = int(acceleration_rpm_s)
            self._move_absolute_pub.publish(msg)
            print(f'Moving winch to: {length_mm} mm at {speed_mm_s} mm/s with acceleration {acceleration_rpm_s} RPM/s')
            return True
        except Exception as e:
            print(f'Error moving winch: {e}')
            return False
        
    def set_load_detection_mode(self, enable: bool):
        if not self.available:
            print("Cannot set load detection: Winch not available")

        try:
            msg = Bool()
            msg.data = enable
            self._load_detection_pub.publish(msg)
            print(f'Load detection mode set to: {enable}')
            return True
        except Exception as e:
            print(f'Error setting load detection mode: {e}')
            return False
    
    def _apply_safety_limits(self, speed: float) -> float:
        """Apply safety limits to winch speed"""
        return max(min(speed, self._max_speed), -self._max_speed)
    
    def _on_max_speed_changed(self, new_value: float):
        """Handle max_speed change from SettingsManager"""
        self._max_speed = new_value
        print(f"[WinchController] Max speed updated to: {new_value}")
    
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
           

    def get_load_detection_enabled(self) -> bool:
        return self._load_detection_enabled
    
    def set_load_detection_enabled(self, value: bool):
        if self._load_detection_enabled != value:
            self._load_detection_enabled = value
            self.load_detection_changed.emit()

    
    def get_unusual_load_detected(self) -> bool:
        return self._unusual_load_detected
    
    def set_unusual_load_detected(self, value: bool):
        if self._unusual_load_detected != value:
            self._unusual_load_detected = value
            self.unusual_load_detected_changed.emit()
    
    # Define Qt properties
    cable_length = Property(float, get_cable_length, set_cable_length, notify=cable_length_changed)
    cable_speed = Property(float, get_cable_speed, set_cable_speed, notify=cable_speed_changed)
    winch_torque = Property(float, get_winch_torque, set_winch_torque, notify=winch_torque_changed)
    motor_temperature = Property(float, get_motor_temperature, set_motor_temperature, notify=motor_temperature_changed)
    motor_voltage = Property(float, get_motor_voltage, set_motor_voltage, notify=motor_voltage_changed)
    motor_brake = Property(bool, get_motor_brake, set_motor_brake, notify=motor_brake_changed)
    available = Property(bool, get_available, notify=available_changed)
    enabled = Property(bool, get_enabled, set_enabled, notify=enabled_changed)
    load_detection_enabled = Property(bool, get_load_detection_enabled, set_load_detection_enabled, notify=load_detection_changed)
    unusual_load_detected = Property(bool, get_unusual_load_detected, notify=unusual_load_detected_changed)

    
    # Slot methods for QML
    @Slot(float)
    def setSpeed(self, speed: float):
        """Set winch speed from QML"""
        return self.command_speed_rpm(speed)
    
    @Slot(int, int)
    def moveIncrement(self, length_mm: int, speed_mm_s: int):
        """Move winch by increment from QML"""
        return self.move_increment(length_mm, speed_mm_s)
    
    @Slot(int, int)
    def moveAbsolute(self, length_mm: int, speed_mm_s: int):
        """Move winch to absolute position from QML"""
        return self.move_absolute(length_mm, speed_mm_s)
    
    @Slot(int, int, int)
    def moveIncrementWithAccel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int):
        """Move winch by increment with custom acceleration from QML"""
        return self.move_increment_with_accel(length_mm, speed_mm_s, acceleration_rpm_s)
    
    @Slot(int, int, int)
    def moveAbsoluteWithAccel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int):
        """Move winch to absolute position with custom acceleration from QML"""
        return self.move_absolute_with_accel(length_mm, speed_mm_s, acceleration_rpm_s)
    
    @Slot(bool)
    def setEnabled(self, enabled: bool):
        """Enable/disable winch from QML"""
        if not self._available:
            print("Cannot enable winch: Winch not available")
            return
        
         # Send command to enable/disable winch
        msg = Bool()
        msg.data = enabled
        self._enable_pub.publish(msg)
        print(f'Winch {"enabled" if enabled else "disabled"}')

    @Slot(bool)
    def setLoadDetectionEnabled(self, enabled: bool):
        """Enable/disable load detection from QML"""
        self.set_load_detection_mode(enabled)
        
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        if self._availability_timer.isActive():
            self._availability_timer.stop()
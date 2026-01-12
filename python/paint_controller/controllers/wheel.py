#!/usr/bin/env python3
import time
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import Bool
from paint_interfaces.msg import MoveVehicleSpd, MoveVehiclePos, VehicleStatus
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
    
    # New signals for motor error and availability
    left_error_changed = Signal()
    right_error_changed = Signal()
    left_motor_available_changed = Signal()
    right_motor_available_changed = Signal()
    
    # Error signal for emergency overlay (has_error: bool, message: str)
    error_state_changed = Signal(bool, str)

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
        
        # Motor error and availability states
        self._left_error = False
        self._right_error = False
        self._left_motor_available = False
        self._right_motor_available = False
        
        # Track last commanded speeds for unified command
        self._last_left_rpm = 0
        self._last_right_rpm = 0
        
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
        """Setup ROS publishers for vehicle control"""
        self._speed_cmd_pub = self._node.create_publisher(MoveVehicleSpd, 'vehicle/speed/cmd', 1)
        self._pos_cmd_pub = self._node.create_publisher(MoveVehiclePos, 'vehicle/position/cmd', 1)
        self._disable_pub = self._node.create_publisher(Bool, 'wheel/disable/cmd', 1)
        self._set_zero_pub = self._node.create_publisher(Bool, 'wheel/set_zero/cmd', 1)

    def _setup_subscribers(self):
        """Setup ROS subscribers for vehicle status"""
        self._status_sub = self._node.create_subscription(
            VehicleStatus,
            'vehicle/status',  
            self._status_callback,
            10  
        )
        print(f"Vehicle status subscriber set up on topic 'vehicle/status'")

    def _check_availability(self):
        """
        Periodically check if wheel controller is still connected based on time since last message
        and motor availability states from VehicleStatus.
        This runs on a timer to ensure we detect disconnections even when no new messages arrive.
        """
        current_time = time.time()
        
        # Calculate time since last status update
        time_since_last_update = current_time - self._last_status_update_time
        
        # Determine if available: must have recent messages AND both motors available
        is_connected = time_since_last_update <= self._connection_timeout
        motors_available = self._left_motor_available and self._right_motor_available
        new_available = is_connected and motors_available
        
        # Only emit if there's a change in availability
        if self._available != new_available:
            self._available = new_available
            self.available_changed.emit()
            if not new_available:
                if not is_connected:
                    print(f"Wheel controller considered disconnected: {time_since_last_update:.1f}s since last message")
                elif not motors_available:
                    print(f"Wheel controller unavailable: left_available={self._left_motor_available}, right_available={self._right_motor_available}")

    def _status_callback(self, msg: VehicleStatus):
        """Callback function for vehicle status messages"""
        try:
            # Update the last status time when any message is received
            current_time = time.time()
            self._last_status_update_time = current_time
            
            # Process motor availability states
            self._update_motor_availability(msg.left_available, msg.right_available)
            
            # Process motor error states
            self._update_error_states(msg.left_error, msg.right_error)
            
            # Check overall availability based on connection + motor states
            motors_available = self._left_motor_available and self._right_motor_available
            new_available = motors_available
            
            if self._available != new_available:
                self._available = new_available
                self.available_changed.emit()
                if new_available:
                    print("Wheel controller connection restored")
            
            # Process the status update
            self.update_status(msg)
        except Exception as e:
            print(f"Error in vehicle status callback: {e}")
    
    def _update_motor_availability(self, left_available: bool, right_available: bool):
        """Update motor availability states and emit signals if changed"""
        if self._left_motor_available != left_available:
            self._left_motor_available = left_available
            self.left_motor_available_changed.emit()
        
        if self._right_motor_available != right_available:
            self._right_motor_available = right_available
            self.right_motor_available_changed.emit()
    
    def _update_error_states(self, left_error: bool, right_error: bool):
        """Update motor error states and trigger emergency signal if errors detected"""
        prev_left_error = self._left_error
        prev_right_error = self._right_error
        
        if self._left_error != left_error:
            self._left_error = left_error
            self.left_error_changed.emit()
        
        if self._right_error != right_error:
            self._right_error = right_error
            self.right_error_changed.emit()
        
        # Emit error_state_changed signal when error transitions to True
        new_errors = []
        if left_error and not prev_left_error:
            new_errors.append("Left")
        if right_error and not prev_right_error:
            new_errors.append("Right")
        
        if new_errors:
            if len(new_errors) == 2:
                error_msg = "Both track motors error"
            else:
                error_msg = f"{new_errors[0]} track motor error"
            self.error_state_changed.emit(True, error_msg)

    def command_speed(self, left_rpm: int, right_rpm: int):
        """
        Command vehicle speed using unified MoveVehicleSpd message.
        
        Args:
            left_rpm: Left track RPM command
            right_rpm: Right track RPM command
        
        Returns:
            True if command was published
        """
        msg = MoveVehicleSpd()
        msg.left_rpm = int(left_rpm)
        msg.right_rpm = int(right_rpm)
        self._speed_cmd_pub.publish(msg)
        self._last_command_time = time.time()
        self._last_left_rpm = int(left_rpm)
        self._last_right_rpm = int(right_rpm)
        return True
    
    def command_position(self, left_mm: int, right_mm: int, rpm_limit: int, relative: bool = True):
        """
        Command vehicle position using MoveVehiclePos message.
        
        Args:
            left_mm: Left track travel distance in mm
            right_mm: Right track travel distance in mm
            rpm_limit: Maximum RPM limit for the movement
            relative: If True, distances are relative to current position
        
        Returns:
            True if command was published
        """
        msg = MoveVehiclePos()
        msg.left_travel_mm = int(left_mm)
        msg.right_travel_mm = int(right_mm)
        msg.rpm_limit = int(rpm_limit)
        msg.relative = relative
        self._pos_cmd_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def command_left_wheel_speed(self, speed: float):
        """
        Command left wheel speed. Uses unified command_speed internally.
        
        Args:
            speed: Left wheel RPM command
        
        Returns:
            True if command was published
        """
        self._last_left_rpm = int(speed)
        return self.command_speed(self._last_left_rpm, self._last_right_rpm)

    def command_right_wheel_speed(self, speed: float): 
        """
        Command right wheel speed. Uses unified command_speed internally.
        
        Args:
            speed: Right wheel RPM command
        
        Returns:
            True if command was published
        """
        self._last_right_rpm = int(speed)
        return self.command_speed(self._last_left_rpm, self._last_right_rpm)

    def update_status(self, msg: VehicleStatus):
        """
        Process incoming vehicle status messages and update properties with throttling
        """
        current_time = time.time()
        if current_time - self._last_update_time >= self._min_update_interval:
            self._last_update_time = current_time
            
            # Update property values from VehicleStatus
            self.set_left_wheel_speed(float(msg.left_speed))
            self.set_right_wheel_speed(float(msg.right_speed))
            self.set_left_wheel_current(float(msg.left_current))
            self.set_right_wheel_current(float(msg.right_current))
            self.set_left_wheel_position(float(msg.left_travel_mm))
            self.set_right_wheel_position(float(msg.right_travel_mm))

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
    
    # Getters for new error and motor availability states
    def get_left_error(self) -> bool:
        return self._left_error
    
    def get_right_error(self) -> bool:
        return self._right_error
    
    def get_left_motor_available(self) -> bool:
        return self._left_motor_available
    
    def get_right_motor_available(self) -> bool:
        return self._right_motor_available
    
    # Define Qt properties
    left_wheel_speed = Property(float, get_left_wheel_speed, set_left_wheel_speed, notify=left_wheel_speed_changed)
    right_wheel_speed = Property(float, get_right_wheel_speed, set_right_wheel_speed, notify=right_wheel_speed_changed)
    left_wheel_current = Property(float, get_left_wheel_current, set_left_wheel_current, notify=left_wheel_current_changed)
    right_wheel_current = Property(float, get_right_wheel_current, set_right_wheel_current, notify=right_wheel_current_changed)
    left_wheel_position = Property(float, get_left_wheel_position, set_left_wheel_position, notify=left_wheel_position_changed)
    right_wheel_position = Property(float, get_right_wheel_position, set_right_wheel_position, notify=right_wheel_position_changed)
    available = Property(bool, get_available, notify=available_changed)
    enabled = Property(bool, get_enabled, set_enabled, notify=enabled_changed)
    
    # New Qt properties for error and motor availability
    left_error = Property(bool, get_left_error, notify=left_error_changed)
    right_error = Property(bool, get_right_error, notify=right_error_changed)
    left_motor_available = Property(bool, get_left_motor_available, notify=left_motor_available_changed)
    right_motor_available = Property(bool, get_right_motor_available, notify=right_motor_available_changed)
    
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
    
    @Slot(int, int)
    def setSpeed(self, left_rpm: int, right_rpm: int):
        """Set both wheel speeds from QML using unified command"""
        return self.command_speed(left_rpm, right_rpm)
    
    @Slot(int, int, int, bool)
    def setPosition(self, left_mm: int, right_mm: int, rpm_limit: int, relative: bool):
        """Command position from QML"""
        return self.command_position(left_mm, right_mm, rpm_limit, relative)
    
    @Slot()
    def emergency_stop(self):
        """Emergency stop - immediately set both wheels to zero speed"""
        self.command_speed(0, 0)
        print('Wheel controller emergency stop activated')
    
    @Slot()
    def resetWheelPosition(self):
        """
        Reset both wheel positions to zero
        """
        msg = Bool()
        msg.data = True
        self._set_zero_pub.publish(msg)
        print('Wheel positions reset to zero')
        
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()
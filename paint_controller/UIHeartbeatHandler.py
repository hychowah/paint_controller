#!/usr/bin/env python3
import time
from enum import Enum
from typing import Dict
from rclpy.node import Node
from std_msgs.msg import UInt8
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer


class HeartbeatStatus(Enum):
    IDLE = 0x00      # System is off or not initialized
    ONTASK = 0x01    # Normal operation
    WARNING = 0x02   # Minor issue detected
    ERROR = 0x03     # Critical error
    CLEAR_ERROR = 0x04  # Command to clear error state


class UIHeartbeatHandler(QObject):
    """
    Qt-based handler for monitoring and managing robot heartbeats.
    Provides signals and slots for UI integration and status management.
    """
    
    # Signals for property changed notifications
    controller_status_changed = Signal()
    base_status_changed = Signal()
    ef_status_changed = Signal()
    controller_online_changed = Signal()
    base_online_changed = Signal()
    ef_online_changed = Signal()
    status_message_changed = Signal()
    
    def __init__(self, node: Node):
        """
        Initialize the heartbeat handler.
        
        Args:
            node: ROS node to attach publishers and subscribers to
        """
        super().__init__()
        self._node = node
        
        # Initialize property values
        self._controller_status = HeartbeatStatus.IDLE.value
        self._base_status = HeartbeatStatus.IDLE.value
        self._ef_status = HeartbeatStatus.IDLE.value
        self._controller_online = False
        self._base_online = False
        self._ef_online = False
        self._status_message = ""
        
        # Tracking variables
        self._controller_last_seen = 0.0
        self._base_last_seen = 0.0
        self._ef_last_seen = 0.0
        self._heartbeat_timeout = 1.0  # Time in seconds before considering disconnected
        
        # Setup publishers and subscribers
        self._setup_publishers()
        self._setup_subscribers()
        
        # Create availability check timer
        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)  # Check every 200ms
        
        self._node.get_logger().info('UIHeartbeatHandler initialized')
    
    def _setup_publishers(self):
        """Setup ROS publishers for heartbeat commands"""
        self._controller_heartbeat_pub = self._node.create_publisher(UInt8, '/controller/heartbeat', 10)
    
    def _setup_subscribers(self):
        """Setup ROS subscribers for heartbeat messages"""
        self._controller_heartbeat_sub = self._node.create_subscription(
            UInt8, 
            '/controller/heartbeat', 
            self._controller_heartbeat_callback,
            10
        )
        
        self._base_heartbeat_sub = self._node.create_subscription(
            UInt8, 
            '/base/heartbeat', 
            self._base_heartbeat_callback,
            10
        )
        
        self._ef_heartbeat_sub = self._node.create_subscription(
            UInt8, 
            '/ef/heartbeat', 
            self._ef_heartbeat_callback,
            10
        )
        
        self._node.get_logger().info('Heartbeat subscribers initialized')
    
    def _check_availability(self):
        """
        Periodically check if components are still connected based on time since last heartbeat
        This runs on a timer to ensure we detect disconnections even when no new messages arrive
        """
        current_time = time.time()
        
        # Check controller heartbeat
        if current_time - self._controller_last_seen > self._heartbeat_timeout:
            if self._controller_online:
                self.set_controller_online(False)
                self.set_status_message("Controller heartbeat lost")
                self._node.get_logger().warning('Controller heartbeat lost')
        
        # Check base heartbeat
        if current_time - self._base_last_seen > self._heartbeat_timeout:
            if self._base_online:
                self.set_base_online(False)
                self.set_status_message("Base heartbeat lost")
                self._node.get_logger().warning('Base heartbeat lost')
        
        # Check ef heartbeat
        if current_time - self._ef_last_seen > self._heartbeat_timeout:
            if self._ef_online:
                self.set_ef_online(False)
                self.set_status_message("EF heartbeat lost")
                self._node.get_logger().warning('EF heartbeat lost')
    
    def _controller_heartbeat_callback(self, msg: UInt8):
        """
        Process controller heartbeat messages
        
        Args:
            msg: UInt8 heartbeat message
        """
        try:
            # Update last seen time
            self._controller_last_seen = time.time()
            
            # Update online status if needed
            if not self._controller_online:
                self.set_controller_online(True)
                self.set_status_message("Controller heartbeat restored")
                self._node.get_logger().info('Controller heartbeat restored')
            
            # Update status if changed
            if self._controller_status != msg.data:
                self.set_controller_status(msg.data)
                status_str = self._status_to_string(msg.data)
                self._node.get_logger().info(f'Controller status changed to: {status_str}')
                
                # Update status message for UI
                if msg.data == HeartbeatStatus.WARNING.value:
                    self.set_status_message("Controller warning")
                elif msg.data == HeartbeatStatus.ERROR.value:
                    self.set_status_message("Controller error")
                
        except Exception as e:
            self._node.get_logger().error(f'Error in controller heartbeat callback: {str(e)}')
    
    def _base_heartbeat_callback(self, msg: UInt8):
        """
        Process base heartbeat messages
        
        Args:
            msg: UInt8 heartbeat message
        """
        try:
            # Update last seen time
            self._base_last_seen = time.time()
            
            # Update online status if needed
            if not self._base_online:
                self.set_base_online(True)
                self.set_status_message("Base heartbeat restored")
                self._node.get_logger().info('Base heartbeat restored')
            
            # Update status if changed
            if self._base_status != msg.data:
                self.set_base_status(msg.data)
                status_str = self._status_to_string(msg.data)
                self._node.get_logger().info(f'Base status changed to: {status_str}')
                
                # Update status message for UI
                if msg.data == HeartbeatStatus.WARNING.value:
                    self.set_status_message("Base warning")
                elif msg.data == HeartbeatStatus.ERROR.value:
                    self.set_status_message("Base error")
                
        except Exception as e:
            self._node.get_logger().error(f'Error in base heartbeat callback: {str(e)}')
    
    def _ef_heartbeat_callback(self, msg: UInt8):
        """
        Process ef heartbeat messages
        
        Args:
            msg: UInt8 heartbeat message
        """
        try:
            # Update last seen time
            self._ef_last_seen = time.time()
            
            # Update online status if needed
            if not self._ef_online:
                self.set_ef_online(True)
                self.set_status_message("EF heartbeat restored")
                self._node.get_logger().info('EF heartbeat restored')
            
            # Update status if changed
            if self._ef_status != msg.data:
                self.set_ef_status(msg.data)
                status_str = self._status_to_string(msg.data)
                self._node.get_logger().info(f'EF status changed to: {status_str}')
                
                # Update status message for UI
                if msg.data == HeartbeatStatus.WARNING.value:
                    self.set_status_message("EF warning")
                elif msg.data == HeartbeatStatus.ERROR.value:
                    self.set_status_message("EF error")
                
        except Exception as e:
            self._node.get_logger().error(f'Error in EF heartbeat callback: {str(e)}')
    
    # Property getters and setters
    def get_controller_status(self) -> int:
        return self._controller_status
    
    def set_controller_status(self, value: int):
        if self._controller_status != value:
            self._controller_status = value
            self.controller_status_changed.emit()
    
    def get_base_status(self) -> int:
        return self._base_status
    
    def set_base_status(self, value: int):
        if self._base_status != value:
            self._base_status = value
            self.base_status_changed.emit()
    
    def get_ef_status(self) -> int:
        return self._ef_status
    
    def set_ef_status(self, value: int):
        if self._ef_status != value:
            self._ef_status = value
            self.ef_status_changed.emit()
    
    def get_controller_online(self) -> bool:
        return self._controller_online
    
    def set_controller_online(self, value: bool):
        if self._controller_online != value:
            self._controller_online = value
            self.controller_online_changed.emit()
    
    def get_base_online(self) -> bool:
        return self._base_online
    
    def set_base_online(self, value: bool):
        if self._base_online != value:
            self._base_online = value
            self.base_online_changed.emit()
    
    def get_ef_online(self) -> bool:
        return self._ef_online
    
    def set_ef_online(self, value: bool):
        if self._ef_online != value:
            self._ef_online = value
            self.ef_online_changed.emit()
    
    def get_status_message(self) -> str:
        return self._status_message
    
    def set_status_message(self, value: str):
        if self._status_message != value:
            self._status_message = value
            self.status_message_changed.emit()
    
    # Define Qt properties
    controller_status = Property(int, get_controller_status, notify=controller_status_changed)
    base_status = Property(int, get_base_status, notify=base_status_changed)
    ef_status = Property(int, get_ef_status, notify=ef_status_changed)
    controller_online = Property(bool, get_controller_online, notify=controller_online_changed)
    base_online = Property(bool, get_base_online, notify=base_online_changed)
    ef_online = Property(bool, get_ef_online, notify=ef_online_changed)
    status_message = Property(str, get_status_message, notify=status_message_changed)
    
    # Helper methods for QML
    @Slot(str, result=bool)
    def is_component_online(self, component_name: str) -> bool:
        """
        Check if a component is online
        
        Args:
            component_name: Name of component to check ("controller", "base", or "ef")
            
        Returns:
            bool: True if component is online, False otherwise
        """
        if component_name == "controller":
            return self._controller_online
        elif component_name == "base":
            return self._base_online
        elif component_name == "ef":
            return self._ef_online
        else:
            return False
    
    @Slot(str, result=int)
    def get_component_status(self, component_name: str) -> int:
        """
        Get the status code of a component
        
        Args:
            component_name: Name of component to check ("controller", "base", or "ef")
            
        Returns:
            int: Status code
        """
        if component_name == "controller":
            return self._controller_status
        elif component_name == "base":
            return self._base_status
        elif component_name == "ef":
            return self._ef_status
        else:
            return HeartbeatStatus.IDLE.value
    
    @Slot(str, result=str)
    def get_status_string(self, component_name: str) -> str:
        """
        Get a string representation of a component's status
        
        Args:
            component_name: Name of component ("controller", "base", or "ef")
            
        Returns:
            str: Status string
        """
        status_code = self.get_component_status(component_name)
        return self._status_to_string(status_code)
    
    @Slot(str, result=str)
    def get_status_color(self, component_name: str) -> str:
        """
        Get a color string for UI display based on component status
        
        Args:
            component_name: Name of component ("controller", "base", or "ef")
            
        Returns:
            str: Color string ("blue", "green", "yellow", "red", or "gray")
        """
        # If not online, return gray
        if not self.is_component_online(component_name):
            return "gray"
        
        # Return color based on status
        status_code = self.get_component_status(component_name)
        
        if status_code == HeartbeatStatus.IDLE.value:
            return "blue"
        elif status_code == HeartbeatStatus.ONTASK.value:
            return "green"
        elif status_code == HeartbeatStatus.WARNING.value:
            return "yellow"
        elif status_code == HeartbeatStatus.ERROR.value:
            return "red"
        
        return "gray"
    
    def _status_to_string(self, status_code: int) -> str:
        """
        Convert status code to string representation
        
        Args:
            status_code: Numeric status code
            
        Returns:
            str: String representation of status
        """
        status_map = {
            HeartbeatStatus.IDLE.value: "IDLE",
            HeartbeatStatus.ONTASK.value: "ONTASK",
            HeartbeatStatus.WARNING.value: "WARNING",
            HeartbeatStatus.ERROR.value: "ERROR",
            HeartbeatStatus.CLEAR_ERROR.value: "CLEAR_ERROR"
        }
        return status_map.get(status_code, f"UNKNOWN({status_code})")
    
    @Slot()
    def clear_error_state(self):
        """
        Send command to clear error/warning states
        """
        self._node.get_logger().info('Attempting to clear error/warning state')
        
        # Publish CLEAR_ERROR command
        msg = UInt8()
        msg.data = HeartbeatStatus.CLEAR_ERROR.value
        self._controller_heartbeat_pub.publish(msg)
        
        # Update status message
        self.set_status_message("Clearing errors...")
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()
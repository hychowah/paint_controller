#!/usr/bin/env python3
"""
ESP32 Valve Controller

This module provides ROS2 integration for the ESP32-based UDP valve controller.
It handles network discovery, UDP communication, status publishing, and command subscription.
"""

import socket
import struct
import subprocess
import re
import time
from typing import Optional, Dict
from enum import IntEnum

from rclpy.node import Node
from std_msgs.msg import Float32
from paint_interfaces.msg import ValveStatus
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QThread


class MessageType(IntEnum):
    """UDP message type identifiers"""
    VALVE_STATUS = 0x00  # Status message from ESP32
    MOVE_VEL = 0x11      # Velocity control command
    TURN_VALVE = 0x12    # Position control command


class UDPReceiveThread(QThread):
    """Thread for receiving UDP status messages from ESP32"""
    status_received = Signal(dict)
    connection_lost = Signal()
    
    def __init__(self, sock: socket.socket, parent=None):
        super().__init__(parent)
        self.sock = sock
        self._running = True
        self._last_receive_time = 0
        
    def run(self):
        """Main thread loop for receiving UDP messages"""
        START_BYTE = 0xAA
        CRC_POLYNOMIAL = 0x07
        CRC_INIT = 0xFF
        
        while self._running:
            try:
                # Non-blocking receive with short timeout
                data, addr = self.sock.recvfrom(1024)
                
                # Validate message
                if not self._validate_message(data, START_BYTE, CRC_POLYNOMIAL, CRC_INIT):
                    continue
                
                if data[1] != MessageType.VALVE_STATUS:
                    continue
                
                if len(data) != 15:
                    continue
                
                # Parse status message
                motor_current = struct.unpack('<h', data[2:4])[0]
                valve_pos = struct.unpack('<h', data[4:6])[0]
                flow_rate = struct.unpack('<h', data[6:8])[0]
                total_volume = struct.unpack('<i', data[8:12])[0]
                motor_connected = bool(data[12])
                flow_connected = bool(data[13])
                
                status = {
                    'motor_current': motor_current,
                    'valve_position_raw': valve_pos,
                    'valve_position': valve_pos / 100.0,  # 0-10000 → 0-100%
                    'flow_rate': flow_rate / 100.0,
                    'total_volume': total_volume / 100.0,
                    'motor_connected': motor_connected,
                    'flow_connected': flow_connected,
                    'timestamp': time.time()
                }
                
                self._last_receive_time = time.time()
                self.status_received.emit(status)
                
            except socket.timeout:
                # Check for connection timeout
                if self._last_receive_time > 0 and (time.time() - self._last_receive_time) > 1.0:
                    self.connection_lost.emit()
                    self._last_receive_time = 0
                continue
            except Exception as e:
                print(f"UDP receive error: {e}")
                time.sleep(0.1)
    
    def _validate_message(self, data: bytes, start_byte: int, polynomial: int, init: int) -> bool:
        """Validate message structure and CRC"""
        if len(data) < 3 or data[0] != start_byte:
            return False
        
        # Calculate CRC
        crc = init
        for byte in data[:-1]:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ polynomial) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        
        return crc == data[-1]
    
    def stop(self):
        """Stop the receive thread"""
        self._running = False


class ESP32ValveController(QObject):
    """
    ROS2 controller for ESP32 valve system
    
    Handles UDP communication, ARP-based discovery, status publishing,
    and command subscription for the ESP32 valve controller.
    """
    
    # Qt signals for property changes
    valve_position_changed = Signal()
    valve_rate_changed = Signal()
    total_volume_changed = Signal()
    valve_motor_current_changed = Signal()
    valve_motor_connected_changed = Signal()
    flow_meter_connected_changed = Signal()
    esp32_connected_changed = Signal()
    
    # UDP protocol constants
    START_BYTE = 0xAA
    CRC_POLYNOMIAL = 0x07
    CRC_INIT = 0xFF
    RECEIVE_PORT = 8888  # ESP32 receives commands
    SEND_PORT = 8889     # ESP32 sends status
    
    # Network configuration
    ESP32_MAC = "1c:db:d4:40:30:c8"
    ESP32_IP_FALLBACK = "192.168.101.102"
    
    def __init__(self, node: Node):
        super().__init__()
        self._node = node
        
        # Initialize properties
        self._valve_position = 0.0
        self._valve_rate = 0.0
        self._total_volume = 0.0
        self._valve_motor_current = 0
        self._valve_motor_connected = False
        self._flow_meter_connected = False
        self._esp32_connected = False
        
        # Command tracking
        self._last_command = 0.0
        self._last_command_time = 0.0
        
        # Network state
        self._esp32_ip = None
        self._sock = None
        self._udp_thread = None
        
        # Throttle variables
        self._last_publish_time = 0
        self._min_publish_interval = 0.2  # 5Hz = 200ms
        
        # Setup ROS communication
        self._setup_publishers()
        self._setup_subscribers()
        
        # Start network discovery
        self._discover_and_connect()
        
        # Create timers
        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.timeout.connect(self._check_reconnect)
        self._reconnect_timer.start(5000)  # Check every 5s
        
        self._keepalive_timer = QTimer(self)
        self._keepalive_timer.timeout.connect(self._send_keepalive)
        self._keepalive_timer.start(1000)  # Check every 1s
        
        self._publish_timer = QTimer(self)
        self._publish_timer.timeout.connect(self._publish_status)
        self._publish_timer.start(200)  # Publish at 5Hz
    
    def _setup_publishers(self):
        """Setup ROS publishers"""
        self._status_pub = self._node.create_publisher(
            ValveStatus, 'valve/status', 10
        )
    
    def _setup_subscribers(self):
        """Setup ROS subscribers"""
        self._cmd_sub = self._node.create_subscription(
            Float32, 'valve/turn/cmd', self._command_callback, 10
        )
    
    def _command_callback(self, msg: Float32):
        """Handle valve turn command"""
        # Clamp to 0-100% range
        position_pct = max(0.0, min(100.0, msg.data))
        
        # Convert to 0-1000 range for ESP32
        position_raw = int(position_pct * 10.0)
        
        # Send command
        self._send_turn_valve(position_raw)
        
        # Update command tracking
        self._last_command = position_pct
        self._last_command_time = time.time()
    
    def _discover_esp32_ip(self) -> Optional[str]:
        """
        Discover ESP32 IP via ARP lookup
        
        Uses 'arp -a' to find device by MAC address, falls back to
        hardcoded IP if not found.
        
        Returns:
            ESP32 IP address or None if not found
        """
        try:
            # Run arp -a command
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode != 0:
                return self.ESP32_IP_FALLBACK
            
            # Parse ARP output for MAC address (case-insensitive, flexible separators)
            mac_pattern = self.ESP32_MAC.replace(':', '[:-]?')
            pattern = rf'(\d+\.\d+\.\d+\.\d+).*?{mac_pattern}'
            
            for line in result.stdout.splitlines():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    ip = match.group(1)
                    print(f"Found ESP32 at {ip} via ARP")
                    return ip
            
            # Not found in ARP table, use fallback
            print(f"ESP32 MAC not found in ARP, using fallback IP {self.ESP32_IP_FALLBACK}")
            return self.ESP32_IP_FALLBACK
            
        except Exception as e:
            print(f"ARP discovery failed: {e}, using fallback IP")
            return self.ESP32_IP_FALLBACK
    
    def _discover_and_connect(self):
        """Discover ESP32 and establish UDP connection"""
        # Discover IP
        self._esp32_ip = self._discover_esp32_ip()
        if not self._esp32_ip:
            return
        
        # Create UDP socket
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.settimeout(0.1)  # 100ms timeout for non-blocking
            self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Bind to send port
            try:
                self._sock.bind(('0.0.0.0', self.SEND_PORT))
            except OSError:
                # Port in use, bind to any port
                self._sock.bind(('', 0))
            
            # Start receive thread
            self._udp_thread = UDPReceiveThread(self._sock, self)
            self._udp_thread.status_received.connect(self._handle_status)
            self._udp_thread.connection_lost.connect(self._handle_connection_lost)
            self._udp_thread.start()
            
            print(f"ESP32 Valve Controller connected to {self._esp32_ip}")
            
        except Exception as e:
            print(f"Failed to create UDP socket: {e}")
            self._sock = None
    
    def _handle_status(self, status: Dict):
        """Handle received status from UDP thread"""
        # Update properties
        self._valve_position = status['valve_position']
        self._valve_rate = status['flow_rate']
        self._total_volume = status['total_volume']
        self._valve_motor_current = status['motor_current']
        self._valve_motor_connected = status['motor_connected']
        self._flow_meter_connected = status['flow_connected']
        
        # Update connection status
        if not self._esp32_connected:
            self._esp32_connected = True
            self.esp32_connected_changed.emit()
        
        # Emit property change signals
        self.valve_position_changed.emit()
        self.valve_rate_changed.emit()
        self.total_volume_changed.emit()
        self.valve_motor_current_changed.emit()
        self.valve_motor_connected_changed.emit()
        self.flow_meter_connected_changed.emit()
    
    def _handle_connection_lost(self):
        """Handle connection timeout"""
        if self._esp32_connected:
            self._esp32_connected = False
            self.esp32_connected_changed.emit()
            print("ESP32 connection lost")
    
    def _check_reconnect(self):
        """Periodically check and attempt reconnection"""
        if not self._esp32_connected:
            print("Attempting to reconnect to ESP32...")
            self._disconnect()
            self._discover_and_connect()
    
    def _send_keepalive(self):
        """Send keepalive command if no recent commands"""
        if not self._esp32_connected:
            return
        
        # Only send keepalive if no command in last 1 second
        if time.time() - self._last_command_time >= 1.0:
            position_raw = int(self._last_command * 10.0)
            self._send_turn_valve(position_raw)
    
    def _publish_status(self):
        """Publish valve status to ROS topic at 5Hz"""
        current_time = time.time()
        
        # Throttle to 5Hz
        if current_time - self._last_publish_time < self._min_publish_interval:
            return
        
        msg = ValveStatus()
        msg.valve_motor_current = self._valve_motor_current
        msg.valve_position = self._valve_position
        msg.valve_rate = self._valve_rate
        msg.total_volume = self._total_volume
        msg.valve_motor_connected = self._valve_motor_connected
        msg.flow_meter_connected = self._flow_meter_connected
        
        self._status_pub.publish(msg)
        self._last_publish_time = current_time
    
    def _calculate_crc8(self, data: bytes) -> int:
        """Calculate CRC8 checksum"""
        crc = self.CRC_INIT
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ self.CRC_POLYNOMIAL) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc
    
    def _build_message(self, msg_type: MessageType, payload: bytes) -> bytes:
        """Build complete UDP message with CRC"""
        message = bytes([self.START_BYTE, msg_type]) + payload
        crc = self._calculate_crc8(message)
        return message + bytes([crc])
    
    def _send_turn_valve(self, position: int):
        """Send TURN_VALVE command to ESP32"""
        if not self._sock or not self._esp32_ip:
            return
        
        try:
            # Clamp to 0-1000 range
            position = max(0, min(1000, position))
            
            # Build message
            payload = struct.pack('<i', position)
            message = self._build_message(MessageType.TURN_VALVE, payload)
            
            # Send to ESP32
            self._sock.sendto(message, (self._esp32_ip, self.RECEIVE_PORT))
            
        except Exception as e:
            print(f"Failed to send valve command: {e}")
    
    @Slot(float)
    def setValveTurn(self, position_pct: float):
        """
        QML-callable method to set valve position
        
        Args:
            position_pct: Target position in percent (0.0-100.0)
        """
        # Clamp to valid range
        position_pct = max(0.0, min(100.0, position_pct))
        
        # Convert to raw 0-1000 range
        position_raw = int(position_pct * 10.0)
        
        # Send command
        self._send_turn_valve(position_raw)
        
        # Update tracking
        self._last_command = position_pct
        self._last_command_time = time.time()
    
    def _disconnect(self):
        """Disconnect and cleanup resources"""
        if self._udp_thread:
            self._udp_thread.stop()
            self._udp_thread.wait(1000)
            self._udp_thread = None
        
        if self._sock:
            self._sock.close()
            self._sock = None
        
        self._esp32_ip = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self._disconnect()
    
    # Qt Properties for QML binding
    valve_position = Property(float, lambda self: self._valve_position, notify=valve_position_changed)
    valve_rate = Property(float, lambda self: self._valve_rate, notify=valve_rate_changed)
    total_volume = Property(float, lambda self: self._total_volume, notify=total_volume_changed)
    valve_motor_current = Property(int, lambda self: self._valve_motor_current, notify=valve_motor_current_changed)
    valve_motor_connected = Property(bool, lambda self: self._valve_motor_connected, notify=valve_motor_connected_changed)
    flow_meter_connected = Property(bool, lambda self: self._flow_meter_connected, notify=flow_meter_connected_changed)
    esp32_connected = Property(bool, lambda self: self._esp32_connected, notify=esp32_connected_changed)

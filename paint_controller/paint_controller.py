#!/usr/bin/env python3

import sys
import os
import time
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable
import yaml

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Float64, Bool
from sensor_msgs.msg import LaserScan
from cv_bridge import CvBridge
from towngas_interfaces.msg import WinchStatus, WheelStatus, SteamDeckInput

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickImageProvider

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp

#############################################
### Configuration
#############################################

@dataclass
class RobotConfig:
    """Robot configuration parameters"""
    video_port: int = 5000
    update_rate: float = 100.0  # Hz
    watchdog_timeout: float = 1.0  # seconds
    joystick_deadzone: float = 2400.0
    max_winch_speed: float = 1000.0
    video_width: int = 640
    video_height: int = 480

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> RobotConfig:
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return RobotConfig(**config_dict)
        except Exception as e:
            print(f"Error loading config: {e}")
            return RobotConfig()
        

#############################################
### UI Data Model
#############################################

class UIDataModel(QObject):
    # Motor Status Signals
    winchLengthChanged = Signal(str)
    winchSpeedChanged = Signal(str)
    winchCurrentChanged = Signal(str)
    winchAvailableChanged = Signal(bool)
    winchTorqueChanged = Signal(str)
    winchTemperatureChanged = Signal(str)
    winchVoltageChanged = Signal(str)
    winchBrakeChanged = Signal(bool)
    winchEnabledChanged = Signal(bool)
    
    # Wheel Status Signals
    leftSpeedChanged = Signal(str)
    leftCurrentChanged = Signal(str)
    rightCurrentChanged = Signal(str)
    rightSpeedChanged = Signal(str)
    wheelAvailableChanged = Signal(bool)
    
    # Control Mode Signals
    leftJoystickControlChanged = Signal(str)
    rightJoystickControlChanged = Signal(str)

    # Input Signals
    leftJoystickXChanged = Signal(int)
    leftJoystickYChanged = Signal(int)
    rightJoystickXChanged = Signal(int)
    rightJoystickYChanged = Signal(int)
    leftTriggerChanged = Signal(int)
    rightTriggerChanged = Signal(int)
    dpadUpChanged = Signal(bool)
    dpadDownChanged = Signal(bool)
    dpadLeftChanged = Signal(bool)
    dpadRightChanged = Signal(bool)
    buttonAChanged = Signal(bool)
    buttonBChanged = Signal(bool)
    buttonXChanged = Signal(bool)
    buttonYChanged = Signal(bool)
    buttonL1Changed = Signal(bool)
    buttonR1Changed = Signal(bool)
    buttonMenuChanged = Signal(bool)

    
    def __init__(self):
        super().__init__()
        self._winch_data = {
            'length': '0.00',
            'speed': '0.00',
            'current': '0.00',
            'available': False,
            'torque': '0.00',
            'temperature': '0.00',
            'voltage': '0.00',
            'brake': False,
            'enabled': False
        }
        
        self._wheel_data = {
            'left_speed': '0.00',
            'right_speed': '0.00',
            'left_current': '0.00',
            'right_current': '0.00',
            'available': False
        }

        self.winch_enabled = False
        
        self._control_modes = {
            'left_joystick': 'None',
            'right_joystick': 'None'
        }

        self._input_state = {
            'left_stick': {'x': 0, 'y': 0},
            'right_stick': {'x': 0, 'y': 0},
            'triggers': {'left': 0, 'right': 0},
            'dpad': {
                'up': False,
                'down': False,
                'left': False,
                'right': False
            },
            'buttons': {
                'a': False,
                'b': False,
                'x': False,
                'y': False,
                'l1': False,
                'r1': False,
                'menu': False
            }
        }

    # Winch Properties
    @Property(str, notify=winchLengthChanged)
    def winch_length(self):
        return self._winch_data['length']
    
    @winch_length.setter
    def winch_length(self, value):
        if self._winch_data['length'] != value:
            self._winch_data['length'] = value
            self.winchLengthChanged.emit(value)

    @Property(bool, notify=winchAvailableChanged)
    def winch_available(self):
        return self._winch_data['available']
    
    @winch_available.setter
    def winch_available(self, value):
        if self._winch_data['available'] != value:
            self._winch_data['available'] = value
            self.winchAvailableChanged.emit(value)

    # Similar properties for other winch attributes...
    @Property(str, notify=winchSpeedChanged)
    def winch_speed(self):
        return self._winch_data['speed']
    
    @winch_speed.setter
    def winch_speed(self, value):
        if self._winch_data['speed'] != value:
            self._winch_data['speed'] = value
            self.winchSpeedChanged.emit(value)
    
    @Property(str, notify=winchCurrentChanged)
    def winch_current(self):
        return self._winch_data['current']
    
    @winch_current.setter
    def winch_current(self, value):
        if self._winch_data['current'] != value:
            self._winch_data['current'] = value
            self.winchCurrentChanged.emit(value)
    
    @Property(str, notify=winchTorqueChanged)
    def winch_torque(self):
        return self._winch_data['torque']
    
    @winch_torque.setter
    def winch_torque(self, value):
        if self._winch_data['torque'] != value:
            self._winch_data['torque'] = value
            self.winchTorqueChanged.emit(value)

    @Property(str, notify=winchTemperatureChanged)
    def winch_temperature(self):
        return self._winch_data['temperature']
    
    @winch_temperature.setter
    def winch_temperature(self, value):
        if self._winch_data['temperature'] != value:
            self._winch_data['temperature'] = value
            self.winchTemperatureChanged.emit(value)
    
    @Property(str, notify=winchVoltageChanged)
    def winch_voltage(self):
        return self._winch_data['voltage']
    
    @winch_voltage.setter
    def winch_voltage(self, value):
        if self._winch_data['voltage'] != value:
            self._winch_data['voltage'] = value
            self.winchVoltageChanged.emit(value)

    @Property(bool, notify=winchBrakeChanged)
    def winch_brake(self):
        return self._winch_data['brake']
    
    @winch_brake.setter
    def winch_brake(self, value):
        if self._winch_data['brake'] != value:
            self._winch_data['brake'] = value
            self.winchBrakeChanged.emit(value)

    # Wheel Properties
    @Property(str, notify=leftSpeedChanged)
    def left_wheel_speed(self):
        return self._wheel_data['left_speed']
    
    @left_wheel_speed.setter
    def left_wheel_speed(self, value):
        if self._wheel_data['left_speed'] != value:
            self._wheel_data['left_speed'] = value
            self.leftSpeedChanged.emit(value)

    # Control Mode Properties
    @Property(str, notify=leftJoystickControlChanged)
    def left_joystick_control(self):
        return self._control_modes['left_joystick']
    
    @left_joystick_control.setter
    def left_joystick_control(self, value):
        if self._control_modes['left_joystick'] != value:
            self._control_modes['left_joystick'] = value
            self.leftJoystickControlChanged.emit(value)

    @Property(str, notify=rightJoystickControlChanged)
    def right_joystick_control(self):
        return self._control_modes['right_joystick']
    
    @right_joystick_control.setter
    def right_joystick_control(self, value):
        if self._control_modes['right_joystick'] != value:
            self._control_modes['right_joystick'] = value
            self.rightJoystickControlChanged.emit(value)

    # Input Properties
    @Property(int, notify=leftJoystickXChanged)
    def left_joystick_x(self):
        return self._input_state['left_stick']['x']
    
    @left_joystick_x.setter
    def left_joystick_x(self, value):
        if self._input_state['left_stick']['x'] != value:
            self._input_state['left_stick']['x'] = value
            self.leftJoystickXChanged.emit(value)

    @Property(int, notify=leftJoystickYChanged)
    def left_joystick_y(self):
        return self._input_state['left_stick']['y']
    
    @left_joystick_y.setter
    def left_joystick_y(self, value):
        if self._input_state['left_stick']['y'] != value:
            self._input_state['left_stick']['y'] = value
            self.leftJoystickYChanged.emit(value)

    @Property(int, notify=rightJoystickXChanged)
    def right_joystick_x(self):
        return self._input_state['right_stick']['x']
    
    @right_joystick_x.setter
    def right_joystick_x(self, value):
        if self._input_state['right_stick']['x'] != value:
            self._input_state['right_stick']['x'] = value
            self.rightJoystickXChanged.emit(value)

    @Property(int, notify=rightJoystickYChanged)
    def right_joystick_y(self):
        return self._input_state['right_stick']['y']
    
    @right_joystick_y.setter
    def right_joystick_y(self, value):
        if self._input_state['right_stick']['y'] != value:
            self._input_state['right_stick']['y'] = value
            self.rightJoystickYChanged.emit(value)

    @Property(int, notify=leftTriggerChanged)
    def left_trigger(self):
        return self._input_state['triggers']['left']
    
    @left_trigger.setter
    def left_trigger(self, value):
        if self._input_state['triggers']['left'] != value:
            self._input_state['triggers']['left'] = value
            self.leftTriggerChanged.emit(value)

    @Property(int, notify=rightTriggerChanged)
    def right_trigger(self):
        return self._input_state['triggers']['right']
    
    @right_trigger.setter
    def right_trigger(self, value):
        if self._input_state['triggers']['right'] != value:
            self._input_state['triggers']['right'] = value
            self.rightTriggerChanged.emit(value)

    @Property(bool, notify=dpadUpChanged)
    def dpad_up(self):
        return self._input_state['dpad']['up']
    
    @dpad_up.setter
    def dpad_up(self, value):
        if self._input_state['dpad']['up'] != value:
            self._input_state['dpad']['up'] = value
            self.dpadUpChanged.emit(value)

    @Property(bool, notify=dpadDownChanged)
    def dpad_down(self):
        return self._input_state['dpad']['down']
    
    @dpad_down.setter
    def dpad_down(self, value):
        if self._input_state['dpad']['down'] != value:
            self._input_state['dpad']['down'] = value
            self.dpadDownChanged.emit(value)

    @Property(bool, notify=dpadLeftChanged)
    def dpad_left(self):
        return self._input_state['dpad']['left']
    
    @dpad_left.setter
    def dpad_left(self, value):
        if self._input_state['dpad']['left'] != value:
            self._input_state['dpad']['left'] = value
            self.dpadLeftChanged.emit(value)

    @Property(bool, notify=dpadRightChanged)
    def dpad_right(self):
        return self._input_state['dpad']['right']
    
    @dpad_right.setter
    def dpad_right(self, value):
        if self._input_state['dpad']['right'] != value:
            self._input_state['dpad']['right'] = value
            self.dpadRightChanged.emit(value)

    @Property(bool, notify=buttonAChanged)
    def button_a(self):
        return self._input_state['buttons']['a']
    
    @button_a.setter
    def button_a(self, value):
        if self._input_state['buttons']['a'] != value:
            self._input_state['buttons']['a'] = value
            self.buttonAChanged.emit(value)

    @Property(bool, notify=buttonBChanged)
    def button_b(self):
        return self._input_state['buttons']['b']
    
    @button_b.setter
    def button_b(self, value):
        if self._input_state['buttons']['b'] != value:
            self._input_state['buttons']['b'] = value
            self.buttonBChanged.emit(value)

    @Property(bool, notify=buttonXChanged)
    def button_x(self):
        return self._input_state['buttons']['x']
    
    @button_x.setter
    def button_x(self, value):
        if self._input_state['buttons']['x'] != value:
            self._input_state['buttons']['x'] = value
            self.buttonXChanged.emit(value)

    @Property(bool, notify=buttonYChanged)
    def button_y(self):
        return self._input_state['buttons']['y']
    
    @button_y.setter
    def button_y(self, value):
        if self._input_state['buttons']['y'] != value:
            self._input_state['buttons']['y'] = value
            self.buttonYChanged.emit(value)

    @Property(bool, notify=buttonL1Changed)
    def button_l1(self):
        return self._input_state['buttons']['l1']
    
    @button_l1.setter
    def button_l1(self, value):
        if self._input_state['buttons']['l1'] != value:
            self._input_state['buttons']['l1'] = value
            self.buttonL1Changed.emit(value)

    @Property(bool, notify=buttonR1Changed)
    def button_r1(self):
        return self._input_state['buttons']['r1']
    
    @button_r1.setter
    def button_r1(self, value):
        if self._input_state['buttons']['r1'] != value:
            self._input_state['buttons']['r1'] = value
            self.buttonR1Changed.emit(value)

    @Property(bool, notify=buttonMenuChanged)
    def button_menu(self):
        return self._input_state['buttons']['menu']
    
    @button_menu.setter
    def button_menu(self, value):
        if self._input_state['buttons']['menu'] != value:
            self._input_state['buttons']['menu'] = value
            self.buttonMenuChanged.emit(value)

    

#############################################
### Video Streaming
#############################################

class ImageProvider(QQuickImageProvider):
    def __init__(self, width: int, height: int):
        super().__init__(QQuickImageProvider.Image)
        self._width = width
        self._height = height
        self._format = QImage.Format_RGB888
        self.image = QImage(self._width, self._height, self._format)
        self._lock = threading.Lock()

    def update_image(self, new_image: QImage):
        with self._lock:
            self.image = new_image.copy()

    def requestImage(self, id: str, size, requestedSize) -> QImage:
        with self._lock:
            return self.image

class VideoStream:
    def __init__(self, port: int):
        Gst.init(None)
        self.pipeline = Gst.parse_launch(
            f"udpsrc port={port} caps=\"application/x-rtp, media=(string)video, "
            f"clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" "
            f"! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
        )
        self.sink = self.pipeline.get_by_name('sink')
        self.sink.set_property('emit-signals', True)
        
    def start(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        
    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def connect_new_sample_callback(self, callback: Callable):
        self.sink.connect('new-sample', callback)

#############################################
### Motor Control
#############################################

class MotorControllerBase:
    def __init__(self):
        self._enabled = False
        self._status = {}
        self._last_command_time = 0
        self._watchdog_timeout = 1.0

    @property
    def is_enabled(self) -> bool:
        return self._enabled and self._check_watchdog()

    def _check_watchdog(self) -> bool:
        return time.time() - self._last_command_time < self._watchdog_timeout

class WinchController(MotorControllerBase):
    def __init__(self, node: Node, max_speed: float):
        super().__init__()
        self._node = node
        self._max_speed = max_speed
        self._setup_publishers()
        self._status_callbacks = []

    def _setup_publishers(self):
        self._speed_pub = self._node.create_publisher(Float64, 'winch/cmd_speed', 1)
        self._enable_pub = self._node.create_publisher(Bool, 'winch/enable', 1)

    def command_speed(self, speed: float) -> bool:
        safe_speed = self._apply_safety_limits(speed)
        msg = Float64()
        msg.data = safe_speed
        self._speed_pub.publish(msg)
        self._last_command_time = time.time()
        return True

    def _apply_safety_limits(self, speed: float) -> float:
        return max(min(speed, self._max_speed), -self._max_speed)

    def update_status(self, msg: WinchStatus):
        self._status = {
            'cable_length': f"{msg.cable_length:.2f}",
            'cable_speed': f"{msg.cable_speed:.2f}",
            'winch_torque': f"{msg.winch_torque:.2f}",
            'motor_temperature': f"{msg.motor_temperature:.1f}",
            'motor_voltage': f"{msg.motor_voltage:.1f}",
            'motor_brake': msg.motor_brake,
            'available': msg.available
        }
        for callback in self._status_callbacks:
            callback(self._status)

    def get_status(self) -> Dict:
        return self._status

#############################################
### Input Handling
#############################################

class InputDevice(Enum):
    STEAM_DECK = auto()
    KEYBOARD = auto()
    GAMEPAD = auto()

class InputManager:
    def __init__(self):
        self._handlers = {}
        self._active_device = None
        self._callbacks = {}

    def register_device(self, device: InputDevice, handler: Any):
        self._handlers[device] = handler

    def set_active_device(self, device: InputDevice):
        if device not in self._handlers:
            raise ValueError(f"Device {device} not registered")
        self._active_device = device

    def register_callback(self, event_type: str, callback: Callable):
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

class SteamDeckHandler:
    def __init__(self, deadzone: float):
        self._deadzone = deadzone
        self._input_state = {}
        self._callbacks = {}

    def process_input(self, msg: SteamDeckInput):
        new_state = {
            'left_stick': self._process_stick(msg.left_stick_x, msg.left_stick_y),
            'right_stick': self._process_stick(msg.right_stick_x, msg.right_stick_y),
            'triggers': {
                'left': msg.left_trigger,
                'right': msg.right_trigger
            },
            'dpad': {
                'up': msg.dpad_up,
                'down': msg.dpad_down,
                'left': msg.dpad_left,
                'right': msg.dpad_right
            },
            'buttons': {
                'a': msg.a,
                'b': msg.b,
                'x': msg.x,
                'y': msg.y,
                'l1': msg.l1,
                'r1': msg.r1,
                'menu': msg.menu
            }
        }
        
        self._input_state = new_state

    def _process_stick(self, x: float, y: float) -> Dict[str, float]:
        magnitude = (x*x + y*y)**0.5
        if magnitude < self._deadzone:
            return {'x': 0, 'y': 0}
        
        scale = (magnitude - self._deadzone) / (32768 - self._deadzone)
        return {
            'x': x,
            'y': y
        }

    def _detect_changes(self, new_state: Dict) -> Dict[str, Any]:
        changes = {}
        for key in new_state:
            if key not in self._input_state or new_state[key] != self._input_state[key]:
                changes[key] = new_state[key]
        return changes
    
    def get_current_state(self) -> Dict:
        """Get current input state"""
        return self._input_state

    def has_new_input(self) -> bool:
        """Check if there are new inputs to process"""
        return bool(self._detect_changes(self._input_state))

#############################################
### ROS Integration
#############################################

class RosThread(QThread):
    error_occurred = Signal(str)
    node_started = Signal()
    node_stopped = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self._running = False
        self._shutdown_requested = False

    def run(self):
        try:
            self._running = True
            self.node_started.emit()
            
            while not self._shutdown_requested:
                if not rclpy.ok():
                    raise RuntimeError("ROS context is not valid")
                rclpy.spin_once(self.node, timeout_sec=0.1)
                
            self._cleanup()
            
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self._running = False
            self.node_stopped.emit()

    def request_shutdown(self):
        self._shutdown_requested = True

    def _cleanup(self):
        if self.node:
            self.node.destroy_node()

#############################################
### Main Controller
#############################################

class RobotController(Node, QObject):
    frame_ready = Signal()
    new_scan_data = Signal(list, float, float, float, float)
    status_updated = Signal()

    def __init__(self, config: RobotConfig):
        Node.__init__(self, 'robot_controller')
        QObject.__init__(self)
        
        # Initialize components
        self.config = config
        self.image_provider = ImageProvider(config.video_width, config.video_height)
        self.video_stream = VideoStream(config.video_port)
        self.winch_controller = WinchController(self, config.max_winch_speed)
        
        self.input_manager = InputManager()
        self.steam_deck = SteamDeckHandler(config.joystick_deadzone)
        self.input_manager.register_device(InputDevice.STEAM_DECK, self.steam_deck)

        self.ui_data_model = UIDataModel()
        self.status_updated.connect(self._update_ui)
        
        # Setup ROS subscribers and publishers
        self._setup_subscribers()
        self._setup_publishers()
        
        # Start video stream
        self.video_stream.connect_new_sample_callback(self.on_new_video_frame)
        self.video_stream.start()

    def _update_ui(self):
        """Update UI elements with latest data"""
        # Update Winch UI
        winch_status = self.winch_controller.get_status()
        self.ui_data_model.winch_length = winch_status['cable_length']
        self.ui_data_model.winch_speed = winch_status['cable_speed']
        self.ui_data_model.winch_torque = winch_status['winch_torque']
        self.ui_data_model.winch_temperature = winch_status['motor_temperature']
        self.ui_data_model.winch_voltage = winch_status['motor_voltage']
        self.ui_data_model.winch_brake = winch_status['motor_brake']
        self.ui_data_model.winch_available = winch_status['available']

        # Update Steam Deck Controls
        input_state = self.steam_deck.get_current_state()
        self.ui_data_model.left_joystick_x = input_state['left_stick']['x']
        self.ui_data_model.left_joystick_y = input_state['left_stick']['y']
        self.ui_data_model.right_joystick_x = input_state['right_stick']['x']
        self.ui_data_model.right_joystick_y = input_state['right_stick']['y']
        self.ui_data_model.left_trigger = input_state['triggers']['left']
        self.ui_data_model.right_trigger = input_state['triggers']['right']
        self.ui_data_model.dpad_up = input_state['dpad']['up']
        self.ui_data_model.dpad_down = input_state['dpad']['down']
        self.ui_data_model.dpad_left = input_state['dpad']['left']
        self.ui_data_model.dpad_right = input_state['dpad']['right']
        self.ui_data_model.button_a = input_state['buttons']['a']
        self.ui_data_model.button_b = input_state['buttons']['b']
        self.ui_data_model.button_x = input_state['buttons']['x']
        self.ui_data_model.button_y = input_state['buttons']['y']
        self.ui_data_model.button_l1 = input_state['buttons']['l1']
        self.ui_data_model.button_r1 = input_state['buttons']['r1']
        self.ui_data_model.button_menu = input_state['buttons']['menu']

        # Process control inputs
        self._process_control_input(input_state)
        

    def _process_control_input(self, input_state: Dict):
        """Process control inputs and update UI accordingly"""
        # Process joystick inputs
        if self.ui_data_model.right_joystick_control == "Winch Speed":
            print(f"Right Joystick Y: {input_state['right_stick']['y']}")
            if self.ui_data_model.winch_available and self.ui_data_model.winch_enabled:
                command_speed = input_state['right_stick']['y'] * self.config.max_winch_speed / 32768
                self.winch_controller.command_speed(command_speed)

    def _setup_subscribers(self):
        self.create_subscription(
            WinchStatus,
            'winch/status',
            self.winch_controller.update_status,
            1
        )
        
        self.create_subscription(
            SteamDeckInput,
            'steam_deck/input',
            self.steam_deck.process_input,
            1
        )
        
        self.create_subscription(
            LaserScan,
            'scan',
            self._on_lidar_scan,
            1
        )

    def _setup_publishers(self):
        self.winch_enable_pub = self.create_publisher(Bool, 'winch/enable', 1)
        self.winch_move_speed_pub = self.create_publisher(Float64, 'winch/cmd_speed', 1)

    def _on_steam_deck_input(self, msg: SteamDeckInput):
        changes = self.steam_deck.process_input(msg)
        print(f"Steam Deck Input: {changes}")
        self.status_updated.emit()

    def _on_lidar_scan(self, msg: LaserScan):
        self.new_scan_data.emit(
            list(msg.ranges),
            msg.angle_min,
            msg.angle_increment,
            msg.range_min,
            msg.range_max
        )

    def on_new_video_frame(self, sink):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        structure = caps.get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')
        
        _, map_info = buffer.map(Gst.MapFlags.READ)
        
        image = QImage(
            map_info.data, 
            width, 
            height, 
            width * 3, 
            QImage.Format_RGB888
        )
        
        self.image_provider.update_image(image)
        buffer.unmap(map_info)
        self.frame_ready.emit()
        
        return Gst.FlowReturn.OK
    
    #############################################
    ### UI Control Methods
    #############################################

    @Slot(bool)
    def setWinchEnabled(self, enabled: bool):
        """Enable/disable winch control"""
        self.ui_data_model.winch_enabled = enabled
        msg = Bool()
        msg.data = enabled
        self.winch_enable_pub.publish(msg)
        self.get_logger().info(f'Winch {"enabled" if enabled else "disabled"}')

    @Slot(str)
    def setLeftJoystickControl(self, control: str):
        """Set left joystick control mode"""
        self.ui_data_model.left_joystick_control = control
        self.get_logger().info(f'Left joystick control set to: {control}')

    @Slot(str)
    def setRightJoystickControl(self, control: str):
        """Set right joystick control mode"""
        self.ui_data_model.right_joystick_control = control
        self.get_logger().info(f'Right joystick control set to: {control}')

    @Slot()
    def terminateNodes(self):
        """Terminate all ROS nodes"""
        try:
            home_dir = os.path.expanduser("~")
            script_path = os.path.join(home_dir, "stop_all_nodes.bash")
            subprocess.run(["bash", script_path])
            self.get_logger().info('Terminated all nodes')
        except subprocess.CalledProcessError as e:
            self.get_logger().error(f'Error terminating nodes: {e}')

    @Slot(bool)
    def toggleSwitchChanged(self, checked: bool):
        """Handle toggle switch state change"""
        self.get_logger().info(f'Toggle switch changed to: {checked}')
        # Add specific toggle switch handling logic here

    def cleanup(self):
        self.video_stream.stop()

#############################################
### Main Application
#############################################

def main():
    # Initialize ROS
    rclpy.init()
    
    # Load configuration
    config = ConfigLoader.load_config('robot_config.yaml')
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create robot controller
    controller = RobotController(config)
    
    # Start ROS thread
    ros_thread = RosThread(controller)
    ros_thread.start()
    
    # Setup QML engine
    engine = QQmlApplicationEngine()
    engine.addImageProvider("live", controller.image_provider)
    
    # Load QML interface
    qml_path = os.path.join(os.path.dirname(__file__), 'qml', 'MainWindow.qml')
    engine.load(QUrl.fromLocalFile(qml_path))
    
    # Set context properties
    engine.rootContext().setContextProperty("backend", controller)
    engine.rootContext().setContextProperty("uiData", controller.ui_data_model)
    
    # Start status update timer
    status_timer = QTimer()
    status_timer.timeout.connect(controller.status_updated.emit)
    status_timer.start(int(1000 / config.update_rate))
    
    # Run application
    try:
        sys.exit(app.exec())
    finally:
        controller.cleanup()
        ros_thread.request_shutdown()
        ros_thread.wait()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
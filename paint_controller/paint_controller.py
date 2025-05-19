#!/usr/bin/env python3

import sys
import os
import time
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable, overload
import yaml
import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64, Bool, Float32, Int32, String, Int32, UInt8
from sensor_msgs.msg import LaserScan

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread, QMetaObject
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, QQmlProperty
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickImageProvider

from UIDataModel import UIDataModel
from OverlayController import OverlayController
from UIControlProcessor import ControlProcessor
from UISteamDeckHandler import SteamDeckHandler
from TrajectoryHandler import TrajectoryHandler
from WarningHandler import WarningHandler
from BaseVideoStreamHandler import BaseVideoStreamHandler
from UIWheelController import WheelController
from UIWinchController import WinchController
from UIWindMonitor import WindMonitor
from UITeensyController import TeensyController
from ActionConfigPython import ActionConfigPython
from UIHeartbeatHandler import UIHeartbeatHandler
from UIEmergencyButtonHandler import EmergencyButtonHandler

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp

#############################################
### Configuration
#############################################

class HeartbeatStatus(Enum):
    IDLE = 0x00      # System is off or not initialized
    ONTASK = 0x01       # Normal operation
    WARNING = 0x02  # Minor issue detected
    ERROR = 0x03    # Critical error

@dataclass
class RobotConfig:
    """Robot configuration parameters"""
    video_port: int = 5000
    update_rate: float = 60.0  # Hz
    watchdog_timeout: float = 1.0  # seconds
    joystick_deadzone: float = 0.1
    max_winch_speed: float = 1500.0
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
### Video Streaming
#############################################

class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(640, 480, QImage.Format_RGB888)

    def requestImage(self, id, size, requestedSize):
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

class NetworkMonitor:
    def __init__(self):
        self.ef_ip = ""
        self.ef_signal_strength = 0
        self.base_ip = ""
        self.base_signal_strength = 0

    def _ef_ip_callback(self, msg: String):
        self.ef_ip = msg.data
    
    def _ef_signal_strength_callback(self, msg: Int32):
        self.ef_signal_strength = msg.data

    def _base_ip_callback(self, msg: String):
        self.base_ip = msg.data

    def _base_signal_strength_callback(self, msg: Int32):
        self.base_signal_strength = msg.data

    def get_ef_ip(self) -> str:
        return self.ef_ip
    
    def get_ef_signal_strength(self) -> int:
        return self.ef_signal_strength
    
    def get_base_ip(self) -> str:
        return self.base_ip
    
    def get_base_signal_strength(self) -> int:
        return self.base_signal_strength


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
    emergency_overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()
    new_scan_data = Signal(list, float, float, float, float)
    status_updated = Signal()
    control_mode_changed = Signal(str)

    def __init__(self, config: RobotConfig):
        Node.__init__(self, 'robot_controller')
        QObject.__init__(self)
        Gst.init(None)
        
        # Initialize components
        self.warningHandler = WarningHandler()

        self.ef_image_provider = ImageProvider()
        self.ef_pipeline = Gst.parse_launch(
            "udpsrc port=5001 caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
        )
        self.ef_sink = self.ef_pipeline.get_by_name('sink')
        self.ef_sink.set_property('emit-signals', True)
        self.ef_sink.connect('new-sample', self.on_new_ef_sample)
        self.ef_pipeline.set_state(Gst.State.PLAYING)
        
        self.current_status = HeartbeatStatus.IDLE
        self.config = config
        self.video_stream = VideoStream(config.video_port)
        self.winch_controller = WinchController(self)
        self.wheel_controller = WheelController(self)
        self.netowrk_monitor = NetworkMonitor()   
        self.overlayController = OverlayController(self)
        self.teensy_controller = TeensyController(self)
        self.wind_monitor = WindMonitor(self)    
        self.controlProcessor = ControlProcessor(self)
        self.action_config = ActionConfigPython(self)
        self.heartbeat_handler = UIHeartbeatHandler(self)
        self.steam_deck_handler = SteamDeckHandler(deadzone=config.joystick_deadzone)
        self.steam_deck_handler.start()
        self.setup_steam_deck_callbacks()

        self.ui_data_model = UIDataModel()
        self.status_updated.connect(self._timer_callback)

        self._control_mode = "base" # base or ef

        # Initialize emergency button handler
        self.emergency_handler = EmergencyButtonHandler(self.steam_deck_handler, self)
        # Connect emergency handler signals to our signals
        self.emergency_handler.overlay_changed.connect(self.emergency_overlay_changed.emit)
        self.emergency_handler.emergency_triggered.connect(self.emergency_triggered.emit)

        # Setup ROS subscribers and publishers
        self._setup_subscribers()
        self.heartbeat_pub = self.create_publisher(UInt8, '/controller/heartbeat', 10)

        self.trajectoryHandler = TrajectoryHandler(self)

        # base video stream handler
        self.base_video_stream_handler = BaseVideoStreamHandler()

    @Slot(str, str, str, int)
    def show_popup(self, title: str, message: str, popup_type: str = "info", dismiss_delay: int = 500):
        """
        Show a popup notification that auto-dismisses
        
        Args:
            title: Title of the popup   
            message: Message content
            popup_type: Type of popup ("info", "warning", or "error")
            dismiss_delay: Time in milliseconds before the popup dismisses itself (default: 3000ms)
        """
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self.get_logger().error('No root QML objects found')
            return
            
        root = root_objects[0]
        popup = root.findChild(QObject, "messagePopup")
        
        if popup:
            QQmlProperty.write(popup, "messageTitle", title)
            QQmlProperty.write(popup, "messageText", message)
            QQmlProperty.write(popup, "messageType", popup_type)
            QQmlProperty.write(popup, "dismissDelay", dismiss_delay)
            QMetaObject.invokeMethod(popup, "open")
            self.get_logger().info(f'Showing {popup_type} popup: {title} - {message}')
        else:
            self.get_logger().error('Popup not found in QML')

    def on_new_ef_sample(self, sink):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        structure = caps.get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')
        
        _, map_info = buffer.map(Gst.MapFlags.READ)
        
        # Ensure the data is in the correct format (RGB)
        data = map_info.data
        
        # Create QImage directly from the buffer data
        ef_image = QImage(data, width, height, width * 3, QImage.Format_RGB888)
        
        self.ef_image_provider.image = ef_image.copy()  # Create a deep copy of the image
        buffer.unmap(map_info)
        
        self.frame_ready.emit()
        
        return Gst.FlowReturn.OK
    
    def setup_steam_deck_callbacks(self):
        """Set up callbacks for Steam Deck buttons that control UI elements"""
        
        # Navigation callbacks
        self.steam_deck_handler.register_button_callback('up', self._on_up_pressed)
        self.steam_deck_handler.register_button_callback('down', self._on_down_pressed)
        self.steam_deck_handler.register_button_callback('left', self._on_left_pressed)
        self.steam_deck_handler.register_button_callback('right', self._on_right_pressed)
        
        # Menu toggle callbacks
        self.steam_deck_handler.register_button_callback('r4', self._on_r4_pressed)
        self.steam_deck_handler.register_button_callback('l4', self._on_l4_pressed)
        self.steam_deck_handler.register_button_callback('menu', self._on_menu_pressed)

        # switch control mode callbacks
        self.steam_deck_handler.register_button_callback('switch', self._on_switch_pressed)

        # expand or hide menu
        self.steam_deck_handler.register_button_callback('dot', self.toggle_sidebar)

        # extend arm
        self.steam_deck_handler.register_button_callback('l5', self._on_l5_pressed)
        self.steam_deck_handler.register_button_callback('r5', self._on_r5_pressed)


    # Add property for control_mode
    @Property(str, notify=control_mode_changed)
    def control_mode(self):
        return self._control_mode
        
    @control_mode.setter
    def control_mode(self, mode):
        if self._control_mode != mode:
            self._control_mode = mode
            self.control_mode_changed.emit(mode)

    @Slot()
    def toggle_sidebar(self):
        """Toggle the sidebar expanded/collapsed state"""
        # Get access to the root objects
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self.get_logger().error('No root QML objects found')
            return
            
        root = root_objects[0]
        # Find the selectBar component
        select_bar = root.findChild(QObject, "selectBar")
        
        if select_bar:
            # Invoke the toggleSidebar method
            QMetaObject.invokeMethod(select_bar, "toggleSidebar")
            self.get_logger().info('Toggled sidebar state')
        else:
            self.get_logger().error('SelectBar not found in QML')

    def _on_l5_pressed(self):
        # Initialize class attributes if they don't exist
        if not hasattr(self, '_l1_last_press_time'):
            self._l1_last_press_time = 0.0
            self._arm_extension_presets = [800]  # List of preset values in mm
        # Get current time
        current_time = time.time()
        time_since_last_press = current_time - self._l1_last_press_time
        
        # Update the last press time
        self._l1_last_press_time = current_time
        self.show_popup("Extending Arm", "Press again to retract the arm", "info")
        
        # Check if this is a double press (within 0.5 seconds)
        if time_since_last_press <= 1:
            # Double press detected - retract arm to 250mm
            self.teensy_controller.extendArm(250)
            # self.show_popup("Retracting Arm", "Retracting arm to 250 mm", "info")

    def _on_r5_pressed(self):
        # Initialize class attributes if they don't exist
        if not hasattr(self, '_r1_last_press_time'):
            self._r1_last_press_time = 0.0
            self._arm_extension_presets = [800]  # List of preset values in mm
            self._arm_preset_index = 0
        
        # Get current time
        current_time = time.time()
        time_since_last_press = current_time - self._r1_last_press_time
        
        # Update the last press time
        self._r1_last_press_time = current_time
        self.show_popup("Extending Arm", "Press again to extend the arm", "info")
        
        # Check if this is a double press (within 0.5 seconds)
        if time_since_last_press <= 1:
            # Double press detected - perform the action
            current_index = self._arm_preset_index
            preset_value = self._arm_extension_presets[current_index]
            
            # Extend the arm to the current preset
            self.teensy_controller.extendArm(preset_value)
            # self.show_popup("Extending Arm", f"Extending arm to {preset_value} mm", "info")
            
            # Update the index for next time (toggle between 0 and 1)
            self._arm_preset_index = (current_index + 1) % len(self._arm_extension_presets)

    def _on_switch_pressed(self):
        """Switch control mode between base and ef"""
        if self.control_mode == "base":
            # Switching to EF mode
            self.control_mode = "ef"
            self.overlayController.set_joystick_controls("EF Yaw Angle", "Winch Speed")
            self.show_popup("Control Mode", "Switched to EF control mode", "info")
        else:
            # Switching to Base mode
            self.control_mode = "base"
            self.overlayController.set_joystick_controls("Left Wheel Speed", "Right Wheel Speed")
            self.wheel_controller.resetWheelPosition()
            time.sleep(0.1)
            self.wheel_controller.resetWheelPosition()
            time.sleep(0.1)
            self.wheel_controller.resetWheelPosition()
            self.show_popup("Control Mode", "Switched to Base control mode", "info")

    def _on_up_pressed(self):
        if self.overlayController.is_showing_menu():
            self.overlayController.move_up()

    def _on_down_pressed(self):
        if self.overlayController.is_showing_menu():
            self.overlayController.move_down()

    def _on_left_pressed(self):
        if self.overlayController.is_showing_menu():
            self.overlayController.move_to_first()
        else:
            # If no menu is showing, switch to previous page (Planner)
            self.trajectoryHandler.switch_to_page(0)  # Switch to Planner

    def _on_right_pressed(self):
        if self.overlayController.is_showing_menu():
            self.overlayController.move_to_last()
        else:
            # If no menu is showing, switch to next page (Executor)
            self.trajectoryHandler.switch_to_page(1)  # Switch to Executor


    def _on_r4_pressed(self):
        self.overlayController.set_active_menu("right")
        self.overlayController.toggle_right_menu()

    def _on_l4_pressed(self):
        self.overlayController.set_active_menu("left")
        self.overlayController.toggle_left_menu()

    def _on_menu_pressed(self):
        self.overlayController.set_active_menu("power")
        self.overlayController.toggle_power_menu()

    def _timer_callback(self):
        """Update UI elements with latest data"""

        # Update Steam Deck Controls
        input_state = self.steam_deck_handler.get_current_state()

        # Update Network Monitor
        self.ui_data_model.ef_ip = self.netowrk_monitor.get_ef_ip()
        self.ui_data_model.ef_signal_strength = self.netowrk_monitor.get_ef_signal_strength()
        self.ui_data_model.base_ip = self.netowrk_monitor.get_base_ip()
        self.ui_data_model.base_signal_strength = self.netowrk_monitor.get_base_signal_strength()

        self.ui_data_model.display_message = self.ui_data_model.display_message

        # Process control inputs with current state
        input_state = self.steam_deck_handler.get_current_state()
        self.controlProcessor.process_input(input_state)\
        
        # Check emergency button state
        self.emergency_handler.check_emergency_button(input_state.get('buttons', {}))


    def display_message(self, message: str):
        self.ui_data_model.display_message = message

    def _publish_heartbeat(self):
        """Publish a heartbeat message every 0.5 seconds"""
        msg = UInt8()
        msg.data = HeartbeatStatus.IDLE.value  # Indicate the node is alive
        self.heartbeat_pub.publish(msg)
        
    def _setup_subscribers(self):
        self.create_subscription(
            String,
            'connection/ef/ip',
            self.netowrk_monitor._ef_ip_callback,
            1
        )

        self.create_subscription(
            Int32,
            'connection/ef/signal_strength',
            self.netowrk_monitor._ef_signal_strength_callback,
            1
        )

        self.create_subscription(
            String,
            'connection/base/ip',
            self.netowrk_monitor._base_ip_callback,
            1
        )

        self.create_subscription(
            Int32,
            'connection/base/signal_strength',
            self.netowrk_monitor._base_signal_strength_callback,
            1
        )

    #############################################
    ### UI Control Methods
    #############################################

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
        self.display_message(f'Right joystick control set to: {control}')

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
        self.emergency_handler.reset_state()

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
    engine.addImageProvider("ef_live", controller.ef_image_provider)
    engine.addImageProvider("base_front_live", controller.base_video_stream_handler.front_image_provider)
    engine.addImageProvider("base_rear_live", controller.base_video_stream_handler.rear_image_provider)
    
    # Load QML interface
    qml_path = os.path.join(os.path.dirname(__file__), 'qml', 'MainWindow.qml')
    engine.load(QUrl.fromLocalFile(qml_path))
    
    # Set context properties
    engine.rootContext().setContextProperty("backend", controller)
    engine.rootContext().setContextProperty("baseStreamer", controller)
    engine.rootContext().setContextProperty("uiData", controller.ui_data_model)
    engine.rootContext().setContextProperty("overlayController", controller.overlayController)
    engine.rootContext().setContextProperty("trajectoryHandler", controller.trajectoryHandler)
    engine.rootContext().setContextProperty("warningHandler", controller.warningHandler)
    engine.rootContext().setContextProperty("baseStreamHandler", controller.base_video_stream_handler)
    engine.rootContext().setContextProperty("wheelController", controller.wheel_controller)
    engine.rootContext().setContextProperty("winchController", controller.winch_controller)
    engine.rootContext().setContextProperty("steamDeckHandler", controller.steam_deck_handler)
    engine.rootContext().setContextProperty("windMonitor", controller.wind_monitor)
    engine.rootContext().setContextProperty("teensyController", controller.teensy_controller)
    engine.rootContext().setContextProperty("actionConfig", controller.action_config)
    engine.rootContext().setContextProperty("heartbeatHandler", controller.heartbeat_handler)
    controller.engine = engine
    
    # Start status update timer
    status_timer = QTimer()
    status_timer.timeout.connect(controller.status_updated.emit)
    status_timer.start(int(1000 / config.update_rate))

    heartbeat_timer = QTimer()
    heartbeat_timer.timeout.connect(controller._publish_heartbeat)
    heartbeat_timer.start(0.5)
    
    # Run application
    try:
        sys.exit(app.exec())
    finally:
        controller.cleanup()
        controller.heartbeat_handler.cleanup()
        ros_thread.request_shutdown()
        ros_thread.wait()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
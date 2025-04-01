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
from std_msgs.msg import Float64, Bool, Float32, Int32, String
from sensor_msgs.msg import LaserScan
from towngas_interfaces.msg import WinchStatus, WheelStatus, SteamDeckInput, TeensyStatus, TeensyYaw, MoveWinchLength, MoveWheelSpeeds

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
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

#############################################
### Teensy Monitor
#############################################

class WindMonitor:
    def __init__(self, node: Node):
        self._node = node
        self._speed = 0
        self._direction = 0

    def _speed_callback(self, msg: Float32):
        self._speed = msg.data

    def _direction_callback(self, msg: Float32):
        self._direction = msg.data

    def get_speed(self) -> float:
        return self._speed
    
    def get_direction(self) -> float:
        return self._direction

class TeensyMonitor:
    def __init__(self, node: Node):
        self._node = node
        self._status = {}
        self._last_status_update_time = 0
        self._connection_timeout = 1.0

    def _status_callback(self, msg: TeensyStatus):
        try:
            # Convert milliseconds to hours, minutes, seconds
            total_seconds = int(msg.runtime / 1000)  # Convert ms to seconds
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            formatted_runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            self._status = {
                'available': True,
                'top_rail_position': f"{msg.top_rail_position:.2f}",
                'top_rail_speed': f"{msg.top_rail_speed:.2f}",
                'top_rail_current': f"{msg.top_rail_current:.2f}",
                'arm_rail_position': f"{msg.arm_rail_position:.2f}",
                'arm_rail_speed': f"{msg.arm_rail_speed:.2f}",
                'arm_rail_current': f"{msg.arm_rail_current:.2f}",
                'voltage': f"{msg.voltage:.2f}",
                'temperature': f"{msg.temperature:.1f}",
                'current': f"{msg.current:.2f}",
                'run_time': formatted_runtime,
                'loop_time': f"{msg.looptime:.2f}",
                'loop_time_counter': f"{msg.looptime_counter:.2f}",
                'left_prop_position': f"{msg.left_prop_position:.2f}",
                'left_prop_pwm': f"{msg.left_prop_pwm:.2f}",
                'right_prop_position': f"{msg.right_prop_position:.2f}",
                'right_prop_pwm': f"{msg.right_prop_pwm:.2f}",
                'imu_acc_x': f"{msg.linear_acceleration.x:.2f}",
                'imu_acc_y': f"{msg.linear_acceleration.y:.2f}",
                'imu_acc_z': f"{msg.linear_acceleration.z:.2f}",
                'imu_angular_acc_x': f"{msg.angular_velocity.x:.2f}",
                'imu_angular_acc_y': f"{msg.angular_velocity.y:.2f}",
                'imu_angular_acc_z': f"{msg.angular_velocity.z:.2f}",
                'imu_pitch': msg.orientation.x,
                'imu_roll': msg.orientation.y,
                'imu_yaw': msg.orientation.z,
                'yaw_enabled': msg.yaw_enabled,
                'yaw_command': f"{msg.yaw_command:.2f}",
                'yaw_pid_p': f"{msg.yaw_pid_p:.2f}",
                'yaw_pid_i': f"{msg.yaw_pid_i:.2f}",
                'yaw_pid_d': f"{msg.yaw_pid_d:.2f}",
                'yaw_pwm': f"{msg.yaw_pwm:.2f}"
            }

            self._last_status_update_time = time.time()
        except Exception as e:
            print(f"Error processing Teensy status: {e}")

    def get_status(self) -> Dict:
        if time.time() - self._last_status_update_time > self._connection_timeout:
            self._status['available'] = False
        return self._status
    
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
    new_scan_data = Signal(list, float, float, float, float)
    status_updated = Signal()

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
        
        self.config = config
        self.video_stream = VideoStream(config.video_port)
        self.winch_controller = WinchController(self)
        self.wheel_controller = WheelController(self)
        self.netowrk_monitor = NetworkMonitor()   
        self.overlayController = OverlayController()
        self.teensyMonitor = TeensyMonitor(self)
        self.windMonitor = WindMonitor(self)    
        self.controlProcessor = ControlProcessor(self)
        self.target_yaw = 0

        self.steam_deck = SteamDeckHandler(deadzone=config.joystick_deadzone)
        self.steam_deck.attach_to_node(self)

        self.ui_data_model = UIDataModel()
        self.status_updated.connect(self._timer_callback)

        
        # Setup ROS subscribers and publishers
        self._setup_subscribers()
        self._setup_publishers()

        self.trajectoryHandler = TrajectoryHandler()

        # base video stream handler
        self.base_video_stream_handler = BaseVideoStreamHandler()

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

    def _timer_callback(self):
        """Update UI elements with latest data"""

        # Update Steam Deck Controls
        input_state = self.steam_deck.get_current_state()

        # Update teensy status
        teensy_status = self.teensyMonitor.get_status()
        self.ui_data_model.top_rail_position = teensy_status.get('top_rail_position', '0.00')
        self.ui_data_model.top_rail_speed = teensy_status.get('top_rail_speed', '0.00')
        self.ui_data_model.top_rail_current = teensy_status.get('top_rail_current', '0.00')
        self.ui_data_model.arm_rail_position = teensy_status.get('arm_rail_position', '0.00')
        self.ui_data_model.arm_rail_speed = teensy_status.get('arm_rail_speed', '0.00')
        self.ui_data_model.arm_rail_current = teensy_status.get('arm_rail_current', '0.00')
        self.ui_data_model.teensy_available = teensy_status.get('available', False)
        self.ui_data_model.teensy_voltage = teensy_status.get('voltage', '0.00')
        self.ui_data_model.teensy_temperature = teensy_status.get('temperature', '0.00')
        self.ui_data_model.teensy_current = teensy_status.get('current', '0.00')
        self.ui_data_model.teensy_run_time = teensy_status.get('run_time', '0.00')
        self.ui_data_model.teensy_loop_time = teensy_status.get('loop_time', '0.00')
        self.ui_data_model.teensy_loop_time_counter = teensy_status.get('loop_time_counter', '0.00')
        self.ui_data_model.left_prop_position = teensy_status.get('left_prop_position', '0.00')
        self.ui_data_model.left_prop_pwm = teensy_status.get('left_prop_pwm', '0.00')
        self.ui_data_model.right_prop_position = teensy_status.get('right_prop_position', '0.00')
        self.ui_data_model.right_prop_pwm = teensy_status.get('right_prop_pwm', '0.00')
        self.ui_data_model.teensy_imu_acc_x = teensy_status.get('imu_acc_x', '0.00')
        self.ui_data_model.teensy_imu_acc_y = teensy_status.get('imu_acc_y', '0.00')
        self.ui_data_model.teensy_imu_acc_z = teensy_status.get('imu_acc_z', '0.00')
        self.ui_data_model.teensy_imu_angular_acc_x = teensy_status.get('imu_angular_acc_x', '0.00')
        self.ui_data_model.teensy_imu_angular_acc_y = teensy_status.get('imu_angular_acc_y', '0.00')
        self.ui_data_model.teensy_imu_angular_acc_z = teensy_status.get('imu_angular_acc_z', '0.00')
        self.ui_data_model.teensy_imu_pitch = round(float(teensy_status.get('imu_pitch', '0.00')), 2)
        self.ui_data_model.teensy_imu_roll = round(float(teensy_status.get('imu_roll', '0.00')), 2)
        self.ui_data_model.teensy_imu_yaw = round(float(teensy_status.get('imu_yaw', '0.00')), 2)
        self.ui_data_model.teensy_yaw_enabled = teensy_status.get('yaw_enabled', False)
        self.ui_data_model.teensy_yaw_command = teensy_status.get('yaw_command', '0.00')
        self.ui_data_model.teensy_yaw_pid_p = teensy_status.get('yaw_pid_p', '0.00')
        self.ui_data_model.teensy_yaw_pid_i = teensy_status.get('yaw_pid_i', '0.00')
        self.ui_data_model.teensy_yaw_pid_d = teensy_status.get('yaw_pid_d', '0.00')
        self.ui_data_model.teensy_yaw_pwm = teensy_status.get('yaw_pwm', '0.00')
        
        # Update Wind Monitor
        self.ui_data_model.wind_speed = round(float(self.windMonitor.get_speed()), 2)
        self.ui_data_model.wind_direction = round(float(self.windMonitor.get_direction()), 2)

        # Update Network Monitor
        self.ui_data_model.ef_ip = self.netowrk_monitor.get_ef_ip()
        self.ui_data_model.ef_signal_strength = self.netowrk_monitor.get_ef_signal_strength()
        self.ui_data_model.base_ip = self.netowrk_monitor.get_base_ip()
        self.ui_data_model.base_signal_strength = self.netowrk_monitor.get_base_signal_strength()

        self.ui_data_model.display_message = self.ui_data_model.display_message

        if self.steam_deck.get_button_pressed('up') and self.overlayController.is_showing_menu():
            self.overlayController.move_up()
        elif self.steam_deck.get_button_pressed('down') and self.overlayController.is_showing_menu():
            self.overlayController.move_down()
        elif self.steam_deck.get_button_pressed('left') and self.overlayController.is_showing_menu():
            self.overlayController.move_to_first()
        elif self.steam_deck.get_button_pressed('right') and self.overlayController.is_showing_menu():
            self.overlayController.move_to_last()

        if self.steam_deck.get_button_pressed('r4'):
            self.overlayController.set_active_menu("right")
            self.overlayController.toggle_right_menu()
        elif self.steam_deck.get_button_pressed('l4'):
            self.overlayController.set_active_menu("left")
            self.overlayController.toggle_left_menu()
        elif self.steam_deck.get_button_pressed('menu'):
            self.overlayController.set_active_menu("power")
            self.overlayController.toggle_power_menu()

        # Process control inputs
        self.controlProcessor.process_input(input_state)

    def display_message(self, message: str):
        self.ui_data_model.display_message = message
        
    def _setup_subscribers(self):
        self.create_subscription(
            LaserScan,
            'scan',
            self._on_lidar_scan,
            1
        )

        self.create_subscription(
            TeensyStatus,
            'teensy/status',
            self.teensyMonitor._status_callback,
            10
        )
        
        self.create_subscription(
            Float32,
            'wind/speed',
            self.windMonitor._speed_callback,
            1
        )

        self.create_subscription(
            Float32,
            'wind/direction',
            self.windMonitor._direction_callback,
            1
        )

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

    def _setup_publishers(self):
        self.ef_move_top_rail_speed_pub = self.create_publisher(Float32, 'teensy/top_rail/speed/cmd', 1)
        self.ef_move_arm_rail_speed_pub = self.create_publisher(Float32, 'teensy/arm_rail/speed/cmd', 1)
        self.prop_left_pwm_pub = self.create_publisher(Int32, 'teensy/prop/left/pwm/cmd', 1)
        self.prop_right_pwm_pub = self.create_publisher(Int32, 'teensy/prop/right/pwm/cmd', 1)
        self.prop_left_joint_pub = self.create_publisher(Float32, 'teensy/prop/left/joint/cmd', 1)
        self.prop_right_joint_pub = self.create_publisher(Float32, 'teensy/prop/right/joint/cmd', 1)
        self.teensy_relay_pub = self.create_publisher(Bool, 'teensy/relay/cmd', 1)
        self.teensy_enable_pub = self.create_publisher(Bool, 'teensy/enable/cmd', 1)
        self.ef_spray_trigger_pub = self.create_publisher(Int32, 'teensy/spray_gun/trigger/cmd', 1)
        self.ef_spray_gimbal_speed_pub = self.create_publisher(Int32, 'teensy/spray_gun/gimbal/speed/cmd', 1)
        self.ef_yaw_control_pub = self.create_publisher(TeensyYaw, 'teensy/yaw/control/cmd', 1)

    def _on_lidar_scan(self, msg: LaserScan):
        self.new_scan_data.emit(
            list(msg.ranges),
            msg.angle_min,
            msg.angle_increment,
            msg.range_min,
            msg.range_max
        )

    #############################################
    ### UI Control Methods
    #############################################

    @Slot(bool)
    def setTeensyEnabled(self, enabled: bool):
        """Enable/disable Teensy control"""
        self.ui_data_model.teensy_enabled = enabled
        msg = Bool()
        msg.data = enabled
        self.teensy_enable_pub.publish(msg)
        self.get_logger().info(f'Teensy {"enabled" if enabled else "disabled"}')

    @Slot(bool)
    def setTeensyRelayEnabled(self, enabled: bool):
        """Enable/disable Teensy relay"""
        self.ui_data_model.teensy_relay_enabled = enabled
        msg = Bool()
        msg.data = enabled
        self.teensy_relay_pub.publish(msg)
        self.get_logger().info(f'Teensy relay {"enabled" if enabled else "disabled"}')

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

    @overload
    def setYawControl(self, target: float) -> None:
        ...

    @overload
    def setYawControl(self, enabled: bool, target: float, p: float, i: float, d: float, pwm: int) -> None:
        ...

    @Slot(bool, float, float, float, float, int)
    def setYawControl(self, *args):
        """Set yaw control parameters and enable state"""
        if len(args) == 1:
            target = args[0]
            teensy_status = self.teensyMonitor.get_status()
            enabled = teensy_status.get('yaw_enabled', False)
            p = float(teensy_status.get('yaw_pid_p', 0.0))
            i = float(teensy_status.get('yaw_pid_i', 0.0))
            d = float(teensy_status.get('yaw_pid_d', 0.0))
            pwm = int(float(teensy_status.get('yaw_pwm', 0)))
        elif len(args) == 6:
            enabled, target, p, i, d, pwm = args

        msg = TeensyYaw()
        msg.yaw_enabled = enabled
        msg.yaw_command = target  # Use current yaw as target
        print(f"Setting yaw control: {enabled}, {target}, {p}, {i}, {d}, {pwm}")
        msg.yaw_pid_p = p
        msg.yaw_pid_i = i
        msg.yaw_pid_d = d
        msg.yaw_pwm = pwm
        self.ef_yaw_control_pub.publish(msg)
        self.display_message(f'Yaw control {"enabled" if enabled else "disabled"} with Target: {target} P:{p} I:{i} D:{d} PWM:{pwm}')

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
    engine.rootContext().setContextProperty("steamDeckHandler", controller.steam_deck)
    
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
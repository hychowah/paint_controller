#!/usr/bin/env python3

import sys
import os
import signal
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, List, Any, Callable
from threading import Lock
import yaml

# Force Qt to use X11 backend for VTK compatibility (Wayland issues)
if 'QT_QPA_PLATFORM' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'xcb'

import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Property, Signal, QThread, QMetaObject, Q_ARG
from PySide6.QtQml import QQmlApplicationEngine, QQmlProperty
from PySide6.QtWidgets import QApplication

from paint_controller.ui.overlay import OverlayController
from paint_controller.handlers.control_processor import ControlProcessor
from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.services.workflow_legacy import WorkFlowHandler  # Keep for backwards compatibility
from paint_controller.handlers.warnings import WarningHandler
from paint_controller.services.video_stream import VideoStreamHandler
from paint_controller.controllers.wheel import WheelController
from paint_controller.controllers.winch import WinchController
from paint_controller.controllers.wind_monitor import WindMonitor
from paint_controller.controllers.teensy import TeensyController
from paint_controller.controllers.lidar import LidarController
from paint_controller.models.action_config import ActionConfigPython
from paint_controller.handlers.heartbeat import UIHeartbeatHandler
from paint_controller.handlers.emergency import EmergencyButtonHandler
from paint_controller.handlers.input import UIInputHandler
from paint_controller.controllers.ssh import UISSHController
from paint_controller.controllers.system_monitor import SystemMonitor
from paint_controller.services.workflow.workflow_runner import WorkFlowRunner
from paint_controller.services.screen_recorder import ScreenRecorder
from paint_controller.services.ros_bag_recorder import RosBagRecorder
from paint_controller.core.settings import SettingsManager

# Global reference for signal handler
_app_instance = None

def signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) gracefully - force immediate exit"""
    print("\n\nReceived interrupt signal (Ctrl+C)...")
    print("Forcing immediate shutdown...")
    
    # Don't try to cleanup from signal handler - just force exit
    # The finally block in main() will handle cleanup if app.exec() exits normally
    # But if we're here, something is stuck, so just exit
    try:
        # Try to stop the Qt app first
        global _app_instance
        if _app_instance is not None:
            _app_instance.quit()
    except:
        pass
    
    # Force exit immediately - don't wait for cleanup
    print("Forced shutdown complete.")
    os._exit(1)  # Use os._exit to bypass cleanup that might be stuck

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
    update_rate: float = 30.0  # Hz
    joystick_deadzone: float = 0.1

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
### ROS Integration
#############################################

class RosThread(QThread):
    """Isolated thread for running ROS event loop with thread-safe shutdown."""
    error_occurred = Signal(str)
    node_started = Signal()
    node_stopped = Signal()

    def __init__(self, node: Node):
        """
        Initialize ROS thread.
        
        Args:
            node: ROS2 node to spin
        """
        super().__init__()
        self.node = node
        self._running = False
        self._shutdown_requested = False
        self._lock = Lock()  # Thread-safe access to shared state
        self._last_spin_time = 0
        self._spin_timeout = 5.0  # Watchdog: if spin_once takes >5s, consider network dead

    def run(self) -> None:
        """
        Run the ROS event loop in a separate thread.
        
        Continuously spins the node until shutdown is requested.
        Handles exceptions and ensures proper cleanup.
        Recovers from network disconnections by destroying and recreating subscriptions.
        """
        try:
            self._running = True
            self.node_started.emit()
            
            while True:
                # Thread-safe check of shutdown flag
                with self._lock:
                    if self._shutdown_requested:
                        break
                
                if not rclpy.ok():
                    error_msg = "ROS context is not valid - network may be disconnected"
                    self.error_occurred.emit(error_msg)
                    # Don't break - try to recover by waiting a bit
                    import time
                    time.sleep(0.5)
                    continue
                
                try:
                    import time
                    self._last_spin_time = time.time()
                    # Use smaller timeout to prevent long hangs on bad network
                    rclpy.spin_once(self.node, timeout_sec=0.05)
                    
                except Exception as spin_error:
                    # Network error during spin - emit but continue trying
                    error_msg = f"ROS spin error (likely network): {str(spin_error)}"
                    self.error_occurred.emit(error_msg)
                    
                    # Sleep briefly to avoid CPU spinning on errors
                    import time
                    time.sleep(0.1)
                
            self._cleanup()
            
        except Exception as e:
            error_msg = f"Critical ROS thread error: {str(e)}"
            self.error_occurred.emit(error_msg)
            # Force cleanup even on critical error
            self._cleanup()
        finally:
            self._running = False
            self.node_stopped.emit()

    def request_shutdown(self) -> None:
        """
        Request thread shutdown.
        
        Thread-safe: Uses lock to ensure visibility across threads.
        This method should be called from the main thread to gracefully
        shut down the ROS event loop.
        """
        with self._lock:
            self._shutdown_requested = True

    def _cleanup(self) -> None:
        """
        Clean up ROS node resources.
        
        Called when thread is shutting down to properly destroy the node.
        This is now called both on normal exit AND on exceptions.
        """
        try:
            if self.node:
                # First trigger cleanup on the node itself (calls cleanup on all sub-components)
                if hasattr(self.node, 'cleanup'):
                    try:
                        self.node.cleanup()
                    except Exception as e:
                        print(f"Error calling node cleanup method: {e}")
                
                # Then destroy the node to clean up all ROS resources
                self.node.destroy_node()
                print("ROS node destroyed successfully")
        except Exception as e:
            print(f"Error during ROS thread cleanup: {e}")

#############################################
### Main Controller
#############################################

class RobotController(Node, QObject):
    frame_ready = Signal()
    emergency_overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()
    status_updated = Signal()
    control_mode_changed = Signal(str)
    display_message_changed = Signal(str)  # For displaying messages in UI
    left_joystick_control_changed = Signal(str)
    right_joystick_control_changed = Signal(str)
    left_control_info_changed = Signal(str, str)  # mode, value
    right_control_info_changed = Signal(str, str)  # mode, value

    def __init__(self, config: RobotConfig):
        Node.__init__(self, 'robot_controller')
        QObject.__init__(self)
        
        # Cleanup guard to prevent multiple cleanup calls
        self._cleanup_in_progress = False
        self._cleanup_complete = False
        
        # Initialize settings manager first (before sub-controllers)
        self.settings_manager = SettingsManager(self)
        
        # Initialize components
        self.warningHandler = WarningHandler()

        # Initialize unified video stream handler with ROS2 integration
        self.video_stream_handler = VideoStreamHandler(config.video_port, ros_node=self)
        
        self.current_status = HeartbeatStatus.IDLE
        self.config = config
        
        # Initialize state variables (replaces UIDataModel)
        self._display_message = ""
        self._left_joystick_control = "None"
        self._right_joystick_control = "None"
        self._left_control_mode = "None"
        self._left_control_value = ""
        self._right_control_mode = "None"
        self._right_control_value = ""
        
        self.winch_controller = WinchController(self)
        self.wheel_controller = WheelController(self)
        self.overlayController = OverlayController(self)
        self.teensy_controller = TeensyController(self)
        self.lidar_controller = LidarController(self)
        self.wind_monitor = WindMonitor(self)    
        self.controlProcessor = ControlProcessor(self)
        self.action_config = ActionConfigPython(self)
        self.heartbeat_handler = UIHeartbeatHandler(self)
        self.steam_deck_handler = SteamDeckHandler(deadzone=config.joystick_deadzone)
        self.input_handler = UIInputHandler(self)
        self.steam_deck_handler.start()
        self.ssh_controller = UISSHController(self)
        self.system_monitor = SystemMonitor()
        self.screen_recorder = ScreenRecorder()
        self.ros_bag_recorder = RosBagRecorder(self)

        
        self.setup_steam_deck_callbacks()

        self.status_updated.connect(self._timer_callback)

        self._control_mode = "base" # base or ef
        
        # Connect control mode changes to update fullscreen video source
        self.control_mode_changed.connect(self.update_fullscreen_video_source)

        # Initialize emergency button handler
        self.emergency_handler = EmergencyButtonHandler(self.steam_deck_handler, self)
        # Connect emergency handler signals to our signals
        self.emergency_handler.overlay_changed.connect(self.emergency_overlay_changed.emit)
        self.emergency_handler.emergency_triggered.connect(self.emergency_triggered.emit)
        
        # Connect wheel controller error signal to trigger emergency
        self.wheel_controller.error_state_changed.connect(self._handle_wheel_motor_error)

        # Setup ROS subscribers and publishers
        self._setup_subscribers()
        self.heartbeat_pub = self.create_publisher(UInt8, '/controller/heartbeat', 10)

        # Initialize workflow runner (new system - replaces old WorkFlowHandler)
        self.workflow_runner = WorkFlowRunner(self)
        
        # Keep old handler for backwards compatibility (can be removed later)
        self.workFlowHandler = WorkFlowHandler(self)

        # Connect video stream signals
        self.video_stream_handler.endEffectorFrameReady.connect(self.frame_ready.emit)
        
        # Note: LiDAR overlay updates automatically via QML Connections block
        # No manual signal connection needed in Python
        
        # Start all video streams
        self.video_stream_handler.start_all_streams()

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

    def _handle_wheel_motor_error(self, has_error: bool, error_message: str):
        """Handle wheel motor error signal - trigger emergency stop and show popup"""
        if has_error:
            self.get_logger().error(f'Wheel motor error detected: {error_message}')
            
            # Stop all motors
            self.wheel_controller.emergency_stop()
            self.winch_controller.command_speed_rpm(0)
            self.teensy_controller.setSprayTrigger(1000)
            
            # Show error popup
            self.show_popup("MOTOR ERROR", error_message, "error", 5000)
            
            # Emit emergency signal
            self.emergency_triggered.emit()

    def setup_steam_deck_callbacks(self):
        ih = self.input_handler
        self.steam_deck_handler.register_button_callback('up', ih.on_up_pressed)
        self.steam_deck_handler.register_button_callback('down', ih.on_down_pressed)
        self.steam_deck_handler.register_button_callback('left', ih.on_left_pressed)
        self.steam_deck_handler.register_button_callback('right', ih.on_right_pressed)
        self.steam_deck_handler.register_button_callback('r4', ih.on_r4_pressed)
        self.steam_deck_handler.register_button_callback('l4', ih.on_l4_pressed)
        self.steam_deck_handler.register_button_callback('menu', ih.on_menu_pressed)
        self.steam_deck_handler.register_button_callback('switch', ih.on_switch_pressed)
        self.steam_deck_handler.register_button_callback('l5', ih.on_l5_pressed)
        self.steam_deck_handler.register_button_callback('r5', ih.on_r5_pressed)
        self.steam_deck_handler.register_button_callback('dot', self.toggle_fullscreen)
        self.steam_deck_handler.register_button_callback('a', self.toggle_lidar_overlay)
        self.steam_deck_handler.register_button_callback('l1', ih.on_l1_pressed)


    # Add property for control_mode
    @Property(str, notify=control_mode_changed)
    def control_mode(self):
        return self._control_mode
        
    @control_mode.setter
    def control_mode(self, mode):
        if self._control_mode != mode:
            self._control_mode = mode
            self.control_mode_changed.emit(mode)

    # Properties for display message (replaces UIDataModel.display_message)
    @Property(str, notify=display_message_changed)
    def display_message(self) -> str:
        return self._display_message
    
    @display_message.setter
    def display_message(self, message: str) -> None:
        if self._display_message != message:
            self._display_message = message
            self.display_message_changed.emit(message)

    # Properties for joystick control modes (replaces UIDataModel.left/right_joystick_control)
    @Property(str, notify=left_joystick_control_changed)
    def left_joystick_control(self) -> str:
        return self._left_joystick_control
    
    @left_joystick_control.setter
    def left_joystick_control(self, mode: str) -> None:
        if self._left_joystick_control != mode:
            self._left_joystick_control = mode
            self.left_joystick_control_changed.emit(mode)

    @Property(str, notify=right_joystick_control_changed)
    def right_joystick_control(self) -> str:
        return self._right_joystick_control
    
    @right_joystick_control.setter
    def right_joystick_control(self, mode: str) -> None:
        if self._right_joystick_control != mode:
            self._right_joystick_control = mode
            self.right_joystick_control_changed.emit(mode)

    # Properties for left control info (mode and value)
    @Property(str, notify=left_control_info_changed)
    def left_control_mode(self) -> str:
        return self._left_control_mode
    
    @left_control_mode.setter
    def left_control_mode(self, mode: str) -> None:
        if self._left_control_mode != mode:
            self._left_control_mode = mode
            self.left_control_info_changed.emit(mode, self._left_control_value)

    @Property(str, notify=left_control_info_changed)
    def left_control_value(self) -> str:
        return self._left_control_value
    
    @left_control_value.setter
    def left_control_value(self, value: str) -> None:
        if self._left_control_value != value:
            self._left_control_value = value
            self.left_control_info_changed.emit(self._left_control_mode, value)

    # Properties for right control info (mode and value)
    @Property(str, notify=right_control_info_changed)
    def right_control_mode(self) -> str:
        return self._right_control_mode
    
    @right_control_mode.setter
    def right_control_mode(self, mode: str) -> None:
        if self._right_control_mode != mode:
            self._right_control_mode = mode
            self.right_control_info_changed.emit(mode, self._right_control_value)

    @Property(str, notify=right_control_info_changed)
    def right_control_value(self) -> str:
        return self._right_control_value
    
    @right_control_value.setter
    def right_control_value(self, value: str) -> None:
        if self._right_control_value != value:
            self._right_control_value = value
            self.right_control_info_changed.emit(self._right_control_mode, value)

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

    @Slot()
    def toggle_fullscreen(self):
        """Toggle the video fullscreen overlay"""
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self.get_logger().error('No root QML objects found')
            return
            
        root = root_objects[0]
        # Find the videoFullscreenOverlay by object name
        video_overlay = root.findChild(QObject, "videoFullscreenOverlay")
        
        if video_overlay:
            # Get current active state
            is_active = QQmlProperty.read(video_overlay, "active")
            
            if is_active:
                # If already active, deactivate it
                QQmlProperty.write(video_overlay, "active", False)
                self.get_logger().info('Deactivated fullscreen overlay')
            else:
                # If not active, activate it with the appropriate video source
                # Determine video source based on control mode
                video_source = "image://ef_live/frame" if self._control_mode == "ef" else "image://base_front_live/frame"
                
                QQmlProperty.write(video_overlay, "videoSource", video_source)
                QQmlProperty.write(video_overlay, "active", True)
                self.get_logger().info(f'Activated fullscreen overlay with source: {video_source}')
        else:
            self.get_logger().error('VideoFullscreenOverlay not found in QML')

    @Slot()
    def toggle_lidar_overlay(self):
        """Toggle the LiDAR point cloud overlay"""
        root_objects = self.engine.rootObjects()
        if not root_objects:
            self.get_logger().error('No root QML objects found')
            return
            
        root = root_objects[0]
        # Find the LiDAR overlay by object name (matches QML objectName: "lidarOverlay")
        lidar_overlay = root.findChild(QObject, "lidarOverlay")
        
        if lidar_overlay:
            # Get current active state
            is_active = QQmlProperty.read(lidar_overlay, "active")
            
            if is_active:
                # Deactivate it
                QQmlProperty.write(lidar_overlay, "active", False)
                self.get_logger().info('Deactivated LiDAR overlay')
            else:
                # Activate it
                QQmlProperty.write(lidar_overlay, "active", True)
                self.get_logger().info('Activated LiDAR overlay')
        else:
            self.get_logger().error('LidarOverlay not found in QML')
    
    # Note: The LiDAR overlay automatically updates via QML signal connections
    # when lidar_controller emits points_ready signal, so no manual update methods needed
    
    


    @Slot()
    def update_fullscreen_video_source(self):
        """Update the fullscreen overlay video source based on control mode (if active)"""
        root_objects = self.engine.rootObjects()
        if not root_objects:
            return
            
        root = root_objects[0]
        video_overlay = root.findChild(QObject, "videoFullscreenOverlay")
        
        if video_overlay:
            # Only update if the overlay is currently active
            is_active = QQmlProperty.read(video_overlay, "active")
            
            if is_active:
                # Determine video source based on control mode
                video_source = "image://ef_live/frame" if self._control_mode == "ef" else "image://base_front_live/frame"
                QQmlProperty.write(video_overlay, "videoSource", video_source)
                self.get_logger().info(f'Updated fullscreen video source to: {video_source}')


    def _timer_callback(self):
        """Update UI elements with latest data"""

        # Process control inputs with current state
        input_state = self.steam_deck_handler.get_current_state()
        self.controlProcessor.process_input(input_state)
        
        # Check emergency button state
        self.emergency_handler.check_emergency_button(input_state.get('buttons', {}))


    def _publish_heartbeat(self):
        """Publish a heartbeat message every 0.5 seconds"""
        msg = UInt8()
        msg.data = HeartbeatStatus.IDLE.value  # Indicate the node is alive
        self.heartbeat_pub.publish(msg)
        
    def _setup_subscribers(self):
        # No subscribers currently needed
        pass

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
        return

    @Slot(bool)
    def toggleSwitchChanged(self, checked: bool):
        """Handle toggle switch state change"""
        self.get_logger().info(f'Toggle switch changed to: {checked}')
        # Add specific toggle switch handling logic here

    def cleanup(self):
        """Cleanup all controller resources"""
        # Prevent multiple cleanup attempts
        if self._cleanup_in_progress or self._cleanup_complete:
            return
        
        self._cleanup_in_progress = True
        
        try:
            self.get_logger().info('Starting controller cleanup...')
            
            # Clean up video streams
            if hasattr(self, 'video_stream_handler') and self.video_stream_handler:
                try:
                    self.video_stream_handler.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up video stream handler: {e}")
            
            # Clean up emergency handler
            if hasattr(self, 'emergency_handler') and self.emergency_handler:
                try:
                    self.emergency_handler.reset_state()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up emergency handler: {e}")
            
            # Clean up Steam Deck handler
            if hasattr(self, 'steam_deck_handler') and self.steam_deck_handler:
                try:
                    self.steam_deck_handler.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up steam deck handler: {e}")
            
            # Clean up all sub-controllers
            if hasattr(self, 'winch_controller') and self.winch_controller:
                try:
                    self.winch_controller.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up winch controller: {e}")
            
            if hasattr(self, 'wheel_controller') and self.wheel_controller:
                try:
                    self.wheel_controller.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up wheel controller: {e}")
            
            if hasattr(self, 'wind_monitor') and self.wind_monitor:
                try:
                    self.wind_monitor.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up wind monitor: {e}")
            
            if hasattr(self, 'teensy_controller') and self.teensy_controller:
                try:
                    self.teensy_controller.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up teensy controller: {e}")
            
            if hasattr(self, 'lidar_controller') and self.lidar_controller:
                try:
                    self.lidar_controller.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up lidar controller: {e}")
            
            if hasattr(self, 'ssh_controller') and self.ssh_controller:
                try:
                    self.ssh_controller.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up ssh controller: {e}")
            
            if hasattr(self, 'system_monitor') and self.system_monitor:
                try:
                    self.system_monitor.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up system monitor: {e}")
            
            if hasattr(self, 'ros_bag_recorder') and self.ros_bag_recorder:
                try:
                    self.ros_bag_recorder.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up ros bag recorder: {e}")
            
            if hasattr(self, 'screen_recorder') and self.screen_recorder:
                try:
                    self.screen_recorder.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up screen recorder: {e}")
            
            if hasattr(self, 'workflow_runner') and self.workflow_runner:
                try:
                    self.workflow_runner.cleanup()
                except Exception as e:
                    self.get_logger().error(f"Error cleaning up workflow runner: {e}")

            # Destroy publishers
            if hasattr(self, 'heartbeat_pub') and self.heartbeat_pub:
                try:
                    self.destroy_publisher(self.heartbeat_pub)
                except Exception as e:
                    self.get_logger().error(f"Error destroying heartbeat publisher: {e}")
            
            self.get_logger().info('Controller cleanup complete')
        finally:
            self._cleanup_in_progress = False
            self._cleanup_complete = True

#############################################
### Main Application
#############################################

def main():
    global _app_instance
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize ROS
    rclpy.init()
    
    # Load configuration
    config = ConfigLoader.load_config('robot_config.yaml')
    
    # Create Qt application
    app = QApplication(sys.argv)
    _app_instance = app
    
    # Create robot controller
    controller = RobotController(config)

    
    # Start ROS thread
    ros_thread = RosThread(controller)
    ros_thread.start()
    
    # Setup timer to process Python signals in Qt event loop
    # This allows Ctrl+C to work properly with Qt
    timer = QTimer()
    timer.start(500)  # Check for signals every 500ms
    timer.timeout.connect(lambda: None)  # Just process events
    
    # Setup QML engine
    engine = QQmlApplicationEngine()
    engine.addImageProvider("ef_live", controller.video_stream_handler.ef_image_provider)
    engine.addImageProvider("base_front_live", controller.video_stream_handler.front_image_provider)
    engine.addImageProvider("base_rear_live", controller.video_stream_handler.rear_image_provider)
    
    # Add QML import path for relative imports to resolve
    qml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qml')
    engine.addImportPath(qml_dir)
    
    # Set context properties BEFORE loading QML to avoid "ReferenceError: X is not defined"
    engine.rootContext().setContextProperty("backend", controller)
    engine.rootContext().setContextProperty("baseStreamer", controller)
    engine.rootContext().setContextProperty("overlayController", controller.overlayController)
    engine.rootContext().setContextProperty("workFlowHandler", controller.workFlowHandler)
    engine.rootContext().setContextProperty("workFlowRunner", controller.workflow_runner)
    engine.rootContext().setContextProperty("warningHandler", controller.warningHandler)
    engine.rootContext().setContextProperty("baseStreamHandler", controller.video_stream_handler)
    engine.rootContext().setContextProperty("wheelController", controller.wheel_controller)
    engine.rootContext().setContextProperty("winchController", controller.winch_controller)
    engine.rootContext().setContextProperty("steamDeckHandler", controller.steam_deck_handler)
    engine.rootContext().setContextProperty("windMonitor", controller.wind_monitor)
    engine.rootContext().setContextProperty("teensyController", controller.teensy_controller)
    engine.rootContext().setContextProperty("lidarController", controller.lidar_controller)
    engine.rootContext().setContextProperty("actionConfig", controller.action_config)
    engine.rootContext().setContextProperty("heartbeatHandler", controller.heartbeat_handler)
    engine.rootContext().setContextProperty("controlProcessor", controller.controlProcessor)
    engine.rootContext().setContextProperty("sshHandler", controller.ssh_controller)
    engine.rootContext().setContextProperty("videoStreamer", controller.video_stream_handler)
    engine.rootContext().setContextProperty("systemMonitor", controller.system_monitor)
    engine.rootContext().setContextProperty("screenRecorder", controller.screen_recorder)
    engine.rootContext().setContextProperty("rosBagRecorder", controller.ros_bag_recorder)
    engine.rootContext().setContextProperty("settingsManager", controller.settings_manager)
    controller.engine = engine
    
    # Load QML interface AFTER setting context properties
    qml_path = os.path.join(qml_dir, 'core', 'MainWindow.qml')
    engine.load(QUrl.fromLocalFile(qml_path))
    
    # Start status update timer
    status_timer = QTimer()
    status_timer.timeout.connect(controller.status_updated.emit)
    status_timer.start(int(1000 / config.update_rate))

    heartbeat_timer = QTimer()
    heartbeat_timer.timeout.connect(controller._publish_heartbeat)
    heartbeat_timer.start(500)  # 500 milliseconds = 0.5 seconds
    
    # Start system monitoring (every 1 second)
    controller.system_monitor.start_monitoring(interval_ms=1000)
    
    # Run application
    try:
        sys.exit(app.exec())
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        print("Starting emergency shutdown sequence...")
        
        # Step 1: Stop timers BEFORE cleaning up anything else (must happen from main thread)
        try:
            status_timer.stop()
            heartbeat_timer.stop()
            timer.stop()
        except Exception as e:
            print(f"Error stopping timers: {e}")
        
        # Step 2: Request ROS thread shutdown and wait for it (short timeout)
        try:
            ros_thread.request_shutdown()
            # Wait max 2 seconds for ROS thread to finish (reduced from 3)
            if not ros_thread.wait(2000):
                print("WARNING: ROS thread did not exit cleanly, forcing termination...")
                ros_thread.terminate()
                ros_thread.wait(500)
        except Exception as e:
            print(f"Error shutting down ROS thread: {e}")
        
        # Step 3: Call cleanup on controller (which calls cleanup on all sub-components)
        # Use a timeout to prevent hanging
        try:
            import threading
            cleanup_done = threading.Event()
            
            def do_cleanup():
                try:
                    controller.cleanup()
                    cleanup_done.set()
                except Exception as e:
                    print(f"Error during controller cleanup: {e}")
                    cleanup_done.set()
            
            cleanup_thread = threading.Thread(target=do_cleanup, daemon=True)
            cleanup_thread.start()
            
            # Wait max 3 seconds for cleanup (reduced from infinite)
            if not cleanup_done.wait(timeout=3.0):
                print("WARNING: Controller cleanup timed out, continuing shutdown...")
        except Exception as e:
            print(f"Error during controller cleanup: {e}")
        
        # Step 4: Clean up heartbeat handler (quick operation)
        try:
            controller.heartbeat_handler.cleanup()
        except Exception as e:
            print(f"Error cleaning up heartbeat handler: {e}")
        
        # Step 5: Shutdown ROS context
        try:
            rclpy.shutdown()
        except Exception as e:
            print(f"Error during ROS shutdown: {e}")
        
        print("Emergency shutdown sequence complete")
        
        # Step 6: Force exit if we reach here
        # If app.exec() returned normally, sys.exit() should have been called
        # But if something prevented that, we force exit here
        print("Forcing application exit...")
        os._exit(0)

if __name__ == '__main__':
    main()
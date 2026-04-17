#!/usr/bin/env python3

import sys
import os
import signal
import time
from dataclasses import dataclass
from threading import Lock
import logging
import yaml

logger = logging.getLogger(__name__)

# Force Qt to use X11 backend for VTK compatibility (Wayland issues)
if 'QT_QPA_PLATFORM' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'xcb'

# Disable Linux native virtual keyboard (on-screen keyboard) for text input fields
os.environ['QT_IM_MODULE'] = 'none'

import rclpy
from rclpy.node import Node

from PySide6.QtCore import QTimer, QUrl, Signal, QThread
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from paint_controller.handlers.steam_deck import SteamDeckHandler
from paint_controller.services.video_stream import VideoStreamHandler
from paint_controller.services.base_top_view_service import BaseTopViewService
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

@dataclass
class RobotConfig:
    """Robot configuration parameters"""
    video_port: int = 5000
    update_rate: float = 60.0  # Hz
    joystick_deadzone: float = 0.1

class ConfigLoader:
    @staticmethod
    def load_config(config_path: str) -> RobotConfig:
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return RobotConfig(**config_dict)
        except Exception as e:
            logger.error("Error loading config: %s", e)
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
                        logger.error("Error calling node cleanup method: %s", e)
                
                # Then destroy the node to clean up all ROS resources
                self.node.destroy_node()
                logger.info("ROS node destroyed successfully")
        except Exception as e:
            logger.error("Error during ROS thread cleanup: %s", e)

#############################################
### Main Application
#############################################

def main():
    global _app_instance
    startup_t0 = time.perf_counter()

    def log_startup(stage: str) -> None:
        elapsed_ms = (time.perf_counter() - startup_t0) * 1000.0
        logger.warning("[startup +%7.1f ms] %s", elapsed_ms, stage)
    
    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    log_startup("Signal handlers registered")
    
    # Initialize ROS
    rclpy.init()
    log_startup("ROS initialized")
    
    # Load configuration
    config = ConfigLoader.load_config('robot_config.yaml')
    log_startup("Configuration loaded")
    
    # Create Qt application
    app = QApplication(sys.argv)
    _app_instance = app
    log_startup("QApplication created")

    # --- Core objects ---
    from paint_controller.core.ros_node import PaintRosNode
    from paint_controller.core.state_store import StateStore
    from paint_controller.core.qt_bridge import QtBridge
    from paint_controller.core.controller_factory import create_controllers

    node = PaintRosNode()
    log_startup("PaintRosNode created")
    settings_manager = SettingsManager(show_popup_fn=None)  # Wire show_popup after QtBridge
    state_store = StateStore()
    steam_deck_handler = SteamDeckHandler(deadzone=config.joystick_deadzone)
    log_startup("Core state/services created")

    # Video & camera services
    video_stream_handler = VideoStreamHandler(config.video_port, ros_node=node)
    base_top_view_service = BaseTopViewService(video_stream_handler, settings_manager=settings_manager)
    log_startup("Video and camera services created")

    steam_deck_handler.start()
    log_startup("Steam Deck handler started")

    # Start ROS thread
    ros_thread = RosThread(node)
    ros_thread.start()
    log_startup("ROS thread started")

    # Timer to process Python signals in Qt event loop (Ctrl+C handling)
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)
    log_startup("Qt signal timer started")

    # --- QML engine ---
    engine = QQmlApplicationEngine()
    engine.addImageProvider("ef_live", video_stream_handler.ef_image_provider)
    engine.addImageProvider("base_front_live", video_stream_handler.front_image_provider)
    engine.addImageProvider("base_rear_live", video_stream_handler.rear_image_provider)
    engine.addImageProvider("base_top_view", base_top_view_service.image_provider)
    log_startup("QML engine and image providers ready")

    qml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'qml')
    engine.addImportPath(qml_dir)

    # Create Qt bridge (needs engine for QML access)
    qt_bridge = QtBridge(engine, state_store, logger=node.get_logger())
    log_startup("Qt bridge created")

    # Wire deferred show_popup to settings_manager
    settings_manager._show_popup_fn = qt_bridge.show_popup

    # --- Create all controllers via factory ---
    bundle = create_controllers(
        node=node,
        settings_manager=settings_manager,
        state_store=state_store,
        steam_deck_handler=steam_deck_handler,
        show_popup_fn=qt_bridge.show_popup,
        close_popup_fn=qt_bridge.close_popup,
        config=config,
    )
    log_startup("Controller bundle created")

    # Deferred wiring
    qt_bridge.set_base_top_view_service(base_top_view_service)
    qt_bridge.set_input_handler(bundle.input_handler)

    # --- Steam Deck button callbacks ---
    ih = bundle.input_handler
    steam_deck_handler.register_button_callback('up', ih.on_up_pressed)
    steam_deck_handler.register_button_callback('down', ih.on_down_pressed)
    steam_deck_handler.register_button_callback('left', ih.on_left_pressed)
    steam_deck_handler.register_button_callback('right', ih.on_right_pressed)
    steam_deck_handler.register_button_callback('r4', ih.on_r4_pressed)
    steam_deck_handler.register_button_callback('l4', ih.on_l4_pressed)
    steam_deck_handler.register_button_callback('menu', ih.on_menu_pressed)
    steam_deck_handler.register_button_callback('switch', ih.on_switch_pressed)
    steam_deck_handler.register_button_callback('l5', ih.on_l5_pressed)
    steam_deck_handler.register_button_callback('r5', ih.on_r5_pressed)
    steam_deck_handler.register_button_callback('dot', qt_bridge.toggle_fullscreen)
    steam_deck_handler.register_button_callback('a', qt_bridge.toggle_lidar_overlay)
    steam_deck_handler.register_button_callback('l1', ih.on_l1_pressed)

    # --- Signal wiring ---
    state_store.control_mode_changed.connect(qt_bridge.update_fullscreen_video_source)
    bundle.emergency_handler.overlay_changed.connect(qt_bridge.emergency_overlay_changed.emit)
    bundle.emergency_handler.emergency_triggered.connect(qt_bridge.emergency_triggered.emit)
    video_stream_handler.endEffectorFrameReady.connect(qt_bridge.frame_ready.emit)

    # Wheel motor error → emergency stop + popup
    def _handle_wheel_motor_error(has_error, error_message):
        if has_error:
            node.get_logger().error(f'Wheel motor error detected: {error_message}')
            bundle.wheel_controller.emergency_stop()
            bundle.winch_controller.command_speed_rpm(0)
            bundle.teensy_controller.setSprayTrigger(1000)
            qt_bridge.show_popup("MOTOR ERROR", error_message, "error", 5000)
            qt_bridge.emergency_triggered.emit()

    bundle.wheel_controller.error_state_changed.connect(_handle_wheel_motor_error)

    # Timer callback: process controller inputs
    def _timer_callback():
        input_state = steam_deck_handler.get_current_state()
        bundle.control_processor.process_input(input_state)
        bundle.emergency_handler.check_emergency_button(input_state.get('buttons', {}))

    qt_bridge.status_updated.connect(_timer_callback)

    # --- QML context properties ---
    ctx = engine.rootContext()
    ctx.setContextProperty("stateStore", state_store)
    ctx.setContextProperty("backend", qt_bridge)
    ctx.setContextProperty("overlayController", bundle.overlay_controller)
    ctx.setContextProperty("workFlowHandler", bundle.workflow_handler)
    ctx.setContextProperty("workFlowRunner", bundle.workflow_runner)
    ctx.setContextProperty("warningHandler", bundle.warning_handler)
    ctx.setContextProperty("baseStreamHandler", video_stream_handler)
    ctx.setContextProperty("wheelController", bundle.wheel_controller)
    ctx.setContextProperty("winchController", bundle.winch_controller)
    ctx.setContextProperty("steamDeckHandler", steam_deck_handler)
    ctx.setContextProperty("windMonitor", bundle.wind_monitor)
    ctx.setContextProperty("teensyController", bundle.teensy_controller)
    ctx.setContextProperty("esp32ValveController", bundle.esp32_valve_controller)
    ctx.setContextProperty("lidarController", bundle.lidar_controller)
    ctx.setContextProperty("actionConfig", bundle.action_config)
    ctx.setContextProperty("heartbeatHandler", bundle.heartbeat_handler)
    ctx.setContextProperty("controlProcessor", bundle.control_processor)
    ctx.setContextProperty("sshHandler", bundle.ssh_controller)
    ctx.setContextProperty("systemMonitor", bundle.system_monitor)
    ctx.setContextProperty("screenRecorder", bundle.screen_recorder)
    ctx.setContextProperty("rosBagRecorder", bundle.ros_bag_recorder)
    ctx.setContextProperty("settingsManager", settings_manager)
    ctx.setContextProperty("screenManager", bundle.screen_manager)
    ctx.setContextProperty("baseTopViewController", base_top_view_service)

    # Load QML interface AFTER setting context properties
    qml_path = os.path.join(qml_dir, 'core', 'MainWindow.qml')
    engine.load(QUrl.fromLocalFile(qml_path))
    log_startup("MainWindow QML loaded")

    # Validate all context properties are set (catches typos / missing wiring)
    _EXPECTED_CONTEXT_PROPERTIES = [
        "stateStore", "backend", "overlayController", "workFlowHandler",
        "workFlowRunner", "warningHandler", "baseStreamHandler",
        "wheelController", "winchController", "steamDeckHandler",
        "windMonitor", "teensyController", "esp32ValveController",
        "lidarController", "actionConfig", "heartbeatHandler",
        "controlProcessor", "sshHandler", "systemMonitor",
        "screenRecorder", "rosBagRecorder", "settingsManager",
        "screenManager", "baseTopViewController",
    ]
    for name in _EXPECTED_CONTEXT_PROPERTIES:
        if ctx.contextProperty(name) is None:
            node.get_logger().error(f"Missing QML context property: {name}")

    # --- Timers ---
    status_timer = QTimer()
    status_timer.timeout.connect(qt_bridge.status_updated.emit)
    status_timer.start(int(1000 / config.update_rate))

    heartbeat_timer = QTimer()
    heartbeat_timer.timeout.connect(node.publish_heartbeat)
    heartbeat_timer.start(500)
    log_startup("Status and heartbeat timers started")

    # Start system monitoring
    bundle.system_monitor.start_monitoring(interval_ms=1000)
    log_startup("System monitoring started")

    def _deferred_video_startup() -> None:
        log_startup("Deferred video startup begin")
        started_count = video_stream_handler.start_all_streams()
        log_startup(f"Deferred video startup end: started {started_count} stream(s)")

    QTimer.singleShot(200, _deferred_video_startup)
    log_startup("Deferred video startup scheduled")

    # --- Run ---
    try:
        log_startup("Entering Qt event loop")
        sys.exit(app.exec())
    except Exception as e:
        logger.error("Application error: %s", e)
        import traceback
        traceback.print_exc()
    finally:
        shutdown_t0 = time.perf_counter()

        def log_shutdown(stage: str) -> None:
            elapsed_ms = (time.perf_counter() - shutdown_t0) * 1000.0
            logger.warning("[shutdown +%7.1f ms] %s", elapsed_ms, stage)

        logger.info("Starting emergency shutdown sequence...")
        log_shutdown("Shutdown sequence started")

        # Step 1: Stop timers
        try:
            status_timer.stop()
            heartbeat_timer.stop()
            timer.stop()
            log_shutdown("Qt timers stopped")
        except Exception as e:
            logger.error("Error stopping timers: %s", e)

        # Step 2: Request ROS thread shutdown and wait
        try:
            ros_thread.request_shutdown()
            if not ros_thread.wait(2000):
                logger.warning("ROS thread did not exit cleanly, forcing termination...")
                ros_thread.terminate()
                ros_thread.wait(500)
            log_shutdown("ROS thread stopped")
        except Exception as e:
            logger.error("Error shutting down ROS thread: %s", e)

        # Step 3: Cleanup controllers
        try:
            bundle.cleanup(node.get_logger())
            log_shutdown("Controller bundle cleaned up")
            base_top_view_service.cleanup()
            log_shutdown("Base top view service cleaned up")
            video_stream_handler.cleanup()
            log_shutdown("Video stream handler cleaned up")
            steam_deck_handler.cleanup()
            log_shutdown("Steam Deck handler cleaned up")
        except Exception as e:
            logger.error("Error during cleanup: %s", e)

        # Step 4: Shutdown ROS context
        try:
            rclpy.shutdown()
            log_shutdown("ROS context shutdown complete")
        except Exception as e:
            logger.error("Error during ROS shutdown: %s", e)

        logger.info("Emergency shutdown sequence complete")
        logger.info("Forcing application exit...")
        os._exit(0)

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Paint Controller Application

Main application class that manages the lifecycle and wiring of
the paint controller application using dependency injection.
"""

import os
import sys
import signal
import time
import threading
from typing import Optional

from paint_controller.core.service_container import ServiceContainer
from paint_controller.core.ros_manager import ROSManager
from paint_controller.core.qt_manager import QtManager
from paint_controller.core.resource_manager import ResourceTracker
from paint_controller.core.application import (
    RobotController, ConfigLoader, RobotConfig, _app_instance
)


class PaintControllerApplication:
    """
    Main application class for Paint Controller.
    
    Manages application lifecycle using dependency injection and
    separation of concerns. Replaces the large main() function with
    a structured approach.
    
    Example:
        app = PaintControllerApplication()
        app.initialize()
        exit_code = app.run()
    """
    
    def __init__(self):
        self._service_container = ServiceContainer()
        self._ros_manager = None
        self._qt_manager = None
        self._resource_tracker = ResourceTracker()
        self._controller = None
        self._config = None
        self._initialized = False
        
        # Global reference for signal handler
        global _app_instance
        self._global_app_ref = None
    
    def initialize(self, config_path: str = 'robot_config.yaml') -> None:
        """
        Initialize the application.
        
        Sets up ROS, Qt, services, and all components.
        
        Args:
            config_path: Path to robot configuration file
        """
        if self._initialized:
            print("Application already initialized")
            return
        
        print("Initializing Paint Controller Application...")
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Load configuration
        self._config = ConfigLoader.load_config(config_path)
        print(f"Configuration loaded from {config_path}")
        
        # Initialize ROS
        self._ros_manager = ROSManager()
        self._ros_manager.initialize()
        
        # Initialize Qt
        self._qt_manager = QtManager()
        self._qt_manager.initialize()
        
        # Set global app reference for signal handler
        global _app_instance
        _app_instance = self._qt_manager.app
        self._global_app_ref = _app_instance
        
        # Register core services
        self._register_services()
        
        # Create controller (still using RobotController for now)
        self._setup_controller()
        
        # Start ROS thread
        self._start_ros_thread()
        
        # Setup Qt/QML
        self._setup_qt()
        
        # Setup timers
        self._setup_timers()
        
        # Start services
        self._start_services()
        
        self._initialized = True
        print("Application initialized successfully")
    
    def _register_services(self) -> None:
        """Register services in the dependency injection container"""
        # For Phase 1, we keep the existing RobotController pattern
        # Future phases will extract more services here
        pass
    
    def _setup_controller(self) -> None:
        """Create and setup the robot controller"""
        # For Phase 1, we still create RobotController directly
        # Future phases will use dependency injection more extensively
        self._controller = RobotController(self._config)
        print("Robot controller created")
    
    def _start_ros_thread(self) -> None:
        """Start ROS spinning in separate thread"""
        ros_thread = self._ros_manager.start_thread(self._controller)
        
        # Setup timer to process Python signals in Qt event loop
        # This allows Ctrl+C to work properly with Qt
        self._qt_manager.create_timer(
            'signal_processor',
            500,  # Check for signals every 500ms
            lambda: None  # Just process events
        )
    
    def _setup_qt(self) -> None:
        """Setup Qt/QML engine"""
        engine = self._qt_manager.engine
        
        # Add image providers
        engine.addImageProvider("ef_live", 
            self._controller.video_stream_handler.ef_image_provider)
        engine.addImageProvider("base_front_live", 
            self._controller.video_stream_handler.front_image_provider)
        engine.addImageProvider("base_rear_live", 
            self._controller.video_stream_handler.rear_image_provider)
        engine.addImageProvider("bird_view", 
            self._controller.bird_view_service.image_provider)
        
        # Add QML import path
        qml_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'qml'
        )
        engine.addImportPath(qml_dir)
        
        # Register all context properties
        self._register_context_properties()
        
        # Set engine reference on controller (for show_popup etc)
        self._controller.engine = engine
        
        # Load QML
        qml_path = os.path.join(qml_dir, 'core', 'MainWindow.qml')
        if not self._qt_manager.load_qml(qml_path):
            raise RuntimeError(f"Failed to load QML from {qml_path}")
    
    def _register_context_properties(self) -> None:
        """Register all context properties for QML"""
        properties = {
            "backend": self._controller,
            "baseStreamer": self._controller,
            "overlayController": self._controller.overlayController,
            "workFlowHandler": self._controller.workFlowHandler,
            "workFlowRunner": self._controller.workflow_runner,
            "warningHandler": self._controller.warningHandler,
            "baseStreamHandler": self._controller.video_stream_handler,
            "wheelController": self._controller.wheel_controller,
            "winchController": self._controller.winch_controller,
            "steamDeckHandler": self._controller.steam_deck_handler,
            "windMonitor": self._controller.wind_monitor,
            "teensyController": self._controller.teensy_controller,
            "esp32ValveController": self._controller.esp32_valve_controller,
            "lidarController": self._controller.lidar_controller,
            "actionConfig": self._controller.action_config,
            "heartbeatHandler": self._controller.heartbeat_handler,
            "controlProcessor": self._controller.controlProcessor,
            "sshHandler": self._controller.ssh_controller,
            "videoStreamer": self._controller.video_stream_handler,
            "systemMonitor": self._controller.system_monitor,
            "screenRecorder": self._controller.screen_recorder,
            "rosBagRecorder": self._controller.ros_bag_recorder,
            "settingsManager": self._controller.settings_manager,
            "screenManager": self._controller.screen_manager,
            "birdViewController": self._controller.bird_view_service,
        }
        
        self._qt_manager.register_multiple_context_properties(properties)
        print(f"Registered {len(properties)} context properties for QML")
    
    def _setup_timers(self) -> None:
        """Setup application timers"""
        # Status update timer
        update_interval = int(1000 / self._config.update_rate)
        self._qt_manager.create_timer(
            'status_update',
            update_interval,
            self._controller.status_updated.emit
        )
        
        # Heartbeat timer
        self._qt_manager.create_timer(
            'heartbeat',
            500,
            self._controller._publish_heartbeat
        )
    
    def _start_services(self) -> None:
        """Start background services"""
        # Start system monitoring
        self._controller.system_monitor.start_monitoring(interval_ms=1000)
        print("Services started")
    
    def run(self) -> int:
        """
        Run the application.
        
        Blocks until the application exits.
        
        Returns:
            Application exit code
        """
        if not self._initialized:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        
        print("Starting application...")
        
        try:
            return self._qt_manager.exec()
        except Exception as e:
            print(f"Application error: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self) -> None:
        """
        Cleanup application resources.
        
        Called automatically on exit, but can also be called manually.
        """
        print("Starting application cleanup...")
        
        # Step 1: Stop timers (must happen from main thread)
        if self._qt_manager:
            self._qt_manager.stop_all_timers()
        
        # Step 2: Shutdown ROS thread
        if self._ros_manager:
            self._ros_manager.shutdown(timeout_ms=2000)
        
        # Step 3: Cleanup controller with timeout
        if self._controller:
            try:
                cleanup_done = threading.Event()
                
                def do_cleanup():
                    try:
                        self._controller.cleanup()
                        cleanup_done.set()
                    except Exception as e:
                        print(f"Error during controller cleanup: {e}")
                        cleanup_done.set()
                
                cleanup_thread = threading.Thread(target=do_cleanup, daemon=True)
                cleanup_thread.start()
                
                # Wait max 3 seconds for cleanup
                if not cleanup_done.wait(timeout=3.0):
                    print("WARNING: Controller cleanup timed out")
            except Exception as e:
                print(f"Error during controller cleanup: {e}")
        
        # Step 4: Cleanup heartbeat handler
        if self._controller and hasattr(self._controller, 'heartbeat_handler'):
            try:
                self._controller.heartbeat_handler.cleanup()
            except Exception as e:
                print(f"Error cleaning up heartbeat handler: {e}")
        
        # Step 5: Cleanup Qt
        if self._qt_manager:
            self._qt_manager.cleanup()
        
        # Step 6: Cleanup service container
        self._service_container.cleanup_all()
        
        # Step 7: Cleanup resource tracker
        self._resource_tracker.cleanup_all()
        
        print("Application cleanup complete")
    
    def _signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl+C) gracefully"""
        print("\n\nReceived interrupt signal...")
        print("Requesting shutdown...")
        
        # Request Qt app to quit
        if self._qt_manager:
            self._qt_manager.quit()
        
        # If shutdown doesn't happen quickly, force exit
        def force_exit():
            time.sleep(2)
            print("Forcing immediate shutdown...")
            os._exit(1)
        
        force_thread = threading.Thread(target=force_exit, daemon=True)
        force_thread.start()

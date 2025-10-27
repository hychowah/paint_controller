"""
CRITICAL FIX #1: ROS Thread Race Condition
File: python/paint_controller.py - RosThread class

This demonstrates the correct implementation of the RosThread class
with proper synchronization and error handling.
"""

from threading import Lock, Event
from rclpy.node import Node
from PySide6.QtCore import QThread, Signal
import rclpy


class RosThread(QThread):
    """Thread-safe ROS event loop with proper shutdown handling"""
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
        self._shutdown_event = Event()  # Better than atomic bool
        self._is_running = False
        self._lock = Lock()
        self._ros_context_valid = True

    def run(self) -> None:
        """
        Run the ROS event loop in a separate thread with proper error handling.
        """
        try:
            self._is_running = True
            self.node_started.emit()
            
            while not self._shutdown_event.is_set():
                try:
                    # Check ROS context validity inside lock
                    with self._lock:
                        if not rclpy.ok():
                            self.error_occurred.emit("ROS context is not valid")
                            break
                    
                    # Spin with timeout
                    rclpy.spin_once(self.node, timeout_sec=0.1)
                    
                except RuntimeError as e:
                    # ROS-specific errors
                    error_msg = f"ROS runtime error: {str(e)}"
                    self.get_logger().error(error_msg)
                    self.error_occurred.emit(error_msg)
                    break
                except Exception as e:
                    # Unexpected errors
                    error_msg = f"Unexpected error in ROS spin: {str(e)}"
                    self.get_logger().error(error_msg)
                    self.error_occurred.emit(error_msg)
                    break
            
            self._cleanup()
            
        except Exception as e:
            self.error_occurred.emit(f"ROS thread fatal error: {str(e)}")
        finally:
            self._is_running = False
            self.node_stopped.emit()

    def request_shutdown(self) -> None:
        """
        Request thread shutdown (non-blocking).
        
        Can be safely called from any thread.
        """
        self._shutdown_event.set()

    def _cleanup(self) -> None:
        """
        Clean up ROS node resources properly.
        """
        try:
            if self.node:
                self.node.destroy_node()
                self.node.get_logger().info("ROS node destroyed")
        except Exception as e:
            self.error_occurred.emit(f"Error destroying node: {str(e)}")

    def get_logger(self):
        """Helper to get node logger"""
        if self.node:
            return self.node.get_logger()
        return None


# ============================================================================
# USAGE in main():
# ============================================================================

def main_improved():
    """Improved main function with proper ROS thread handling"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    # Initialize ROS
    rclpy.init()
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Create controller
        controller = RobotController(config)
        
        # Start ROS thread
        ros_thread = RosThread(controller)
        ros_thread.error_occurred.connect(on_ros_error)
        ros_thread.node_stopped.connect(on_ros_stopped)
        ros_thread.start()
        
        # Setup QML engine
        engine = QQmlApplicationEngine()
        engine.load(QUrl.fromLocalFile(qml_path))
        
        # Setup timers with error handling
        status_timer = QTimer()
        status_timer.timeout.connect(lambda: safe_timer_callback(controller))
        status_timer.start(int(1000 / config.update_rate))
        
        # Run application
        exit_code = app.exec()
        
    except Exception as e:
        print(f"Fatal error during startup: {e}")
        exit_code = 1
    finally:
        # Graceful shutdown sequence
        try:
            print("Initiating graceful shutdown...")
            
            # Request ROS thread shutdown
            ros_thread.request_shutdown()
            
            # Wait with timeout
            print("Waiting for ROS thread to stop...")
            if ros_thread.wait(msecs=5000):
                print("ROS thread stopped successfully")
            else:
                print("WARNING: ROS thread did not stop gracefully, terminating...")
                ros_thread.terminate()
                ros_thread.wait(msecs=1000)
            
            # Shutdown ROS
            print("Shutting down ROS context...")
            rclpy.shutdown()
            
            print("Shutdown complete")
        except Exception as e:
            print(f"Error during shutdown: {e}")
        
        sys.exit(exit_code)


def safe_timer_callback(controller):
    """Timer callback with exception handling"""
    try:
        input_state = controller.steam_deck_handler.get_current_state()
        if input_state:
            controller.controlProcessor.process_input(input_state)
            controller.emergency_handler.check_emergency_button(input_state.get('buttons', {}))
    except Exception as e:
        controller.get_logger().error(f"Timer callback error: {e}")


def on_ros_error(error_msg):
    """Handle ROS thread errors"""
    print(f"ROS thread error: {error_msg}")
    # Could trigger UI notification or graceful shutdown


def on_ros_stopped():
    """Handle ROS thread stopped"""
    print("ROS thread has stopped")

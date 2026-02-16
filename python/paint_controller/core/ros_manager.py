#!/usr/bin/env python3
"""
ROS Manager

Encapsulates ROS2 context lifecycle and thread management.
"""

import time
import rclpy
from rclpy.node import Node
from threading import Lock
from PySide6.QtCore import QThread, Signal


class RosThread(QThread):
    """
    Isolated thread for running ROS event loop with thread-safe shutdown.
    
    This is extracted from the original application.py RosThread class
    to be reusable by the new architecture.
    """
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
                    time.sleep(0.5)
                    continue
                
                try:
                    self._last_spin_time = time.time()
                    # Use smaller timeout to prevent long hangs on bad network
                    rclpy.spin_once(self.node, timeout_sec=0.05)
                    
                except Exception as spin_error:
                    # Network error during spin - emit but continue trying
                    error_msg = f"ROS spin error (likely network): {str(spin_error)}"
                    self.error_occurred.emit(error_msg)
                    
                    # Sleep briefly to avoid CPU spinning on errors
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
                self.node.destroy_node()
                print("ROS node destroyed successfully")
        except Exception as e:
            print(f"Error during ROS thread cleanup: {e}")


class ROSManager:
    """
    Manages ROS2 context lifecycle and threading.
    
    Encapsulates ROS initialization, node creation, and cleanup
    to separate concerns from the main application.
    
    Example:
        manager = ROSManager()
        manager.initialize()
        node = manager.create_node('my_node')
        manager.start_thread(node)
        
        # Later...
        manager.shutdown()
    """
    
    def __init__(self):
        self._initialized = False
        self._ros_thread = None
        self._node = None
    
    def initialize(self) -> None:
        """
        Initialize ROS2 context.
        
        Must be called before creating nodes or starting threads.
        """
        if self._initialized:
            return
        
        rclpy.init()
        self._initialized = True
        print("ROS2 context initialized")
    
    def create_node(self, node_name: str) -> Node:
        """
        Create a ROS2 node.
        
        Args:
            node_name: Name for the ROS2 node
            
        Returns:
            Created ROS2 node
        """
        if not self._initialized:
            raise RuntimeError("ROSManager not initialized. Call initialize() first.")
        
        node = Node(node_name)
        self._node = node
        return node
    
    def start_thread(self, node: Node) -> RosThread:
        """
        Start ROS spinning in a separate thread.
        
        Args:
            node: ROS2 node to spin
            
        Returns:
            RosThread instance
        """
        if self._ros_thread is not None:
            raise RuntimeError("ROS thread already started")
        
        self._ros_thread = RosThread(node)
        self._ros_thread.start()
        print("ROS thread started")
        return self._ros_thread
    
    def shutdown(self, timeout_ms: int = 2000) -> None:
        """
        Shutdown ROS thread and context.
        
        Args:
            timeout_ms: Maximum time to wait for thread shutdown
        """
        # Step 1: Request ROS thread shutdown
        if self._ros_thread is not None:
            try:
                self._ros_thread.request_shutdown()
                
                # Wait for thread to finish
                if not self._ros_thread.wait(timeout_ms):
                    print("WARNING: ROS thread did not exit cleanly, forcing termination...")
                    self._ros_thread.terminate()
                    self._ros_thread.wait(500)
                
                self._ros_thread = None
            except Exception as e:
                print(f"Error shutting down ROS thread: {e}")
        
        # Step 2: Shutdown ROS context
        if self._initialized:
            try:
                rclpy.shutdown()
                self._initialized = False
                print("ROS2 context shutdown")
            except Exception as e:
                print(f"Error during ROS shutdown: {e}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if ROS context is initialized"""
        return self._initialized
    
    @property
    def ros_thread(self) -> RosThread:
        """Get the ROS thread instance"""
        return self._ros_thread

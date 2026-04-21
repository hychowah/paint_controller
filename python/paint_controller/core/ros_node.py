"""ROS2 node and ROS-thread primitives."""

from __future__ import annotations

import time
from threading import Lock
from typing import Optional

import rclpy
from PySide6.QtCore import QThread, Signal
from rclpy.node import Node
from std_msgs.msg import UInt8

from paint_controller.core.state_store import StateStore
from paint_controller.utils.constants import HeartbeatStatus

class PaintRosNode(Node):
    """ROS2 node for the paint controller. Owns heartbeat publisher."""

    def __init__(self, state_store: Optional[StateStore] = None, node_name: str = 'robot_controller'):
        super().__init__(node_name)
        self._state_store = state_store
        self.heartbeat_pub = self.create_publisher(UInt8, '/controller/heartbeat', 10)
        self._cleanup_done = False

    def publish_heartbeat(self):
        msg = UInt8()
        heartbeat_state = HeartbeatStatus.IDLE
        if self._state_store is not None:
            try:
                heartbeat_state = HeartbeatStatus(self._state_store.controller_heartbeat_state)
            except (TypeError, ValueError):
                heartbeat_state = HeartbeatStatus.IDLE
        msg.data = int(heartbeat_state)
        self.heartbeat_pub.publish(msg)

    def cleanup(self):
        if self._cleanup_done:
            return
        self._cleanup_done = True
        try:
            self.destroy_publisher(self.heartbeat_pub)
            self.get_logger().info('PaintRosNode cleanup complete')
        except Exception as e:
            self.get_logger().error(f'Error during PaintRosNode cleanup: {e}')


class RosThread(QThread):
    """Isolated thread for running the ROS event loop with thread-safe shutdown."""

    error_occurred = Signal(str)
    node_started = Signal()
    node_stopped = Signal()

    def __init__(self, node: Node):
        super().__init__()
        self.node = node
        self._running = False
        self._shutdown_requested = False
        self._lock = Lock()
        self._last_spin_time = 0.0
        self._spin_timeout = 5.0

    def run(self) -> None:
        try:
            self._running = True
            self.node_started.emit()

            while True:
                with self._lock:
                    if self._shutdown_requested:
                        break

                if not rclpy.ok():
                    self.error_occurred.emit(
                        "ROS context is not valid - network may be disconnected"
                    )
                    time.sleep(0.5)
                    continue

                try:
                    self._last_spin_time = time.time()
                    rclpy.spin_once(self.node, timeout_sec=0.05)
                except Exception as spin_error:
                    self.error_occurred.emit(
                        f"ROS spin error (likely network): {spin_error}"
                    )
                    time.sleep(0.1)

            self._cleanup()
        except Exception as error:
            self.error_occurred.emit(f"Critical ROS thread error: {error}")
            self._cleanup()
        finally:
            self._running = False
            self.node_stopped.emit()

    def request_shutdown(self) -> None:
        with self._lock:
            self._shutdown_requested = True

    def _cleanup(self) -> None:
        try:
            self.node.get_logger().info('ROS thread spin loop exited')
        except Exception as error:
            self.node.get_logger().error(f'Error during ROS thread cleanup: {error}')

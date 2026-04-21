"""Pure ROS2 node — no Qt dependencies."""

from __future__ import annotations

from typing import Optional

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

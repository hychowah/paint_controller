"""Pure ROS2 node — no Qt dependencies."""

from rclpy.node import Node
from std_msgs.msg import UInt8


class HeartbeatStatus:
    IDLE = 0x00
    ONTASK = 0x01
    WARNING = 0x02
    ERROR = 0x03


class PaintRosNode(Node):
    """ROS2 node for the paint controller. Owns heartbeat publisher."""

    def __init__(self, node_name: str = 'robot_controller'):
        super().__init__(node_name)
        self.heartbeat_pub = self.create_publisher(UInt8, '/controller/heartbeat', 10)
        self._cleanup_done = False

    def publish_heartbeat(self):
        msg = UInt8()
        msg.data = HeartbeatStatus.IDLE
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

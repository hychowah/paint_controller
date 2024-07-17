#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from teknic_interfaces.msg import TeknicStatus

class TestSubscriber(Node):
    def __init__(self):
        super().__init__('test_subscriber')
        self.subscription = self.create_subscription(
            TeknicStatus,
            'teknicStatus',
            self.listener_callback,
            10)
        self.get_logger().info("Subscribed to teknicStatus topic")

    def listener_callback(self, msg):
        self.get_logger().info(f'Received motor feedback: {msg}')

def main(args=None):
    rclpy.init(args=args)
    node = TestSubscriber()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

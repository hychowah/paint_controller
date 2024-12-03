import rclpy
from rclpy.node import Node
from towngas_interfaces.msg import WheelStatus
import random

class FakeWheelStatusPublisher(Node):
    def __init__(self):
        super().__init__('fake_wheel_status_publisher')
        self.publisher_ = self.create_publisher(WheelStatus, 'wheel_motor_status', 10)
        self.timer = self.create_timer(0.1, self.publish_fake_data)  # Publish every 0.1 seconds
        # Initialize the values
        self.left_wheel_speed = 0.0
        self.right_wheel_speed = 0.0
        self.left_wheel_current = 0.0
        self.right_wheel_current = 0.0

    def random_walk(self, value, step, lower_bound, upper_bound):
        new_value = value + random.uniform(-step, step)
        return max(min(new_value, upper_bound), lower_bound)

    def publish_fake_data(self):
        msg = WheelStatus()
        # Update values with bounded random walk
        self.left_wheel_speed = self.random_walk(self.left_wheel_speed, random.uniform(-5, 5), -40, 40)
        self.right_wheel_speed = self.random_walk(self.right_wheel_speed, random.uniform(-5, 5), -40, 40)
        self.left_wheel_current = self.random_walk(self.left_wheel_current, random.uniform(-1, 1), -6, 6)
        self.right_wheel_current = self.random_walk(self.right_wheel_current, random.uniform(-1, 1), -6, 6)

        # Assign values to message, explicitly converting to float
        msg.left_wheel_speed = float(self.left_wheel_speed)
        msg.right_wheel_speed = float(self.right_wheel_speed)
        msg.left_wheel_current = float(self.left_wheel_current)
        msg.right_wheel_current = float(self.right_wheel_current)

        # Publish the message
        self.publisher_.publish(msg)

        # Log the published publish_fake_data
        # self.get_logger().info(f'Publishing: '
          #                     f'Left Speed: {self.left_wheel_speed:.2f}, '
          #                     f'Right Speed: {self.right_wheel_speed:.2f}, '
          #                     f'Left Current: {self.left_wheel_current:.2f}, '
          #                     f'Right Current: {self.right_wheel_current:.2f}')

def main(args=None):
    rclpy.init(args=args)
    fake_publisher = FakeWheelStatusPublisher()
    rclpy.spin(fake_publisher)
    fake_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

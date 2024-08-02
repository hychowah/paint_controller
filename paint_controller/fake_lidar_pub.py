import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import math
import random
import array

class FakeLidarPublisher(Node):
    def __init__(self):
        super().__init__('fake_lidar_publisher')
        self.publisher_ = self.create_publisher(LaserScan, '/scan', 10)
        self.timer = self.create_timer(0.02, self.publish_scan)  # 10 Hz
        
        self.angle_min = -math.pi
        self.angle_max = math.pi
        self.num_readings = 1000  # Set to 360 points
        self.angle_increment = (self.angle_max - self.angle_min) / self.num_readings
        self.range_min = 0.05
        self.range_max = 40.0
        
        # Initialize with random values
        self.last_ranges = [random.uniform(self.range_min, self.range_max) for _ in range(self.num_readings)]

    def publish_scan(self):
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = 'laser'
        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = self.angle_increment
        scan.time_increment = 9.331268665846437e-05
        scan.scan_time = 0.10068438947200775
        scan.range_min = self.range_min
        scan.range_max = self.range_max
        
        # Generate new ranges with random increments following normal distribution
        new_ranges = array.array('f')
        for last_range in self.last_ranges:
            increment = random.gauss(0, 0.05)  # Mean 0, standard deviation 0.5
            new_range = max(min(last_range + increment, self.range_max), self.range_min)
            new_ranges.append(new_range)
        
        scan.ranges = new_ranges
        self.last_ranges = list(new_ranges)
        
        # Generate random intensities following normal distribution
        intensities = array.array('f')
        for _ in range(self.num_readings):
            intensity = max(0, random.gauss(23.5, 7.8))
            intensities.append(intensity)
        
        scan.intensities = intensities
        
        self.publisher_.publish(scan)
        self.get_logger().info('Publishing fake LiDAR scan with 360 points')

def main(args=None):
    rclpy.init(args=args)
    fake_lidar_publisher = FakeLidarPublisher()
    rclpy.spin(fake_lidar_publisher)
    fake_lidar_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
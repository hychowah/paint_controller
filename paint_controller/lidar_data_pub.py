import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
import csv
import os
import time
import argparse
from glob import glob

class LidarDataPublisher(Node):
    def __init__(self, data_dir, file_format='npy', publish_rate=10.0, skip_entries=0):
        super().__init__('lidar_data_publisher')
        self.publisher = self.create_publisher(LaserScan, '/scan', 10)
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_data)
        
        self.data_dir = data_dir
        self.file_format = file_format
        self.files = sorted(glob(os.path.join(data_dir, f'*.{file_format}')))
        self.current_file_index = 0
        self.current_data = None
        self.current_data_index = 0
        self.skip_entries = skip_entries
        self.total_entries_skipped = 0
        
        self.get_logger().info(f'Found {len(self.files)} files to publish')
        self.load_next_file()

    def load_next_file(self):
        if self.current_file_index < len(self.files):
            filename = self.files[self.current_file_index]
            self.get_logger().info(f'Loading file: {filename}')
            
            if self.file_format == 'npy':
                full_data = np.load(filename, allow_pickle=True)
                if self.total_entries_skipped < self.skip_entries:
                    entries_to_skip = min(len(full_data), self.skip_entries - self.total_entries_skipped)
                    self.current_data = full_data[entries_to_skip:]
                    self.total_entries_skipped += entries_to_skip
                else:
                    self.current_data = full_data
            elif self.file_format == 'csv':
                with open(filename, 'r') as f:
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    if self.total_entries_skipped < self.skip_entries:
                        # Skip required number of entries
                        for _ in range(min(self.skip_entries - self.total_entries_skipped, sum(1 for _ in reader))):
                            next(reader)
                            self.total_entries_skipped += 1
                        f.seek(0)
                        next(reader)  # Skip header again
                    self.current_data = list(reader)
            
            self.current_data_index = 0
            self.current_file_index += 1
            
            self.get_logger().info(f'Loaded {len(self.current_data)} entries. Total entries skipped: {self.total_entries_skipped}')
        else:
            self.get_logger().info('All files processed. Stopping.')
            self.timer.cancel()

    def publish_data(self):
        if self.current_data is None or self.current_data_index >= len(self.current_data):
            self.load_next_file()
            if self.current_data is None:
                return

        data = self.current_data[self.current_data_index]
        
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'laser_frame'
        
        if self.file_format == 'npy':
            msg.angle_min = float(data[1])
            msg.angle_max = float(data[2])
            msg.angle_increment = float(data[3])
            msg.time_increment = float(data[4])
            msg.scan_time = float(data[5])
            msg.range_min = float(data[6])
            msg.range_max = float(data[7])
            msg.ranges = [float(x) for x in data[8]]
            msg.intensities = [float(x) for x in data[9]]
        elif self.file_format == 'csv':
            msg.angle_min = float(data[1])
            msg.angle_max = float(data[2])
            msg.angle_increment = float(data[3])
            msg.time_increment = float(data[4])
            msg.scan_time = float(data[5])
            msg.range_min = float(data[6])
            msg.range_max = float(data[7])
            msg.ranges = [float(x) for x in eval(data[8])]
            msg.intensities = [float(x) for x in eval(data[9])]

        self.publisher.publish(msg)
        self.current_data_index += 1

def main(args=None):
    parser = argparse.ArgumentParser(description='LiDAR Data Publisher')
    parser.add_argument('--data_dir', type=str, required=True,
                        help='Directory containing the logged data files')
    parser.add_argument('--format', type=str, choices=['csv', 'npy'], default='npy',
                        help='File format of the logged data (csv or npy)')
    parser.add_argument('--rate', type=float, default=10.0,
                        help='Publishing rate in Hz')
    parser.add_argument('--skip', type=int, default=0,
                        help='Number of entries to skip at the start')

    args, ros_args = parser.parse_known_args(args)
    
    rclpy.init(args=ros_args)
    publisher = LidarDataPublisher(args.data_dir, args.format, args.rate, args.skip)

    try:
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

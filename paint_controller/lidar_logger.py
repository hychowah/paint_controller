import numpy as np
import csv
import time
import os
from datetime import datetime
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import gzip
import shutil
import argparse

class LidarDataLogger(Node):
    def __init__(self, base_path='~/log/lidar', flush_interval=10, max_file_size=100*1024*1024, compress_interval=3600, file_format='npy'):
        super().__init__('lidar_data_logger')
        self.base_path = os.path.expanduser(base_path)
        self.flush_interval = flush_interval
        self.max_file_size = max_file_size
        self.compress_interval = compress_interval
        self.file_format = file_format
        self.last_flush = time.time()
        self.last_compress = time.time()
        self.filename = None
        self.current_date = None
        self.data_buffer = []
        self.setup_file()

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.log_scan,
            10)

    def setup_file(self):
        if self.filename:
            self.save_and_close_file()

        current_date = datetime.now().strftime('%Y-%m-%d')
        if current_date != self.current_date:
            self.current_date = current_date
            os.makedirs(os.path.join(self.base_path, self.current_date), exist_ok=True)

        current_time = datetime.now().strftime('%H-%M-%S')
        self.filename = os.path.join(self.base_path, self.current_date, f"{current_time}.{self.file_format}")
        self.data_buffer = []

        if self.file_format == 'npy':
            np.save(self.filename, np.array([]))
        elif self.file_format == 'csv':
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'angle_min', 'angle_max', 'angle_increment', 'time_increment', 
                                 'scan_time', 'range_min', 'range_max', 'ranges', 'intensities'])

    def log_scan(self, scan_msg):
        timestamp = self.get_clock().now().to_msg().sec
        data = [timestamp, scan_msg.angle_min, scan_msg.angle_max, scan_msg.angle_increment,
                scan_msg.time_increment, scan_msg.scan_time, scan_msg.range_min, scan_msg.range_max,
                list(scan_msg.ranges), list(scan_msg.intensities)]
        
        self.data_buffer.append(data)

        current_time = time.time()
        if current_time - self.last_flush > self.flush_interval:
            self.flush_data()
            self.last_flush = current_time

        if os.path.exists(self.filename) and os.path.getsize(self.filename) > self.max_file_size:
            self.setup_file()

        # if current_time - self.last_compress > self.compress_interval:
        #     self.compress_old_files()
        #     self.last_compress = current_time

    def flush_data(self):
        if self.data_buffer:
            if self.file_format == 'npy':
                data_array = np.array(self.data_buffer, dtype=object)
                if os.path.exists(self.filename):
                    try:
                        existing_data = np.load(self.filename, allow_pickle=True)
                        data_array = np.vstack((existing_data, data_array))
                    except Exception as e:
                        self.get_logger().warn(f"Error loading existing file: {e}. Creating new file.")
                np.save(self.filename, data_array)
            elif self.file_format == 'csv':
                with open(self.filename, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(self.data_buffer)
            self.data_buffer = []

    def save_and_close_file(self):
        self.flush_data()

    def compress_old_files(self):
        for root, _, files in os.walk(self.base_path):
            for file in files:
                if file.endswith(self.file_format) and not file.endswith('.gz'):
                    file_path = os.path.join(root, file)
                    if time.time() - os.path.getmtime(file_path) > self.compress_interval:
                        with open(file_path, 'rb') as f_in:
                            with gzip.open(file_path + '.gz', 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        os.remove(file_path)
                        self.get_logger().info(f'Compressed {file_path}')

    def close(self):
        self.save_and_close_file()
        self.get_logger().info('Data logger closed.')

def main(args=None):
    parser = argparse.ArgumentParser(description='LiDAR Data Logger')
    parser.add_argument('--format', type=str, choices=['csv', 'npy'], default='npy',
                        help='File format for data storage (csv or npy)')
    parser.add_argument('--base_path', type=str, default='~/log/lidar',
                        help='Base path for storing log files')
    parser.add_argument('--flush_interval', type=int, default=10,
                        help='Interval in seconds for flushing data to disk')
    parser.add_argument('--max_file_size', type=int, default=100*1024*1024,
                        help='Maximum file size in bytes before creating a new file')
    parser.add_argument('--compress_interval', type=int, default=300,
                        help='Interval in seconds for compressing old files')

    args, ros_args = parser.parse_known_args(args)
    
    rclpy.init(args=ros_args)
    logger = LidarDataLogger(
        base_path=args.base_path,
        flush_interval=args.flush_interval,
        max_file_size=args.max_file_size,
        compress_interval=args.compress_interval,
        file_format=args.format
    )

    try:
        rclpy.spin(logger)
    except KeyboardInterrupt:
        pass
    finally:
        logger.close()
        logger.destroy_node()
        rclpy.shutdown()
        print("LiDAR data logger has been shut down.")

if __name__ == '__main__':
    main()
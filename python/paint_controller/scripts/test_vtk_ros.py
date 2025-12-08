#!/usr/bin/env python3
"""
Test VTK with real ROS PointCloud2 data from /unilidar/cloud
This helps debug VTK visualization issues
"""

import sys
import os
import numpy as np
import struct
import signal

# Force Qt to use X11 backend for VTK compatibility (Wayland issues)
if 'QT_QPA_PLATFORM' not in os.environ:
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    print("Note: Setting QT_QPA_PLATFORM=xcb for VTK compatibility")
    print("")

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal
from paint_controller.widgets.vtk_pointcloud import VTKPointCloudWidget


class PointCloudSubscriber(Node, QObject):
    """ROS node that subscribes to point cloud and emits Qt signal"""
    points_received = Signal(np.ndarray)
    
    def __init__(self):
        Node.__init__(self, 'vtk_test_subscriber')
        QObject.__init__(self)
        
        self.subscription = self.create_subscription(
            PointCloud2,
            '/unilidar/cloud',
            self.pointcloud_callback,
            10
        )
        
        print("✓ Subscribed to /unilidar/cloud")
        self.message_count = 0
        
    def pointcloud_callback(self, msg):
        """Parse PointCloud2 and emit as numpy array"""
        self.message_count += 1
        
        # Find x, y, z field offsets
        x_offset = y_offset = z_offset = None
        for field in msg.fields:
            if field.name == 'x':
                x_offset = field.offset
            elif field.name == 'y':
                y_offset = field.offset
            elif field.name == 'z':
                z_offset = field.offset
        
        if x_offset is None or y_offset is None or z_offset is None:
            print("Warning: Could not find x, y, z fields")
            return
        
        # Parse points
        point_step = msg.point_step
        num_points = msg.width * msg.height
        
        # Downsample for testing
        downsample = max(1, num_points // 50000)
        
        points_list = []
        for i in range(0, num_points, downsample):
            offset = i * point_step
            
            x = struct.unpack_from('f', msg.data, offset + x_offset)[0]
            y = struct.unpack_from('f', msg.data, offset + y_offset)[0]
            z = struct.unpack_from('f', msg.data, offset + z_offset)[0]
            
            # Filter out invalid points
            if not (np.isnan(x) or np.isnan(y) or np.isnan(z) or 
                   abs(x) > 100 or abs(y) > 100 or abs(z) > 100):
                points_list.append([-y, z, -x])
        
        if points_list:
            points_array = np.array(points_list, dtype=np.float32)
            print(f"Message #{self.message_count}: Parsed {len(points_array)} points")
            print(f"  X range: [{points_array[:, 0].min():.2f}, {points_array[:, 0].max():.2f}]")
            print(f"  Y range: [{points_array[:, 1].min():.2f}, {points_array[:, 1].max():.2f}]")
            print(f"  Z range: [{points_array[:, 2].min():.2f}, {points_array[:, 2].max():.2f}]")
            self.points_received.emit(points_array)
        else:
            print(f"Message #{self.message_count}: No valid points")


def main():
    print("=" * 60)
    print("VTK Test with Real ROS PointCloud2 Data")
    print("=" * 60)
    print("")
    
    # Initialize ROS
    rclpy.init()
    
    # Create Qt application
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    print("✓ Qt Application created")
    
    # Create VTK widget
    widget = VTKPointCloudWidget()
    widget.setWindowTitle("VTK Test - Real LiDAR Data from /unilidar/cloud")
    widget.resize(1200, 800)
    
    print("✓ VTK widget created")
    
    # Create ROS subscriber
    subscriber = PointCloudSubscriber()

    # --- Shutdown Handling ---
    shutdown_requested = False
    def shutdown_app(*args):
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        print("\nShutting down...")
        ros_timer.stop()
        if rclpy.ok():
            subscriber.destroy_node()
            rclpy.shutdown()
        print("✓ Cleanup complete. Forcing exit.")
        sys.exit(0) # Force exit

    # Connect signals for shutdown and data
    subscriber.points_received.connect(widget.update_point_cloud)
    widget.closed.connect(shutdown_app)
    print("✓ Signals connected")
    
    # Allow Ctrl+C to gracefully exit
    signal.signal(signal.SIGINT, shutdown_app)
    
    # We need a timer to process signals for Ctrl+C to work
    signal_timer = QTimer()
    signal_timer.start(100)
    signal_timer.timeout.connect(lambda: None)
    
    # Show widget
    widget.show()
    print("✓ Widget shown")
    print("")
    print("=" * 60)
    print("Waiting for point cloud data from /unilidar/cloud...")
    print("Make sure the LiDAR is publishing!")
    print("Press Ctrl+C or close the window to exit")
    print("=" * 60)
    print("")
    
    # Create timer to spin ROS
    ros_timer = QTimer()
    ros_timer.timeout.connect(lambda: rclpy.spin_once(subscriber, timeout_sec=0.01))
    ros_timer.start(10)  # Spin every 10ms
    
    # Run Qt event loop
    exit_code = app.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

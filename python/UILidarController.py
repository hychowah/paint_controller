#!/usr/bin/env python3

import time
import struct
from sensor_msgs.msg import PointCloud2
from PySide6.QtCore import QObject, Signal, Property, Slot


class LidarController(QObject):
    # Define Qt signals
    pointcloud_updated = Signal(dict)
    points_ready = Signal(list)  # Signal to send parsed 3D points to QML
    
    def __init__(self, robot_controller):
        super().__init__()
        self._robot_controller = robot_controller  # Store reference to the robot controller
        
        # Simple tracking variables
        self._message_count = 0
        self._point_count = 0
        self._frame_id = ""
        self._points_3d = []  # Store parsed 3D points
        
        # Configure subscribers
        self._setup_subscribers()
        
    def _setup_subscribers(self):
        """Set up ROS subscribers for LiDAR data"""
        self._pointcloud_sub = self._robot_controller.create_subscription(
            PointCloud2,
            '/unilidar/cloud',
            self._pointcloud_callback,
            10
        )
        print('LidarController: Subscribed to /unilidar/cloud')
    
    def _parse_pointcloud2(self, msg: PointCloud2):
        """Parse PointCloud2 message and extract XYZ points"""
        points = []
        
        # PointCloud2 structure: width * height points
        # Each point has fields defined in msg.fields (typically x, y, z, intensity, etc.)
        
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
            print("Warning: Could not find x, y, z fields in PointCloud2")
            return points
        
        # Parse binary data
        point_step = msg.point_step
        num_points = msg.width * msg.height
        
        # Downsample for performance - take every Nth point
        downsample = max(1, num_points // 5000)  # Max 5000 points for rendering
        
        for i in range(0, num_points, downsample):
            offset = i * point_step
            
            # Extract x, y, z as floats (assuming float32)
            x = struct.unpack_from('f', msg.data, offset + x_offset)[0]
            y = struct.unpack_from('f', msg.data, offset + y_offset)[0]
            z = struct.unpack_from('f', msg.data, offset + z_offset)[0]
            
            # Filter out invalid points (NaN, Inf)
            if not (abs(x) > 100 or abs(y) > 100 or abs(z) > 100):
                points.append({'x': float(x), 'y': float(y), 'z': float(z)})
        
        return points
    
    def _pointcloud_callback(self, msg: PointCloud2):
        """Process incoming PointCloud2 messages from ROS"""
        self._message_count += 1
        self._point_count = msg.width * msg.height
        self._frame_id = msg.header.frame_id
        
        print(f"LiDAR message #{self._message_count}: {self._point_count} points, frame_id={self._frame_id}")
        
        # Parse 3D points
        self._points_3d = self._parse_pointcloud2(msg)
        print(f"Parsed {len(self._points_3d)} points for visualization")
        
        # Emit signal with basic data
        data = {
            'point_count': self._point_count,
            'frame_id': self._frame_id,
            'message_count': self._message_count,
            'parsed_points': len(self._points_3d)
        }
        self.pointcloud_updated.emit(data)
        
        # Emit parsed points for 3D rendering
        self.points_ready.emit(self._points_3d)
    
    # Qt Properties for QML access
    @Property(int, notify=pointcloud_updated)
    def point_count(self):
        return self._point_count
    
    @Property(int, notify=pointcloud_updated)
    def messages_received(self):
        return self._message_count
    
    @Property(str, notify=pointcloud_updated)
    def frame_id(self):
        return self._frame_id
    
    @Slot(result=list)
    def get_points(self):
        """Get current 3D points for QML"""
        return self._points_3d
    
    def cleanup(self):
        """Cleanup controller resources"""
        print(f'Cleaning up LidarController... (received {self._message_count} messages)')


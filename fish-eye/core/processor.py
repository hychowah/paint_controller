"""
Fisheye image unwrapping processor with support for circular fisheye lenses.
Pre-computes remap tables for fast processing.
"""
import cv2
import numpy as np
from utils.config import (get_camera_matrix, get_distortion_coeffs,
                         DEFAULT_OUTPUT_WIDTH, DEFAULT_OUTPUT_HEIGHT)
import time


class FisheyeProcessor:
    """Process fisheye images with perspective correction and unwrapping."""
    
    def __init__(self, input_width, input_height):
        self.input_width = input_width
        self.input_height = input_height
        
        # Remap tables (pre-computed for speed)
        self.map_x = None
        self.map_y = None
        
        # Current parameters
        self.params = {
            'focal_length': 450.0,
            'center_x': input_width // 2,
            'center_y': input_height // 2,
            'radius': 500,
            'k1': -0.35,
            'k2': 0.15,
            'k3': 0.0,
            'k4': 0.0,
            'fov_h': 180.0,
            'fov_v': 140.0,
            'zoom': 1.0,
            'rotation': 0.0
        }
        
        # Output dimensions
        self.output_width = DEFAULT_OUTPUT_WIDTH
        self.output_height = DEFAULT_OUTPUT_HEIGHT
        
        # Performance tracking
        self.last_remap_time = 0
        
    def update_parameters(self, **kwargs):
        """Update processing parameters and recompute remap tables."""
        params_changed = False
        
        for key, value in kwargs.items():
            if key in self.params and self.params[key] != value:
                self.params[key] = value
                params_changed = True
                
        if params_changed:
            self.compute_remap_tables()
            
    def set_output_size(self, width, height):
        """Set output image dimensions."""
        if width != self.output_width or height != self.output_height:
            self.output_width = width
            self.output_height = height
            self.compute_remap_tables()
            
    def compute_remap_tables(self):
        """Compute remap lookup tables for fast image transformation."""
        start_time = time.time()
        
        # For circular fisheye, the focal length is related to the radius
        # f = radius / (2 * sin(fov/4)) for equidistant projection
        # For 180° FOV, this approximates to radius
        focal_for_fisheye = self.params['radius']
        
        # Camera matrix (intrinsics) for fisheye input
        camera_matrix = np.array([
            [focal_for_fisheye, 0, self.params['center_x']],
            [0, focal_for_fisheye, self.params['center_y']],
            [0, 0, 1]
        ], dtype=np.float32)
        
        # Distortion coefficients (OpenCV fisheye model)
        dist_coeffs = np.array([
            self.params['k1'],
            self.params['k2'],
            self.params['k3'],
            self.params['k4']
        ], dtype=np.float32)
        
        # New camera matrix for output (perspective projection)
        # Clamp FOV to avoid tan(90°) = infinity
        fov_h_rad = np.deg2rad(min(self.params['fov_h'], 179.9))
        fov_v_rad = np.deg2rad(min(self.params['fov_v'], 179.9))
        
        # Calculate focal length for perspective output
        # For smaller FOV values, use standard projection
        if self.params['fov_h'] < 120:
            new_fx = (self.output_width / 2.0) / np.tan(fov_h_rad / 2.0) * self.params['zoom']
        else:
            # For wider FOV, use a scaled version based on the fisheye radius
            new_fx = focal_for_fisheye * self.params['zoom'] * (120.0 / self.params['fov_h'])
            
        if self.params['fov_v'] < 120:
            new_fy = (self.output_height / 2.0) / np.tan(fov_v_rad / 2.0) * self.params['zoom']
        else:
            # For wider FOV, use a scaled version based on the fisheye radius
            new_fy = focal_for_fisheye * self.params['zoom'] * (120.0 / self.params['fov_v'])
        
        new_camera_matrix = np.array([
            [new_fx, 0, self.output_width / 2.0],
            [0, new_fy, self.output_height / 2.0],
            [0, 0, 1]
        ], dtype=np.float32)
        
        # Rotation matrix (for rotation parameter)
        rotation_rad = np.deg2rad(self.params['rotation'])
        R = cv2.Rodrigues(np.array([0, 0, rotation_rad], dtype=np.float32))[0]
        
        # Compute remap tables using OpenCV fisheye model
        try:
            self.map_x, self.map_y = cv2.fisheye.initUndistortRectifyMap(
                camera_matrix,
                dist_coeffs,
                R,
                new_camera_matrix,
                (self.output_width, self.output_height),
                cv2.CV_32FC1
            )
        except Exception as e:
            print(f"Error computing remap tables: {e}")
            # Fallback to identity mapping
            self.map_x, self.map_y = np.meshgrid(
                np.arange(self.output_width, dtype=np.float32),
                np.arange(self.output_height, dtype=np.float32)
            )
            
        self.last_remap_time = time.time() - start_time
        print(f"Remap tables computed in {self.last_remap_time*1000:.2f}ms")
        
    def process_frame(self, frame, fast_mode=False):
        """
        Apply fisheye correction to frame.
        
        Args:
            frame: Input frame (numpy array)
            fast_mode: If True, use faster interpolation (for preview)
            
        Returns:
            Corrected frame (numpy array)
        """
        if self.map_x is None or self.map_y is None:
            # First time - compute tables
            self.compute_remap_tables()
            
        # Apply remap transformation
        interpolation = cv2.INTER_LINEAR if fast_mode else cv2.INTER_CUBIC
        
        try:
            unwrapped = cv2.remap(frame, self.map_x, self.map_y, 
                                 interpolation, borderMode=cv2.BORDER_CONSTANT)
            return unwrapped
        except Exception as e:
            print(f"Error in remap: {e}")
            # Return original frame on error
            return cv2.resize(frame, (self.output_width, self.output_height))
            
    def detect_circle(self, frame):
        """
        Detect the fisheye circle in the frame.
        Returns (center_x, center_y, radius) or None if not found.
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Detect circles using Hough transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=frame.shape[0] // 2,
            param1=50,
            param2=30,
            minRadius=200,
            maxRadius=min(frame.shape[0], frame.shape[1]) // 2
        )
        
        if circles is not None and len(circles) > 0:
            # Take the first detected circle
            circle = circles[0][0]
            center_x, center_y, radius = int(circle[0]), int(circle[1]), int(circle[2])
            return center_x, center_y, radius
            
        return None
        
    def auto_detect_parameters(self, frame):
        """
        Automatically detect fisheye circle parameters from a frame.
        Updates center_x, center_y, and radius.
        """
        result = self.detect_circle(frame)
        
        if result:
            center_x, center_y, radius = result
            print(f"Auto-detected circle: center=({center_x}, {center_y}), radius={radius}")
            
            self.update_parameters(
                center_x=center_x,
                center_y=center_y,
                radius=radius
            )
            return True
        else:
            print("Failed to auto-detect fisheye circle")
            return False
            
    def get_parameters(self):
        """Get current processing parameters."""
        return self.params.copy()
        
    def draw_circle_overlay(self, frame):
        """
        Draw the fisheye circle and center point on the frame.
        Useful for visualizing parameters.
        """
        overlay = frame.copy()
        
        # Draw circle
        cv2.circle(overlay, 
                  (int(self.params['center_x']), int(self.params['center_y'])),
                  int(self.params['radius']),
                  (0, 255, 0), 2)
        
        # Draw center crosshair
        center_x = int(self.params['center_x'])
        center_y = int(self.params['center_y'])
        cv2.line(overlay, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
        cv2.line(overlay, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)
        
        return overlay

"""
Main application window with dual video display and controls.
"""
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QLabel, QScrollArea, QStatusBar, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
import numpy as np
import time

from core.processor import FisheyeProcessor
from core.video_recorder import VideoRecorder
from gui.controls_panel import ControlsPanel


class VideoLabel(QLabel):
    """Custom QLabel for displaying video frames."""
    
    def __init__(self, title="Video", parent=None):
        super().__init__(parent)
        self.title = title
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background-color: black; border: 2px solid gray;")
        self.setText(f"{title}\n(No video)")
        self.setScaledContents(True)  # Let Qt scale - GPU accelerated
        
        # Performance attributes
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        # Keep frame data alive to avoid QImage.copy()
        self.frame_data = None
        
    def set_frame(self, frame):
        """Display a frame (numpy array)."""
        if frame is None or frame.size == 0:
            return
            
        # Convert BGR to RGB
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        else:
            frame_rgb = frame
        
        # Keep frame data alive (prevents QImage dangling pointer)
        self.frame_data = frame_rgb
            
        # Get frame dimensions
        h, w = self.frame_data.shape[:2]
                
        # Convert to QImage (no copy - setScaledContents handles scaling)
        if len(self.frame_data.shape) == 3:
            bytes_per_line = 3 * w
            q_image = QImage(self.frame_data.data, w, h, bytes_per_line, QImage.Format_RGB888)
        else:
            bytes_per_line = w
            q_image = QImage(self.frame_data.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
            
        # Display - Qt scales automatically with setScaledContents(True)
        self.setPixmap(QPixmap.fromImage(q_image))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, camera_index, resolution):
        super().__init__()
        
        self.camera_index = camera_index
        self.resolution = resolution
        self.width, self.height = resolution
        
        # Core components - NO MORE QTHREADS!
        self.camera = None
        self.processor = None
        self.video_recorder = VideoRecorder()
        
        # Current frames
        self.current_original_frame = None
        self.current_unwrapped_frame = None
        
        # UI state
        self.show_circle_overlay = True
        self.is_recording = False
        
        # FPS tracking
        self.frame_count = 0
        self.fps_start_time = None
        self.display_fps = 0.0
        
        self.init_ui()
        self.start_camera()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Fisheye Unwrapper - Real-Time")
        self.resize(1600, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left side: Video displays
        video_layout = QVBoxLayout()
        
        # Original video
        self.original_label = VideoLabel("Original Fisheye")
        video_layout.addWidget(self.original_label)
        
        # Unwrapped video
        self.unwrapped_label = VideoLabel("Unwrapped / Corrected")
        video_layout.addWidget(self.unwrapped_label)
        
        main_layout.addLayout(video_layout, stretch=3)
        
        # Right side: Controls panel in scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumWidth(350)
        scroll_area.setMaximumWidth(400)
        
        self.controls_panel = ControlsPanel()
        self.controls_panel.parameters_changed.connect(self.on_parameters_changed)
        self.controls_panel.auto_detect_requested.connect(self.on_auto_detect)
        self.controls_panel.snapshot_requested.connect(self.on_snapshot)
        self.controls_panel.recording_toggled.connect(self.on_recording_toggled)
        self.controls_panel.show_circle_toggled.connect(self.on_show_circle_toggled)
        
        scroll_area.setWidget(self.controls_panel)
        main_layout.addWidget(scroll_area, stretch=1)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Initializing...")
        
        # Single timer for everything - direct approach like test_simple_qt.py
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.update_frame)
        self.main_timer.start(0)  # As fast as possible
        
        # FPS update timer
        self.fps_timer = QTimer()
        self.fps_timer.timeout.connect(self.update_status)
        self.fps_timer.start(1000)
        
    def start_camera(self):
        """Start camera capture and processing - DIRECT, NO THREADS!"""
        # Open camera directly
        self.camera = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        
        if not self.camera.isOpened():
            QMessageBox.critical(self, "Error", f"Failed to open camera {self.camera_index}")
            return
        
        # Set resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        # Verify resolution
        actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"Camera resolution: {actual_width}x{actual_height}")
        
        # Initialize processor
        self.processor = FisheyeProcessor(self.width, self.height)
        
        # Set initial parameters from controls
        initial_params = self.controls_panel.get_parameters()
        self.processor.update_parameters(
            focal_length=initial_params['focal_length'],
            center_x=initial_params['center_x'],
            center_y=initial_params['center_y'],
            radius=initial_params['radius'],
            k1=initial_params['k1'],
            k2=initial_params['k2'],
            fov_h=initial_params['fov_h'],
            fov_v=initial_params['fov_v'],
            zoom=initial_params['zoom'],
            rotation=initial_params['rotation']
        )
        
        self.fps_start_time = time.time()
        self.status_bar.showMessage("Camera started")
    
    def update_frame(self):
        """Main update loop - direct processing, no threads!"""
        if self.camera is None or not self.camera.isOpened():
            return
        
        # Read frame directly
        ret, frame = self.camera.read()
        if not ret:
            return
        
        # Store original
        self.current_original_frame = frame.copy()
        
        # Process frame directly
        unwrapped = self.processor.process_frame(frame, fast_mode=False)
        self.current_unwrapped_frame = unwrapped
        
        # Prepare display frames
        if self.show_circle_overlay:
            display_original = self.processor.draw_circle_overlay(frame)
        else:
            display_original = frame
        
        # Display both frames
        self.original_label.set_frame(display_original)
        if unwrapped is not None:
            self.unwrapped_label.set_frame(unwrapped)
        
        # Record if active
        if self.is_recording:
            self.video_recorder.write_frame(
                original_frame=self.current_original_frame,
                unwrapped_frame=self.current_unwrapped_frame
            )
        
        # Update FPS counter
        self.frame_count += 1
        
    def on_parameters_changed(self, params):
        """Handle parameter changes from controls panel."""
        if self.processor:
            self.processor.update_parameters(
                focal_length=params['focal_length'],
                center_x=params['center_x'],
                center_y=params['center_y'],
                radius=params['radius'],
                k1=params['k1'],
                k2=params['k2'],
                fov_h=params['fov_h'],
                fov_v=params['fov_v'],
                zoom=params['zoom'],
                rotation=params['rotation']
            )
            
    def on_auto_detect(self):
        """Handle auto-detect circle request."""
        if self.current_original_frame is None:
            QMessageBox.warning(self, "No Frame", 
                              "No frame available for detection. Please wait for camera.")
            return
            
        # Detect circle
        success = self.processor.auto_detect_parameters(self.current_original_frame)
        
        if success:
            # Update controls with detected parameters
            detected_params = self.processor.get_parameters()
            self.controls_panel.set_parameters(detected_params)
            QMessageBox.information(self, "Auto Detect", 
                                  "Circle detected successfully!")
        else:
            QMessageBox.warning(self, "Auto Detect", 
                              "Could not detect fisheye circle. Please adjust manually.")
                              
    def on_snapshot(self):
        """Handle snapshot request."""
        if self.current_unwrapped_frame is None:
            QMessageBox.warning(self, "No Frame", "No frame available to save.")
            return
            
        # Save both original and unwrapped
        path_original = self.video_recorder.save_snapshot(self.current_original_frame, "original")
        path_unwrapped = self.video_recorder.save_snapshot(self.current_unwrapped_frame, "unwrapped")
        
        if path_original and path_unwrapped:
            QMessageBox.information(self, "Snapshot Saved", 
                                  f"Saved:\n{path_original}\n{path_unwrapped}")
                                  
    def on_recording_toggled(self, start_recording):
        """Handle recording toggle."""
        if start_recording:
            # Start recording
            self.is_recording = True
            paths = self.video_recorder.start_recording(
                self.width, self.height, record_both=True
            )
            if paths[0] is None and paths[1] is None:
                QMessageBox.critical(self, "Recording Error", 
                                   "Failed to start recording.")
                self.controls_panel.record_btn.setChecked(False)
                self.is_recording = False
        else:
            # Stop recording
            self.is_recording = False
            paths = self.video_recorder.stop_recording()
            if paths:
                QMessageBox.information(self, "Recording Saved", 
                                      f"Saved:\n{paths[0]}\n{paths[1]}")
                                      
    def on_show_circle_toggled(self, show):
        """Handle show circle overlay toggle."""
        self.show_circle_overlay = show
        
    def update_status(self):
        """Update status bar with current information."""
        # Calculate FPS
        if self.fps_start_time is not None:
            elapsed = time.time() - self.fps_start_time
            if elapsed > 0:
                self.display_fps = self.frame_count / elapsed
        
        self.frame_count = 0
        self.fps_start_time = time.time()
        
        status_parts = [
            f"FPS: {self.display_fps:.1f}",
            f"Resolution: {self.width}x{self.height}"
        ]
        
        if self.is_recording:
            frame_count = self.video_recorder.get_frame_count()
            duration = self.video_recorder.get_duration()
            status_parts.append(f"Recording: {frame_count} frames ({duration:.1f}s)")
            self.controls_panel.update_recording_info(frame_count, duration)
            
        self.status_bar.showMessage(" | ".join(status_parts))
        
    def closeEvent(self, event):
        """Handle window close."""
        # Stop recording if active
        if self.is_recording:
            self.video_recorder.stop_recording()
        
        # Release camera
        if self.camera is not None:
            self.camera.release()
            
        event.accept()

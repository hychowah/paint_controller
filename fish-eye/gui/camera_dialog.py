"""
Camera selection dialog for choosing USB camera and resolution.
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QListWidget, QListWidgetItem,
                             QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
from utils.config import AVAILABLE_RESOLUTIONS


class CameraDialog(QDialog):
    """Dialog for selecting camera device and resolution."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Camera")
        self.setModal(True)
        self.resize(600, 500)
        
        self.selected_camera_index = None
        self.selected_resolution = (1920, 1080)
        self.preview_capture = None
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        
        self.init_ui()
        self.enumerate_cameras()
        
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Camera selection group
        camera_group = QGroupBox("Available Cameras")
        camera_layout = QVBoxLayout()
        
        self.camera_list = QListWidget()
        self.camera_list.itemClicked.connect(self.on_camera_selected)
        camera_layout.addWidget(self.camera_list)
        
        camera_group.setLayout(camera_layout)
        layout.addWidget(camera_group)
        
        # Resolution selection
        resolution_group = QGroupBox("Resolution")
        resolution_layout = QHBoxLayout()
        
        resolution_layout.addWidget(QLabel("Select Resolution:"))
        self.resolution_combo = QComboBox()
        for width, height in AVAILABLE_RESOLUTIONS:
            self.resolution_combo.addItem(f"{width}x{height}", (width, height))
        # Set default to 1920x1080
        index = self.resolution_combo.findData((1920, 1080))
        if index >= 0:
            self.resolution_combo.setCurrentIndex(index)
        self.resolution_combo.currentIndexChanged.connect(self.on_resolution_changed)
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch()
        
        resolution_group.setLayout(resolution_layout)
        layout.addWidget(resolution_group)
        
        # Preview group
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_label = QLabel("Select a camera to preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)
        self.preview_label.setStyleSheet("background-color: black; color: white;")
        preview_layout.addWidget(self.preview_label)
        
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh Cameras")
        self.refresh_btn.clicked.connect(self.enumerate_cameras)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
        
    def enumerate_cameras(self):
        """Find all available camera devices."""
        self.camera_list.clear()
        self.stop_preview()
        
        # Check up to 10 camera indices
        available_cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)  # Use DirectShow on Windows
            if cap.isOpened():
                # Try to read a frame to confirm camera works
                ret, frame = cap.read()
                if ret:
                    # Get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    available_cameras.append((i, width, height))
                cap.release()
        
        if not available_cameras:
            item = QListWidgetItem("No cameras found")
            item.setFlags(Qt.NoItemFlags)
            self.camera_list.addItem(item)
            QMessageBox.warning(self, "No Cameras", 
                              "No cameras were detected. Please connect a camera and try again.")
        else:
            for cam_id, width, height in available_cameras:
                item = QListWidgetItem(f"Camera {cam_id} ({width}x{height})")
                item.setData(Qt.UserRole, cam_id)
                self.camera_list.addItem(item)
                
    def on_camera_selected(self, item):
        """Handle camera selection."""
        cam_id = item.data(Qt.UserRole)
        if cam_id is not None:
            self.selected_camera_index = cam_id
            self.ok_btn.setEnabled(True)
            self.start_preview()
            
    def on_resolution_changed(self, index):
        """Handle resolution change."""
        self.selected_resolution = self.resolution_combo.currentData()
        if self.preview_capture is not None:
            # Restart preview with new resolution
            self.start_preview()
            
    def start_preview(self):
        """Start camera preview."""
        self.stop_preview()
        
        if self.selected_camera_index is None:
            return
            
        self.preview_capture = cv2.VideoCapture(self.selected_camera_index, cv2.CAP_DSHOW)
        
        if self.preview_capture.isOpened():
            # Use LOW resolution for preview to reduce lag (640x480)
            self.preview_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.preview_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Set lower FPS for preview to reduce CPU usage
            self.preview_capture.set(cv2.CAP_PROP_FPS, 15)
            
            # Disable buffering to reduce lag
            self.preview_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Start preview timer (15 FPS - slower to reduce load)
            self.preview_timer.start(66)  # ~15 FPS
        else:
            QMessageBox.warning(self, "Camera Error", 
                              f"Could not open camera {self.selected_camera_index}")
            
    def stop_preview(self):
        """Stop camera preview."""
        self.preview_timer.stop()
        
        if self.preview_capture is not None:
            self.preview_capture.release()
            self.preview_capture = None
            
        self.preview_label.clear()
        self.preview_label.setText("Select a camera to preview")
        
    def update_preview(self):
        """Update preview frame."""
        if self.preview_capture is None or not self.preview_capture.isOpened():
            self.stop_preview()
            return
            
        ret, frame = self.preview_capture.read()
        if ret:
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Scale to fit preview label
            label_size = self.preview_label.size()
            h, w = frame_rgb.shape[:2]
            
            # Calculate scaling to fit in label
            scale = min(label_size.width() / w, label_size.height() / h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            
            if new_w > 0 and new_h > 0:
                # Use fastest interpolation for preview
                frame_resized = cv2.resize(frame_rgb, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
                
                # Convert to QImage with copy to avoid memory issues
                h, w, ch = frame_resized.shape
                bytes_per_line = ch * w
                q_image = QImage(frame_resized.data, w, h, bytes_per_line, QImage.Format_RGB888).copy()
                
                # Display
                self.preview_label.setPixmap(QPixmap.fromImage(q_image))
                
    def get_selection(self):
        """Return selected camera index and resolution."""
        return self.selected_camera_index, self.selected_resolution
        
    def closeEvent(self, event):
        """Handle dialog close."""
        self.stop_preview()
        event.accept()
        
    def reject(self):
        """Handle cancel button."""
        self.stop_preview()
        super().reject()
        
    def accept(self):
        """Handle OK button."""
        self.stop_preview()
        super().accept()

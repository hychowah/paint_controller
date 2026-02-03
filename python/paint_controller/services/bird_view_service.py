"""
Bird's Eye View Service for Paint Controller
Transforms base front camera feed to top-down bird view using QThread worker pattern
"""

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker, QThread, Slot, Property
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider
from typing import Optional, List
import logging

from .video_stream import VideoStreamHandler, CameraType


class BirdViewTransformer:
    """Core bird view transformation logic extracted from bird_view_transform.py"""
    
    def __init__(self):
        # Camera calibration for 150° FOV fisheye
        self.k1: float = 0.32   # Fisheye distortion coefficient 1
        self.k2: float = 0.272  # Fisheye distortion coefficient 2
        self.camera_matrix: Optional[np.ndarray] = None
        self.dist_coeffs: Optional[np.ndarray] = None
        
        # Cached undistortion maps (calculated once for performance)
        self.map1: Optional[np.ndarray] = None
        self.map2: Optional[np.ndarray] = None
        
        # Output dimensions (final bird view size)
        self.output_width: int = 300
        self.output_height: int = 400
        
        # Transformation parameters (from bird_view_transform.py defaults)
        self.zoom: float = 0.606  # Bird's eye view zoom factor
        self.offset_x: float = 0.026  # Horizontal pan (-1.0 to 1.0)
        self.offset_y: float = 0.474  # Vertical pan (-1.0 to 1.0)
        
        # Crop settings for vertical road view
        self.crop_enabled: bool = True
        self.crop_width_ratio: float = 0.9  # Width as ratio (0.0-1.0) - increased from 0.656
        self.crop_center_x: float = 0.5  # Horizontal center (0.0-1.0)
        
        # Source points as normalized coordinates (0.0 to 1.0)
        # These will be scaled to actual resolution in initialize_for_resolution()
        # Based on original trapezoid for 860x550: [[10,550], [850,550], [720,400], [320,400]]
        self.src_points_normalized: List[List[float]] = [
            [0.012, 1.0],      # Bottom-left (10/860, 550/550)
            [0.988, 1.0],      # Bottom-right (850/860, 550/550)
            [0.837, 0.727],    # Top-right (720/860, 400/550)
            [0.372, 0.727]     # Top-left (320/860, 400/550)
        ]
        
        # Actual pixel coordinates (will be calculated from normalized)
        self.src_points: List[List[float]] = []
        
        # Destination points will be calculated based on zoom/pan
        self.dst_points: List[List[float]] = []
        self.perspective_matrix: Optional[np.ndarray] = None
        
    def initialize_for_resolution(self, width: int, height: int):
        """
        Initialize camera calibration and undistortion maps for given resolution
        
        Args:
            width: Input frame width
            height: Input frame height
        """
        # Scale normalized source points to actual resolution
        self.src_points = [
            [pt[0] * width, pt[1] * height]
            for pt in self.src_points_normalized
        ]
        
        # Approximate camera intrinsic parameters for 150° FOV fisheye
        focal_length = width * 0.6  # Empirical value
        
        self.camera_matrix = np.array([
            [focal_length, 0, width / 2.0],
            [0, focal_length, height / 2.0],
            [0, 0, 1]
        ], dtype=np.float64)
        
        # Fisheye distortion coefficients (k1, k2, k3, k4)
        self.dist_coeffs = np.array([self.k1, self.k2, 0, 0], dtype=np.float64)
        
        # Compute and cache undistortion maps (expensive operation, done once)
        balance = 0.5
        new_camera_matrix = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
            self.camera_matrix, self.dist_coeffs, (width, height), np.eye(3),
            balance=balance
        )
        
        self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(
            self.camera_matrix, self.dist_coeffs, np.eye(3),
            new_camera_matrix, (width, height), cv2.CV_16SC2
        )
        
        # Initialize destination points for perspective transform
        self._calculate_destination_points()
    
    def _calculate_destination_points(self):
        """Calculate destination points based on zoom and pan offsets"""
        center_x = self.output_width * 0.5
        center_y = self.output_height * 0.5
        
        # Apply pan offsets
        center_x += self.offset_x * self.output_width * 0.5
        center_y += self.offset_y * self.output_height * 0.5
        
        # Base coordinates relative to center
        base_coords = [
            [-0.3, 0.3],   # Bottom-left
            [0.3, 0.3],    # Bottom-right
            [0.3, -0.3],   # Top-right
            [-0.3, -0.3]   # Top-left
        ]
        
        # Apply zoom and convert to absolute coordinates
        self.dst_points = [
            [
                center_x + (coord[0] * self.output_width * self.zoom),
                center_y + (coord[1] * self.output_height * self.zoom)
            ]
            for coord in base_coords
        ]
    
    def undistort_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply fisheye undistortion using cached maps (fast)
        
        Args:
            frame: Input frame
            
        Returns:
            Undistorted frame
        """
        if self.map1 is None or self.map2 is None:
            return frame
        
        return cv2.remap(frame, self.map1, self.map2, interpolation=cv2.INTER_LINEAR)
    
    def apply_perspective_transform(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply perspective transformation for bird's eye view
        
        Args:
            frame: Undistorted input frame
            
        Returns:
            Transformed bird's eye view frame
        """
        if len(self.src_points) != 4 or len(self.dst_points) != 4:
            return cv2.resize(frame, (self.output_width, self.output_height))
        
        src = np.array(self.src_points, dtype=np.float32)
        dst = np.array(self.dst_points, dtype=np.float32)
        
        self.perspective_matrix = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(
            frame, self.perspective_matrix,
            (self.output_width, self.output_height)
        )
        
        # Apply vertical crop if enabled
        if self.crop_enabled:
            warped = self._crop_to_vertical_road(warped)
        
        return warped
    
    def _crop_to_vertical_road(self, frame: np.ndarray) -> np.ndarray:
        """
        Crop to vertical rectangle mimicking road view
        
        Args:
            frame: Full bird's eye view frame
            
        Returns:
            Cropped frame
        """
        height, width = frame.shape[:2]
        crop_width = int(width * self.crop_width_ratio)
        center_x = int(width * self.crop_center_x)
        
        left = max(0, center_x - crop_width // 2)
        right = min(width, left + crop_width)
        
        if right > width:
            right = width
            left = right - crop_width
        
        return frame[:, left:right]
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Full processing pipeline: undistort + perspective transform + crop
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Processed bird view frame
        """
        undistorted = self.undistort_frame(frame)
        transformed = self.apply_perspective_transform(undistorted)
        return transformed


class BirdViewImageProvider(QQuickImageProvider):
    """Image provider for QML display with thread-safe access"""
    
    def __init__(self, width: int = 300, height: int = 400):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(width, height, QImage.Format_RGB888)
        self.image.fill(0)  # Black background initially
        self._image_lock = QMutex()
    
    def requestImage(self, id, size, requestedSize):
        """Thread-safe image retrieval for QML"""
        locker = QMutexLocker(self._image_lock)
        return self.image.copy()


class BirdViewWorker(QObject):
    """Worker that processes frames in separate thread"""
    
    frameReady = Signal()
    
    def __init__(self, image_provider: BirdViewImageProvider):
        super().__init__()
        self.image_provider = image_provider
        self.transformer = BirdViewTransformer()
        self._processing = False
        self._initialized = False
        self.logger = logging.getLogger(__name__)
    
    @Slot(object, QImage)
    def process_frame(self, camera_type: CameraType, qimage: QImage):
        """
        Process incoming frame from VideoStreamHandler
        
        Args:
            camera_type: Type of camera (should be BASE_FRONT)
            qimage: QImage from camera stream
        """
        # Skip if already processing (stay realtime, drop frames if needed)
        if self._processing:
            return
        
        # Only process BASE_FRONT camera
        if camera_type != CameraType.BASE_FRONT:
            return
        
        self._processing = True
        
        try:
            # Convert QImage to numpy array (BGR for OpenCV)
            width = qimage.width()
            height = qimage.height()
            
            # Ensure RGB888 format
            if qimage.format() != QImage.Format_RGB888:
                qimage = qimage.convertToFormat(QImage.Format_RGB888)
            
            # Get raw bytes and convert to numpy
            ptr = qimage.constBits()
            arr = np.array(ptr).reshape(height, width, 3)  # RGB
            arr_bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            
            # Initialize transformer on first frame
            if not self._initialized:
                self.transformer.initialize_for_resolution(width, height)
                self._initialized = True
            
            # Apply bird view transformation
            transformed = self.transformer.process_frame(arr_bgr)
            
            # Convert back to QImage for Qt display
            arr_rgb = cv2.cvtColor(transformed, cv2.COLOR_BGR2RGB)
            h, w, ch = arr_rgb.shape
            bytes_per_line = 3 * w
            
            result_image = QImage(arr_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            
            # Update image provider (thread-safe)
            locker = QMutexLocker(self.image_provider._image_lock)
            self.image_provider.image = result_image.copy()
            locker.unlock()
            
            # Notify QML to refresh
            self.frameReady.emit()
            
        except Exception as e:
            self.logger.error(f"Error processing bird view frame: {e}")
        
        finally:
            self._processing = False


class BirdViewService(QObject):
    """Main service for bird view integration"""
    
    frameReady = Signal()
    
    # Parameter change signals
    zoomChanged = Signal(float)
    offsetXChanged = Signal(float)
    offsetYChanged = Signal(float)
    cropEnabledChanged = Signal(bool)
    cropWidthRatioChanged = Signal(float)
    cropCenterXChanged = Signal(float)
    k1Changed = Signal(float)
    k2Changed = Signal(float)
    editModeChanged = Signal(bool)
    sourcePointsChanged = Signal()
    
    def __init__(self, video_handler: VideoStreamHandler, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.video_handler = video_handler
        self.image_provider = BirdViewImageProvider()
        self.logger = logging.getLogger(__name__)
        self._edit_mode = False
        
        # Create worker and thread
        self.worker = BirdViewWorker(self.image_provider)
        self.worker_thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)
        
        # Connect signals
        self.worker.frameReady.connect(self.frameReady.emit)
        
        # Connect to BASE_FRONT camera stream
        base_front_stream = video_handler.camera_streams.get(CameraType.BASE_FRONT)
        if base_front_stream:
            base_front_stream.frameReady.connect(self.worker.process_frame)
            self.logger.info("Bird view service connected to BASE_FRONT camera stream")
        else:
            self.logger.warning("BASE_FRONT camera stream not found")
        
        # Start thread
        self.worker_thread.start()
        self.logger.info("Bird view worker thread started")
    
    def cleanup(self):
        """Clean up thread resources"""
        try:
            self.logger.info("Stopping bird view worker thread...")
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.logger.info("Bird view worker thread stopped")
        except Exception as e:
            self.logger.error(f"Error during bird view cleanup: {e}")
    
    # ========== Qt Properties ==========
    
    @Property(float, notify=zoomChanged)
    def zoom(self) -> float:
        return self.worker.transformer.zoom
    
    @zoom.setter
    def zoom(self, value: float):
        if self.worker.transformer.zoom != value:
            self.worker.transformer.zoom = value
            self.worker.transformer._calculate_destination_points()
            self.zoomChanged.emit(value)
    
    @Property(float, notify=offsetXChanged)
    def offsetX(self) -> float:
        return self.worker.transformer.offset_x
    
    @offsetX.setter
    def offsetX(self, value: float):
        if self.worker.transformer.offset_x != value:
            self.worker.transformer.offset_x = value
            self.worker.transformer._calculate_destination_points()
            self.offsetXChanged.emit(value)
    
    @Property(float, notify=offsetYChanged)
    def offsetY(self) -> float:
        return self.worker.transformer.offset_y
    
    @offsetY.setter
    def offsetY(self, value: float):
        if self.worker.transformer.offset_y != value:
            self.worker.transformer.offset_y = value
            self.worker.transformer._calculate_destination_points()
            self.offsetYChanged.emit(value)
    
    @Property(bool, notify=cropEnabledChanged)
    def cropEnabled(self) -> bool:
        return self.worker.transformer.crop_enabled
    
    @cropEnabled.setter
    def cropEnabled(self, value: bool):
        if self.worker.transformer.crop_enabled != value:
            self.worker.transformer.crop_enabled = value
            self.cropEnabledChanged.emit(value)
    
    @Property(float, notify=cropWidthRatioChanged)
    def cropWidthRatio(self) -> float:
        return self.worker.transformer.crop_width_ratio
    
    @cropWidthRatio.setter
    def cropWidthRatio(self, value: float):
        if self.worker.transformer.crop_width_ratio != value:
            self.worker.transformer.crop_width_ratio = value
            self.cropWidthRatioChanged.emit(value)
    
    @Property(float, notify=cropCenterXChanged)
    def cropCenterX(self) -> float:
        return self.worker.transformer.crop_center_x
    
    @cropCenterX.setter
    def cropCenterX(self, value: float):
        if self.worker.transformer.crop_center_x != value:
            self.worker.transformer.crop_center_x = value
            self.cropCenterXChanged.emit(value)
    
    @Property(float, notify=k1Changed)
    def k1(self) -> float:
        return self.worker.transformer.k1
    
    @k1.setter
    def k1(self, value: float):
        if self.worker.transformer.k1 != value:
            self.worker.transformer.k1 = value
            # Reinitialize distortion maps with new k1
            if self.worker._initialized:
                self.worker.transformer.dist_coeffs[0] = value
                self._reinitialize_maps()
            self.k1Changed.emit(value)
    
    @Property(float, notify=k2Changed)
    def k2(self) -> float:
        return self.worker.transformer.k2
    
    @k2.setter
    def k2(self, value: float):
        if self.worker.transformer.k2 != value:
            self.worker.transformer.k2 = value
            # Reinitialize distortion maps with new k2
            if self.worker._initialized:
                self.worker.transformer.dist_coeffs[1] = value
                self._reinitialize_maps()
            self.k2Changed.emit(value)
    
    def _reinitialize_maps(self):
        """Reinitialize undistortion maps when distortion coefficients change"""
        try:
            transformer = self.worker.transformer
            if transformer.camera_matrix is not None:
                width = int(transformer.camera_matrix[0, 2] * 2)
                height = int(transformer.camera_matrix[1, 2] * 2)
                
                balance = 0.5
                new_camera_matrix = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
                    transformer.camera_matrix, transformer.dist_coeffs, (width, height), np.eye(3),
                    balance=balance
                )
                
                transformer.map1, transformer.map2 = cv2.fisheye.initUndistortRectifyMap(
                    transformer.camera_matrix, transformer.dist_coeffs, np.eye(3),
                    new_camera_matrix, (width, height), cv2.CV_16SC2
                )
        except Exception as e:
            self.logger.error(f"Error reinitializing distortion maps: {e}")
    
    @Slot()
    def resetToDefaults(self):
        """Reset all parameters to default values"""
        self.zoom = 0.606
        self.offsetX = 0.026
        self.offsetY = 0.474
        self.cropEnabled = True
        self.cropWidthRatio = 0.9  # Increased from 0.656
        self.cropCenterX = 0.5
        self.k1 = 0.32
        self.k2 = 0.272
    
    # ========== Source Points Properties ==========
    
    @Property('QVariantList', notify=sourcePointsChanged)
    def sourcePoints(self) -> List[List[float]]:
        """Get all four source points as normalized coordinates"""
        return self.worker.transformer.src_points_normalized
    
    @Slot(int, float, float)
    def updateSourcePoint(self, index: int, x: float, y: float):
        """Update a single source point (normalized coordinates 0.0-1.0)"""
        if 0 <= index < 4:
            self.worker.transformer.src_points_normalized[index] = [x, y]
            # Recalculate actual pixel coordinates if already initialized
            if self.worker._initialized and self.worker.transformer.camera_matrix is not None:
                width = int(self.worker.transformer.camera_matrix[0, 2] * 2)
                height = int(self.worker.transformer.camera_matrix[1, 2] * 2)
                self.worker.transformer.src_points = [
                    [pt[0] * width, pt[1] * height]
                    for pt in self.worker.transformer.src_points_normalized
                ]
            self.sourcePointsChanged.emit()
    
    @Property(bool, notify=editModeChanged)
    def editMode(self) -> bool:
        """Whether point editing mode is active"""
        return self._edit_mode
    
    @editMode.setter
    def editMode(self, value: bool):
        if self._edit_mode != value:
            self._edit_mode = value
            self.editModeChanged.emit(value)

"""
Base Top View Service for Paint Controller
Transforms base top camera feed (port 5003) with fish-eye correction using QThread worker pattern
"""

import json
import logging
import os

import cv2
import numpy as np
from PySide6.QtCore import (
    Property,
    QMutex,
    QMutexLocker,
    QObject,
    Qt,
    QThread,
    QTimer,
    Signal,
    Slot,
)
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from paint_controller.core.settings import _SETTINGS_SCHEMA

from .video_stream import CameraType, VideoStreamHandler

# Draft-live service attributes ↔ SettingsManager schema keys.
# Live slider ticks mutate service draft properties only; Save/Reset persist.
_BASE_TOP_SETTING_KEYS: tuple[tuple[str, str], ...] = (
    ("zoom", "base_top_view_zoom"),
    ("offsetX", "base_top_view_offset_x"),
    ("offsetY", "base_top_view_offset_y"),
    ("cropEnabled", "base_top_view_crop_enabled"),
    ("cropWidthRatio", "base_top_view_crop_width_ratio"),
    ("cropCenterX", "base_top_view_crop_center_x"),
    ("k1", "base_top_view_k1"),
    ("k2", "base_top_view_k2"),
    ("k3", "base_top_view_k3"),
    ("k4", "base_top_view_k4"),
)
_BASE_TOP_SRC_POINTS_KEY = "base_top_view_src_points"


def _schema_default(key: str):
    """Return the Settings schema default for a base-top key (single source of truth)."""
    return _SETTINGS_SCHEMA[key]["default"]


class BaseTopViewTransformer:
    """Core fish-eye correction transformation logic for base top camera"""

    def __init__(self, config_path: str | None = None):
        # Load calibration from fish-eye config file
        if config_path is None:
            # Default to base_top_view_camera.json in config folder
            config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
            config_path = os.path.join(config_dir, "base_top_view_camera.json")

        # Default values (will be overridden by config file if available)
        self.k1: float = -0.389  # Fisheye distortion coefficient 1
        self.k2: float = 0.142  # Fisheye distortion coefficient 2
        self.k3: float = 0.0  # Fisheye distortion coefficient 3
        self.k4: float = 0.0  # Fisheye distortion coefficient 4

        # Circle boundary parameters (from fish-eye config, at calibration resolution)
        self.center_x: int = 966
        self.center_y: int = 540
        self.radius: int = 599

        # Calibration resolution (resolution at which center_x/center_y/radius were measured)
        self.calibration_width: int = 1920
        self.calibration_height: int = 1080

        # FOV and zoom parameters
        self.fov_h: float = 93.75
        self.fov_v: float = 67.5
        self.zoom: float = 0.51
        self.rotation: float = 0.0

        # Load from config file if available
        if os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    config = json.load(f)
                self.k1 = config.get("k1", self.k1)
                self.k2 = config.get("k2", self.k2)
                self.k3 = config.get("k3", 0.0)
                self.k4 = config.get("k4", 0.0)
                self.center_x = config.get("center_x", self.center_x)
                self.center_y = config.get("center_y", self.center_y)
                self.radius = config.get("radius", self.radius)
                self.calibration_width = config.get("calibration_width", 1920)
                self.calibration_height = config.get("calibration_height", 1080)
                self.fov_h = config.get("fov_h", self.fov_h)
                self.fov_v = config.get("fov_v", self.fov_v)
                self.zoom = config.get("zoom", self.zoom)
                self.rotation = config.get("rotation", self.rotation)
                logging.info(
                    f"Loaded base top view config: k1={self.k1}, k2={self.k2}, k3={self.k3}, k4={self.k4}, zoom={self.zoom}"
                )
            except Exception as e:
                logging.warning(f"Failed to load base top view config from {config_path}: {e}")

        self.camera_matrix: np.ndarray | None = None
        self.dist_coeffs: np.ndarray | None = None

        # Cached undistortion maps (calculated once for performance)
        self.map1: np.ndarray | None = None
        self.map2: np.ndarray | None = None

        # Output dimensions — square (fisheye lens projects a circle, square is optimal)
        self.max_output_size: int = 500  # Performance cap per side
        self.output_width: int = 500  # Will be recalculated from lens circle
        self.output_height: int = 500  # Will be recalculated from lens circle

        # Input stream dimensions (set on first frame)
        self._input_width: int = 0
        self._input_height: int = 0

        # Legacy parameters (kept for settings compatibility)
        self.offset_x: float = 0.026
        self.offset_y: float = 0.474
        self.crop_enabled: bool = True
        self.crop_width_ratio: float = 0.9
        self.crop_center_x: float = 0.5
        self.src_points_normalized: list[list[float]] = [[0.012, 1.0], [0.988, 1.0], [0.837, 0.727], [0.372, 0.727]]
        self.src_points: list[list[float]] = []
        self.dst_points: list[list[float]] = []
        self.perspective_matrix: np.ndarray | None = None

    def initialize_for_resolution(self, width: int, height: int):
        """
        Initialize camera calibration and undistortion maps for given resolution.
        Matches the archived fisheye prototype logic that was ported into this service.

        Output is square — the fisheye lens projects a circle onto the sensor,
        so the sensor's aspect ratio is irrelevant. Square maximizes the
        useful area extracted from the circular projection.

        Args:
            width: Input frame width
            height: Input frame height
        """
        self._input_width = width
        self._input_height = height

        # Square output sized from the lens circle diameter, capped for performance
        scale = min(width / self.calibration_width, height / self.calibration_height)
        scaled_diameter = int(self.radius * 2 * scale)
        side = min(scaled_diameter, self.max_output_size)
        self.output_width = side
        self.output_height = side
        logging.info(
            f"Base top view output: {side}x{side} square "
            f"(from {width}x{height} stream, scaled_diameter={scaled_diameter})"
        )

        self._compute_remap_tables()

    def _compute_remap_tables(self):
        """Compute remap lookup tables for fast image transformation.
        Preserves the historical calibration math from the archived fisheye prototype.

        Calibration parameters (center_x, center_y, radius) are scaled from
        calibration resolution to actual input stream resolution."""

        width = self._input_width
        height = self._input_height

        # Scale calibration parameters from calibration resolution to actual stream resolution
        scale_x = width / self.calibration_width
        scale_y = height / self.calibration_height
        scaled_center_x = self.center_x * scale_x
        scaled_center_y = self.center_y * scale_y
        scaled_radius = self.radius * min(scale_x, scale_y)  # Use min to keep circle inscribed

        logging.info(
            f"Scaled calibration: center=({scaled_center_x:.0f},{scaled_center_y:.0f}) "
            f"radius={scaled_radius:.0f} (scale {scale_x:.3f}x{scale_y:.3f} "
            f"from {self.calibration_width}x{self.calibration_height} to {width}x{height})"
        )

        # For circular fisheye, focal length = radius (equidistant projection)
        focal_for_fisheye = scaled_radius

        # Camera matrix (intrinsics) for fisheye input
        self.camera_matrix = np.array(
            [[focal_for_fisheye, 0, scaled_center_x], [0, focal_for_fisheye, scaled_center_y], [0, 0, 1]],
            dtype=np.float32,
        )

        # Distortion coefficients (OpenCV fisheye model)
        self.dist_coeffs = np.array([self.k1, self.k2, self.k3, self.k4], dtype=np.float32)

        # New camera matrix for output (perspective projection)
        # Clamp FOV to avoid tan(90°) = infinity
        fov_h_rad = np.deg2rad(min(self.fov_h, 179.9))
        fov_v_rad = np.deg2rad(min(self.fov_v, 179.9))

        # Calculate focal length for perspective output
        if self.fov_h < 120:
            new_fx = (self.output_width / 2.0) / np.tan(fov_h_rad / 2.0) * self.zoom
        else:
            new_fx = focal_for_fisheye * self.zoom * (120.0 / self.fov_h)

        if self.fov_v < 120:
            new_fy = (self.output_height / 2.0) / np.tan(fov_v_rad / 2.0) * self.zoom
        else:
            new_fy = focal_for_fisheye * self.zoom * (120.0 / self.fov_v)

        new_camera_matrix = np.array(
            [[new_fx, 0, self.output_width / 2.0], [0, new_fy, self.output_height / 2.0], [0, 0, 1]], dtype=np.float32
        )

        # Rotation matrix (for rotation parameter)
        rotation_rad = np.deg2rad(self.rotation)
        R = cv2.Rodrigues(np.array([0, 0, rotation_rad], dtype=np.float32))[0]

        # Compute remap tables using OpenCV fisheye model
        try:
            self.map1, self.map2 = cv2.fisheye.initUndistortRectifyMap(
                self.camera_matrix,
                self.dist_coeffs,
                R,
                new_camera_matrix,
                (self.output_width, self.output_height),
                cv2.CV_32FC1,
            )
        except Exception as e:
            logging.error(f"Error computing remap tables: {e}")
            self.map1, self.map2 = np.meshgrid(
                np.arange(self.output_width, dtype=np.float32), np.arange(self.output_height, dtype=np.float32)
            )

    def _calculate_destination_points(self):
        """Calculate destination points based on zoom and pan offsets"""
        center_x = self.output_width * 0.5
        center_y = self.output_height * 0.5

        # Apply pan offsets
        center_x += self.offset_x * self.output_width * 0.5
        center_y += self.offset_y * self.output_height * 0.5

        # Base coordinates relative to center
        base_coords = [
            [-0.3, 0.3],  # Bottom-left
            [0.3, 0.3],  # Bottom-right
            [0.3, -0.3],  # Top-right
            [-0.3, -0.3],  # Top-left
        ]

        # Apply zoom and convert to absolute coordinates
        self.dst_points = [
            [
                center_x + (coord[0] * self.output_width * self.zoom),
                center_y + (coord[1] * self.output_height * self.zoom),
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
        Apply perspective transformation for top view

        Args:
            frame: Undistorted input frame

        Returns:
            Transformed top view frame
        """
        if len(self.src_points) != 4 or len(self.dst_points) != 4:
            return cv2.resize(frame, (self.output_width, self.output_height))

        src = np.array(self.src_points, dtype=np.float32)
        dst = np.array(self.dst_points, dtype=np.float32)

        self.perspective_matrix = cv2.getPerspectiveTransform(src, dst)
        warped = cv2.warpPerspective(frame, self.perspective_matrix, (self.output_width, self.output_height))

        # Apply vertical crop if enabled
        if self.crop_enabled:
            warped = self._crop_to_vertical_road(warped)

        return warped

    def _crop_to_vertical_road(self, frame: np.ndarray) -> np.ndarray:
        """
        Crop to vertical rectangle

        Args:
            frame: Full top view frame

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
        Processing pipeline: fisheye undistortion with circular crop and zoom.

        Args:
            frame: Input BGR frame

        Returns:
            Undistorted and cropped frame
        """
        if self.map1 is None or self.map2 is None:
            return frame

        # Apply fisheye undistortion with proper circular boundary and zoom
        undistorted = cv2.remap(frame, self.map1, self.map2, interpolation=cv2.INTER_LINEAR)
        return undistorted


class BaseTopViewImageProvider(QQuickImageProvider):
    """Image provider for QML display with thread-safe access"""

    def __init__(self, width: int = 500, height: int = 500):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(width, height, QImage.Format_RGB888)
        self.image.fill(0)  # Black background initially
        self._image_lock = QMutex()

    def requestImage(self, id, size, requestedSize):
        """Thread-safe image retrieval for QML"""
        with QMutexLocker(self._image_lock):
            return self.image.copy()


class BaseTopViewWorker(QObject):
    """Worker that processes frames in separate thread"""

    frameReady = Signal()

    def __init__(self, image_provider: BaseTopViewImageProvider):
        super().__init__()
        self.image_provider = image_provider
        self.transformer = BaseTopViewTransformer()
        self._processing = False
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    @Slot()
    def recompute_maps(self) -> None:
        """Recompute undistortion maps on the worker thread only (TD-039)."""
        if not self._initialized:
            return
        if getattr(self.transformer, "_input_width", 0) <= 0:
            return
        try:
            self.transformer._compute_remap_tables()
        except Exception as e:
            self.logger.error(f"Error recomputing distortion maps: {e}")

    @Slot(object, QImage)
    def process_frame(self, camera_type: CameraType, qimage: QImage):
        """
        Process incoming frame from VideoStreamHandler

        Args:
            camera_type: Type of camera (should be BASE_TOP)
            qimage: QImage from camera stream
        """
        # Skip if already processing (stay realtime, drop frames if needed)
        if self._processing:
            return

        # Only process BASE_TOP camera
        if camera_type != CameraType.BASE_TOP:
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

            # Initialize transformer on first frame or when resolution changes
            if (
                not self._initialized
                or width != self.transformer._input_width
                or height != self.transformer._input_height
            ):
                self.transformer.initialize_for_resolution(width, height)
                self._initialized = True

            # Apply top view transformation
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
            self.logger.error(f"Error processing base top view frame: {e}")

        finally:
            self._processing = False


class BaseTopViewService(QObject):
    """Main service for base top view integration"""

    frameReady = Signal()
    # Internal: service (GUI) → worker (queued) map recompute request.
    mapsRecomputeRequested = Signal()

    # Parameter change signals
    zoomChanged = Signal(float)
    offsetXChanged = Signal(float)
    offsetYChanged = Signal(float)
    cropEnabledChanged = Signal(bool)
    cropWidthRatioChanged = Signal(float)
    cropCenterXChanged = Signal(float)
    k1Changed = Signal(float)
    k2Changed = Signal(float)
    k3Changed = Signal(float)
    k4Changed = Signal(float)
    editModeChanged = Signal(bool)
    sourcePointsChanged = Signal()
    enabledChanged = Signal(bool)

    def __init__(self, video_handler: VideoStreamHandler, settings_manager=None, parent: QObject | None = None):
        super().__init__(parent)
        self.video_handler = video_handler
        self.settings_manager = settings_manager
        self.image_provider = BaseTopViewImageProvider()
        self.logger = logging.getLogger(__name__)
        self._edit_mode = False
        self._enabled = False  # Start disabled to save resources
        self._frame_ready_connected = False
        self._base_top_stream = None

        # Create worker and thread
        self.worker = BaseTopViewWorker(self.image_provider)
        self.worker_thread = QThread()

        # Move worker to thread
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker.frameReady.connect(self.frameReady.emit)
        # GUI → worker: queue map recompute so map1/map2 writes never race remap.
        self.mapsRecomputeRequested.connect(
            self.worker.recompute_maps,
            Qt.QueuedConnection,
        )

        # Store reference to BASE_TOP camera stream but don't connect yet
        self._base_top_stream = video_handler.camera_streams.get(CameraType.BASE_TOP)
        if self._base_top_stream:
            self.logger.info("Base top view service found BASE_TOP camera stream")
        else:
            self.logger.warning("BASE_TOP camera stream not found")

        # Coalesce rapid calibration slider updates onto one queued worker recompute.
        self._map_recompute_timer = QTimer(self)
        self._map_recompute_timer.setSingleShot(True)
        self._map_recompute_timer.timeout.connect(self._flush_map_recompute)

        # Start thread
        self.worker_thread.start()
        self.logger.info("Base top view worker thread started")

        # Migrate old bird_view settings to base_top_view if they exist
        if self.settings_manager:
            self._migrate_settings()

        # Seed draft-live state from SettingsManager (defaults from schema).
        if self.settings_manager:
            for attr, key in _BASE_TOP_SETTING_KEYS:
                setattr(self, attr, self.settings_manager.get(key, _schema_default(key)))
            src_points = self.settings_manager.get(
                _BASE_TOP_SRC_POINTS_KEY, _schema_default(_BASE_TOP_SRC_POINTS_KEY)
            )
            self.worker.transformer.src_points_normalized = src_points
            self.logger.info("Base top view settings loaded from SettingsManager")

    def _migrate_settings(self):
        """Migrate old bird_view settings to base_top_view settings"""
        if not self.settings_manager:
            return

        # List of settings to migrate
        settings_map = {
            "bird_view_zoom": "base_top_view_zoom",
            "bird_view_offset_x": "base_top_view_offset_x",
            "bird_view_offset_y": "base_top_view_offset_y",
            "bird_view_crop_enabled": "base_top_view_crop_enabled",
            "bird_view_crop_width_ratio": "base_top_view_crop_width_ratio",
            "bird_view_crop_center_x": "base_top_view_crop_center_x",
            "bird_view_k1": "base_top_view_k1",
            "bird_view_k2": "base_top_view_k2",
            "bird_view_src_points": "base_top_view_src_points",
        }

        migrated_any = False
        for old_key, new_key in settings_map.items():
            # If old key exists and new key doesn't, migrate
            old_value = self.settings_manager.get(old_key, None)
            new_value = self.settings_manager.get(new_key, None)
            if old_value is not None and new_value is None:
                self.settings_manager.set(new_key, old_value)
                migrated_any = True

        if migrated_any:
            # Save all settings to persist migration
            self.settings_manager.save_all()
            self.logger.info("Migrated old bird_view settings to base_top_view")

    def cleanup(self):
        """Clean up thread resources"""
        try:
            self.logger.info("Stopping base top view worker thread...")
            self._enabled = False
            if hasattr(self, "_map_recompute_timer") and self._map_recompute_timer is not None:
                self._map_recompute_timer.stop()
            if self._base_top_stream is not None and self._frame_ready_connected:
                try:
                    self._base_top_stream.frameReady.disconnect(self.worker.process_frame)
                    self._frame_ready_connected = False
                except RuntimeError:
                    # Already disconnected
                    self._frame_ready_connected = False
            self.worker_thread.quit()
            self.worker_thread.wait()
            self.logger.info("Base top view worker thread stopped")
        except Exception as e:
            self.logger.error(f"Error during base top view cleanup: {e}")

    # ========== Qt Properties ==========

    @Property(float, notify=zoomChanged)
    def zoom(self) -> float:
        return self.worker.transformer.zoom

    @zoom.setter
    def zoom(self, value: float):
        if self.worker.transformer.zoom != value:
            self.worker.transformer.zoom = value
            if self.worker._initialized:
                self._reinitialize_maps()
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
            # Only update the scalar; worker recompute rebuilds dist_coeffs/maps.
            self.worker.transformer.k1 = value
            if self.worker._initialized:
                self._reinitialize_maps()
            self.k1Changed.emit(value)

    @Property(float, notify=k2Changed)
    def k2(self) -> float:
        return self.worker.transformer.k2

    @k2.setter
    def k2(self, value: float):
        if self.worker.transformer.k2 != value:
            self.worker.transformer.k2 = value
            if self.worker._initialized:
                self._reinitialize_maps()
            self.k2Changed.emit(value)

    @Property(float, notify=k3Changed)
    def k3(self) -> float:
        return self.worker.transformer.k3

    @k3.setter
    def k3(self, value: float):
        if self.worker.transformer.k3 != value:
            self.worker.transformer.k3 = value
            if self.worker._initialized:
                self._reinitialize_maps()
            self.k3Changed.emit(value)

    @Property(float, notify=k4Changed)
    def k4(self) -> float:
        return self.worker.transformer.k4

    @k4.setter
    def k4(self, value: float):
        if self.worker.transformer.k4 != value:
            self.worker.transformer.k4 = value
            if self.worker._initialized:
                self._reinitialize_maps()
            self.k4Changed.emit(value)

    def _reinitialize_maps(self):
        """Coalesce and queue undistortion-map recompute onto the worker (TD-039).

        Never calls ``_compute_remap_tables`` on the GUI thread — the worker
        owns map1/map2 writes so they never race with ``cv2.remap``.
        """
        # Restarting a 0ms single-shot timer collapses rapid slider events.
        self._map_recompute_timer.start(0)

    def _flush_map_recompute(self) -> None:
        """Emit the queued worker recompute after coalescing."""
        try:
            self.mapsRecomputeRequested.emit()
        except Exception as e:
            self.logger.error(f"Error requesting distortion map recompute: {e}")

    @Slot()
    def resetToDefaults(self):
        """Reset draft-live state to schema defaults, then persist via SettingsManager.

        Live calibration still lives on this service; Save/Reset are the only
        settings persistence boundaries (not per-slider apply).
        """
        for attr, key in _BASE_TOP_SETTING_KEYS:
            setattr(self, attr, _schema_default(key))

        default_src_points = list(_schema_default(_BASE_TOP_SRC_POINTS_KEY))
        self.worker.transformer.src_points_normalized = default_src_points
        self.sourcePointsChanged.emit()

        if self.settings_manager:
            for attr, key in _BASE_TOP_SETTING_KEYS:
                self.settings_manager.set(key, getattr(self, attr))
            self.settings_manager.set(_BASE_TOP_SRC_POINTS_KEY, default_src_points)
            self.settings_manager.save_all()
            self.logger.info("Base top view settings reset to schema defaults and saved")

    @Slot(result=bool)
    def saveSettings(self) -> bool:
        """Persist current draft-live service state into SettingsManager (QML callable)."""
        if not self.settings_manager:
            self.logger.warning("Cannot save: no settings_manager")
            return False

        try:
            for attr, key in _BASE_TOP_SETTING_KEYS:
                self.settings_manager.set(key, getattr(self, attr))
            self.settings_manager.set(_BASE_TOP_SRC_POINTS_KEY, self.sourcePoints)
            success, msg = self.settings_manager.save_all()
            if success:
                self.logger.info("Base top view settings saved")
            else:
                self.logger.error(f"Failed to save base top view settings: {msg}")
            return success
        except Exception as e:
            self.logger.error(f"Error saving base top view settings: {e}")
            return False

    # ========== Source Points Properties ==========

    @Property("QVariantList", notify=sourcePointsChanged)
    def sourcePoints(self) -> list[list[float]]:
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
                    [pt[0] * width, pt[1] * height] for pt in self.worker.transformer.src_points_normalized
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

    # ========== Enabled Property (for pausing processing) ==========

    @Property(bool, notify=enabledChanged)
    def enabled(self) -> bool:
        """Whether base top view processing is active"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        if self._enabled != value:
            self._enabled = value
            self.enabledChanged.emit(value)

            # Connect/disconnect signal based on enabled state
            if value and self._base_top_stream:
                # P-02: base top is not warm-started; demand-start the pipeline.
                try:
                    self.video_handler.ensure_stream_running(CameraType.BASE_TOP)
                except Exception as exc:
                    self.logger.warning("Could not start BASE_TOP stream: %s", exc)
                self._base_top_stream.frameReady.connect(self.worker.process_frame)
                self._frame_ready_connected = True
                self.logger.info("Base top view processing enabled")
            elif not value and self._base_top_stream:
                try:
                    self._base_top_stream.frameReady.disconnect(self.worker.process_frame)
                    self._frame_ready_connected = False
                    self.logger.info("Base top view processing disabled")
                except RuntimeError:
                    # Already disconnected
                    self._frame_ready_connected = False

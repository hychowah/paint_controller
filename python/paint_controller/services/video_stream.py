import logging
import threading
import time
from collections.abc import Callable
from copy import copy
from dataclasses import dataclass
from enum import Enum

import gi
from PySide6.QtCore import Property, QMutex, QMutexLocker, QObject, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from paint_controller.core.availability import AvailabilityState
from paint_controller.core.availability_watchdog import AvailabilityWatchdog

gi.require_version("Gst", "1.0")
gi.require_version("GstApp", "1.0")
from gi.repository import Gst

logger = logging.getLogger(__name__)

# Operator-facing rule: hide frozen last frame after this long without samples.
STREAM_FRAME_TIMEOUT_S = 3.0
STREAM_AVAILABILITY_POLL_MS = 250

# ROS2 imports (optional - gracefully handle if not available)
try:
    from rclpy.node import Node
    from std_msgs.msg import Bool, String

    ROS2_AVAILABLE = True
except ImportError:
    ROS2_AVAILABLE = False
    logging.warning("ROS2 not available - VideoStreamHandler will run in standalone mode")


class CameraType(Enum):
    """Enumeration of supported camera types"""

    END_EFFECTOR = "end_effector"
    BASE_FRONT = "base_front"
    BASE_REAR = "base_rear"
    BASE_TOP = "base_top"
    CONFIGURABLE = "configurable"


@dataclass
class CameraConfig:
    """Configuration for a single camera stream"""

    camera_type: CameraType
    port: int
    name: str
    enabled: bool = True
    width: int = 640
    height: int = 480


class ImageProvider(QQuickImageProvider):
    """Thread-safe live-frame provider (P-06 double-buffer / COW swap).

    Writers publish a **detached** QImage via :meth:`publish` (swap under lock).
    Readers get a shallow QImage (Qt COW) — no per-request deep ``.copy()``.
    Pixel buffers of published frames are never mutated in place.
    """

    def __init__(self, camera_type: CameraType, width: int = 640, height: int = 480):
        super().__init__(QQuickImageProvider.Image)
        self.camera_type = camera_type
        self._default_width = max(int(width), 1)
        self._default_height = max(int(height), 1)
        self.image = QImage(self._default_width, self._default_height, QImage.Format_RGB888)
        self.image.fill(0)
        self._image_lock = QMutex()  # ✅ Thread-safe Qt mutex for concurrent access
        self._generation = 0

    @property
    def generation(self) -> int:
        """Monotonic frame generation; bumps on every publish/clear (P-01)."""
        with QMutexLocker(self._image_lock):
            return int(self._generation)

    def _black_placeholder(self) -> QImage:
        """Return a non-null black frame safe for QML requestImage."""
        width = self._default_width
        height = self._default_height
        if self.image is not None and not self.image.isNull():
            width = max(self.image.width(), 1)
            height = max(self.image.height(), 1)
        placeholder = QImage(width, height, QImage.Format_RGB888)
        placeholder.fill(0)
        return placeholder

    def publish(self, image: QImage) -> tuple[int, QImage]:
        """Atomically swap the front buffer. ``image`` must be detached from GST/OpenCV.

        Returns ``(generation, shallow_front)`` for optional signal consumers.
        """
        if image is None or image.isNull():
            self.clear_to_placeholder()
            with QMutexLocker(self._image_lock):
                return int(self._generation), QImage(self.image)
        # Detach from foreign (GStreamer) memory into a heap-owned buffer once.
        owned = image.copy()
        with QMutexLocker(self._image_lock):
            self.image = owned
            self._generation += 1
            return int(self._generation), QImage(self.image)

    def clear_to_placeholder(self) -> None:
        """Replace the current frame with a black placeholder under the provider lock."""
        with QMutexLocker(self._image_lock):
            self.image = self._black_placeholder()
            self._generation += 1

    def requestImage(self, id, size, requestedSize):
        from paint_controller.utils.perf_counters import PERF

        PERF.incr("image_request")
        with QMutexLocker(self._image_lock):
            # Never return None: render thread may call during stream cleanup.
            if self.image is None or self.image.isNull():
                return self._black_placeholder()
            # Shallow QImage (COW): safe while we never mutate published pixels in place.
            return QImage(self.image)


class CameraStream(QObject):
    """Individual camera stream handler with thread-safe state management"""

    frameReady = Signal(CameraType, QImage)

    def __init__(self, config: CameraConfig):
        super().__init__()
        self.config = config
        self.pipeline = None
        self.sink = None
        self.image_provider = ImageProvider(config.camera_type, config.width, config.height)
        self._is_running = False
        self._running_lock = threading.RLock()

        if config.enabled:
            self._create_pipeline()

    def _create_pipeline(self):
        """Create GStreamer pipeline for this camera"""
        try:
            # Create pipeline with unique sink name based on camera type
            sink_name = f"{self.config.camera_type.value}_sink"
            pipeline_str = (
                f"udpsrc port={self.config.port} "
                f'caps="application/x-rtp, media=(string)video, clock-rate=(int)90000, '
                f'encoding-name=(string)H264, payload=(int)96" '
                f"! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB "
                f"! appsink name={sink_name}"
            )

            self.pipeline = Gst.parse_launch(pipeline_str)
            self.sink = self.pipeline.get_by_name(sink_name)

            if self.sink:
                self.sink.set_property("emit-signals", True)
                self.sink.connect("new-sample", self._on_new_sample)
            else:
                raise RuntimeError(f"Failed to create sink for {self.config.name}")

        except Exception as e:
            logger.error("Error creating pipeline for %s: %s", self.config.name, e)
            self.pipeline = None
            self.sink = None

    def _on_new_sample(self, sink):
        sample = None
        map_info = None

        try:
            sample = sink.emit("pull-sample")
            if not sample:
                return Gst.FlowReturn.ERROR

            buffer = sample.get_buffer()
            caps = sample.get_caps()

            if not buffer or not caps:
                return Gst.FlowReturn.ERROR

            structure = caps.get_structure(0)
            if not structure:
                return Gst.FlowReturn.ERROR

            width = structure.get_value("width")
            height = structure.get_value("height")

            if not width or not height:
                return Gst.FlowReturn.ERROR

            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success or not map_info:
                return Gst.FlowReturn.ERROR

            try:
                image = QImage(map_info.data, width, height, width * 3, QImage.Format_RGB888)
                # publish() deep-copies once into the provider front buffer (P-06).
                _gen, front = self.image_provider.publish(image)
                from paint_controller.utils.perf_counters import PERF

                PERF.incr("frame_publish")
                self.frameReady.emit(self.config.camera_type, front)

                return Gst.FlowReturn.OK

            finally:
                if map_info is not None:
                    buffer.unmap(map_info)
                    map_info = None

        except Exception as e:
            logger.error("Error processing sample for %s: %s", self.config.name, e)
            return Gst.FlowReturn.ERROR

        finally:
            if sample is not None:
                sample = None

    def start(self):
        with self._running_lock:  # ✅ Thread-safe lock
            if self.pipeline and not self._is_running:
                try:
                    self.pipeline.set_state(Gst.State.PLAYING)
                    self._is_running = True
                    logger.info("Started stream for %s", self.config.name)
                    return True
                except Exception as e:
                    logger.error("Error starting stream for %s: %s", self.config.name, e)
                    return False
        return False

    def stop(self):
        with self._running_lock:  # ✅ Thread-safe lock
            if self.pipeline and self._is_running:
                try:
                    self.pipeline.set_state(Gst.State.NULL)
                    self._is_running = False
                    logger.info("Stopped stream for %s", self.config.name)
                    return True
                except Exception as e:
                    logger.error("Error stopping stream for %s: %s", self.config.name, e)
                    return False
        return False

    def set_sample_callback(self, callback: Callable[[CameraType, QImage], None]):
        """Deprecated: Use frameReady signal instead"""
        pass

    def is_running(self) -> bool:
        with self._running_lock:  # ✅ Thread-safe lock
            return self._is_running

    def cleanup(self):
        try:
            self.stop()

            if self.sink:
                try:
                    self.sink.disconnect("new-sample")
                except Exception:
                    pass

            # This triggers garbage collection and memory release
            if self.sink is not None:
                self.sink = None

            if self.pipeline is not None:
                # Ensure pipeline is in NULL state before releasing
                try:
                    if self.pipeline.get_state(0)[1] != Gst.State.NULL:
                        self.pipeline.set_state(Gst.State.NULL)
                except Exception:
                    pass
                self.pipeline = None

            if self.image_provider is not None:
                # Keep a locked black placeholder so requestImage never hits None.copy().
                self.image_provider.clear_to_placeholder()

            logger.info("Cleaned up stream for %s", self.config.name)

        except Exception as e:
            logger.error("Error during cleanup for %s: %s", self.config.name, e)


class VideoStreamHandler(QObject):
    """Unified video stream handler for multiple cameras with ROS2 integration"""

    # Signals for different camera frames
    endEffectorFrameReady = Signal()
    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()
    configurableFrameReady = Signal()

    # General frame ready signal with camera type
    frameReady = Signal(str)  # Emits camera type as string

    # Per-feed liveness (frame within STREAM_FRAME_TIMEOUT_S). Default unavailable.
    endEffectorStreamAvailableChanged = Signal()
    baseFrontStreamAvailableChanged = Signal()
    baseRearStreamAvailableChanged = Signal()

    # ROS2 signals for status and recording
    recordingStatusChanged = Signal(str)  # Emits recording status ("recording", "stopped", "failed")
    baseRecordingStatusChanged = Signal(str)  # Emits base camera recording status
    cameraStatusChanged = Signal(str)  # Emits camera status ("streaming", "idle", "error")

    def __init__(self, configurable_port: int = 5000, ros_node: Node | None = None):
        """
        Initialize VideoStreamHandler with optional ROS2 integration.

        Args:
            configurable_port: Port for configurable camera stream
            ros_node: ROS2 node for publishing/subscribing to recording commands and status
        """
        super().__init__()

        # Initialize GStreamer
        Gst.init(None)

        # ROS2 integration
        self._ros_node = ros_node
        self._ros_initialized = False
        self._recording_state = False
        self._base_recording_state = False

        # Setup ROS2 publishers and subscribers if node is provided
        if ROS2_AVAILABLE and ros_node is not None:
            try:
                self._setup_ros_interface()
                self._ros_initialized = True
                self._log("ROS2 interface initialized for VideoStreamHandler")
            except Exception as e:
                self._log(f"Failed to setup ROS2 interface: {e}", level="warning")

        # ✅ Thread-safe lock for camera_streams dictionary
        self._streams_lock = threading.RLock()
        self._startup_lock = threading.RLock()
        self._streams_started = False

        # Operator feeds with fullscreen / preview consumers (not base-top processed path).
        self._feed_availability: dict[CameraType, AvailabilityState] = {
            CameraType.END_EFFECTOR: AvailabilityState(STREAM_FRAME_TIMEOUT_S),
            CameraType.BASE_FRONT: AvailabilityState(STREAM_FRAME_TIMEOUT_S),
            CameraType.BASE_REAR: AvailabilityState(STREAM_FRAME_TIMEOUT_S),
        }
        self._feed_available_signals: dict[CameraType, Signal] = {
            CameraType.END_EFFECTOR: self.endEffectorStreamAvailableChanged,
            CameraType.BASE_FRONT: self.baseFrontStreamAvailableChanged,
            CameraType.BASE_REAR: self.baseRearStreamAvailableChanged,
        }
        self._watchdog: AvailabilityWatchdog | None = None

        # Define camera configurations
        self.camera_configs = {
            CameraType.END_EFFECTOR: CameraConfig(
                camera_type=CameraType.END_EFFECTOR, port=5001, name="End Effector Camera", enabled=True
            ),
            CameraType.BASE_FRONT: CameraConfig(
                camera_type=CameraType.BASE_FRONT, port=5002, name="Base Front Camera", enabled=True
            ),
            CameraType.BASE_TOP: CameraConfig(
                camera_type=CameraType.BASE_TOP, port=5003, name="Base Top Camera", enabled=True
            ),
            CameraType.BASE_REAR: CameraConfig(
                camera_type=CameraType.BASE_REAR, port=5004, name="Base Rear Camera", enabled=True
            ),
            CameraType.CONFIGURABLE: CameraConfig(
                camera_type=CameraType.CONFIGURABLE,
                port=configurable_port,
                name="Configurable Camera",
                enabled=False,  # Disabled by default, can be enabled if needed
            ),
        }

        # Create camera streams
        self.camera_streams: dict[CameraType, CameraStream] = {}
        self._create_camera_streams()
        self._start_feed_availability_watchdog()

    def _setup_ros_interface(self):
        """Setup ROS2 publishers and subscribers for end effector camera recording control and status."""
        # Publisher for recording commands to end effector camera
        self._record_cmd_pub = self._ros_node.create_publisher(Bool, "/ef/camera/record/cmd", 10)

        # Subscriber for status updates from end effector camera node
        self._status_sub = self._ros_node.create_subscription(String, "/ef/camera/status", self._status_callback, 10)

        # Publisher for recording commands to base camera
        self._base_record_cmd_pub = self._ros_node.create_publisher(Bool, "/base/camera/record/cmd", 10)

        # Subscriber for status updates from base camera node
        self._base_status_sub = self._ros_node.create_subscription(
            String, "/base/camera/status", self._base_status_callback, 10
        )

        self._log(
            "ROS2 interface setup complete: /ef/camera/record/cmd (pub), /ef/camera/status (sub), /base/camera/record/cmd (pub), /base/camera/status (sub)"
        )

    def _record_cmd_callback(self, msg: Bool):
        """
        ROS2 callback for recording commands from remote camera node.

        Args:
            msg: Bool message where True = start recording, False = stop recording
        """
        if msg.data:
            self._log("ROS2 recording command received: START")
            self.start_recording()
        else:
            self._log("ROS2 recording command received: STOP")
            self.stop_recording()

    @Slot()
    def start_recording(self):
        """
        Qt Slot to start recording video from end effector camera.
        Publishes recording command to ROS2.
        """
        if self._recording_state:
            self._log("Already recording", level="warning")
            return

        self._recording_state = True
        self._log("Recording started - publishing command to /ef/camera/record/cmd")
        self.recordingStatusChanged.emit("recording")

        if self._ros_initialized:
            self._publish_record_command(True)

    @Slot()
    def stop_recording(self):
        """
        Qt Slot to stop recording video.
        Publishes recording stop command to ROS2.
        """
        if not self._recording_state:
            self._log("Not currently recording", level="warning")
            return

        self._recording_state = False
        self._log("Recording stopped - publishing command to /ef/camera/record/cmd")
        self.recordingStatusChanged.emit("stopped")

        if self._ros_initialized:
            self._publish_record_command(False)

    @Slot()
    def toggleRecording(self):
        """
        Qt Slot to toggle recording state.
        Starts recording if not recording, stops if recording.
        """
        self._log("Toggling recording state")
        if self._recording_state:
            self.stop_recording()
        else:
            self.start_recording()

    @Property(bool, notify=recordingStatusChanged)
    def is_recording(self) -> bool:
        """Qt Property to check if currently recording."""
        return self._recording_state

    @Slot()
    def start_base_recording(self):
        """
        Qt Slot to start recording video from base camera.
        Publishes recording command to ROS2.
        """
        if self._base_recording_state:
            self._log("Base camera already recording", level="warning")
            return

        self._base_recording_state = True
        self._log("Base camera recording started - publishing command to /base/camera/record/cmd")
        self.baseRecordingStatusChanged.emit("recording")

        if self._ros_initialized:
            self._publish_base_record_command(True)

    @Slot()
    def stop_base_recording(self):
        """
        Qt Slot to stop recording video from base camera.
        Publishes recording stop command to ROS2.
        """
        if not self._base_recording_state:
            self._log("Base camera not currently recording", level="warning")
            return

        self._base_recording_state = False
        self._log("Base camera recording stopped - publishing command to /base/camera/record/cmd")
        self.baseRecordingStatusChanged.emit("stopped")

        if self._ros_initialized:
            self._publish_base_record_command(False)

    @Slot()
    def toggleBaseRecording(self):
        """
        Qt Slot to toggle base camera recording state.
        Starts recording if not recording, stops if recording.
        """
        self._log("Toggling base camera recording state")
        if self._base_recording_state:
            self.stop_base_recording()
        else:
            self.start_base_recording()

    @Property(bool, notify=baseRecordingStatusChanged)
    def is_base_recording(self) -> bool:
        """Qt Property to check if base camera is currently recording."""
        return self._base_recording_state

    def _status_callback(self, msg: String):
        """
        ROS2 callback to receive camera status from remote camera node.

        Args:
            msg: String message with camera status (e.g., "STREAMING", "RECORDING", "ERROR")
        """
        status = msg.data
        self.cameraStatusChanged.emit(status)

    def _base_status_callback(self, msg: String):
        """
        ROS2 callback to receive base camera status from remote camera node.

        Args:
            msg: String message with camera status (e.g., "STREAMING", "RECORDING", "ERROR")
        """
        status = msg.data
        self.baseRecordingStatusChanged.emit(status)

    def _publish_record_command(self, start_recording: bool):
        """
        Publish recording command to remote camera node.

        Args:
            start_recording: True to start recording, False to stop recording
        """
        if not self._ros_initialized or self._record_cmd_pub is None:
            return

        try:
            msg = Bool()
            msg.data = start_recording
            self._record_cmd_pub.publish(msg)
            cmd_str = "START" if start_recording else "STOP"
            self._log(f"Published recording command: {cmd_str}")
        except Exception as e:
            self._log(f"Failed to publish recording command: {e}", level="error")

    def _publish_base_record_command(self, start_recording: bool):
        """
        Publish recording command to base camera node.

        Args:
            start_recording: True to start recording, False to stop recording
        """
        if not self._ros_initialized or self._base_record_cmd_pub is None:
            return

        try:
            msg = Bool()
            msg.data = start_recording
            self._base_record_cmd_pub.publish(msg)
            cmd_str = "START" if start_recording else "STOP"
            self._log(f"Published base camera recording command: {cmd_str}")
        except Exception as e:
            self._log(f"Failed to publish base camera recording command: {e}", level="error")

    def _publish_status(self, status: str):
        """
        Deprecated: Status is now received from remote camera node via subscription.

        Args:
            status: Status string (no longer used)
        """
        pass

    def _log(self, message: str, level: str = "info"):
        """
        Log message using ROS2 logger if available, otherwise use print.

        Args:
            message: Message to log
            level: Log level ("info", "warning", "error", "debug")
        """
        if self._ros_node is not None:
            logger = self._ros_node.get_logger()
            if level == "info":
                logger.info(f"[VideoStreamHandler] {message}")
            elif level == "warning":
                logger.warn(f"[VideoStreamHandler] {message}")
            elif level == "error":
                logger.error(f"[VideoStreamHandler] {message}")
            elif level == "debug":
                logger.debug(f"[VideoStreamHandler] {message}")
        else:
            logger.info("%s", message)

    def _create_camera_streams(self):
        """Create all configured camera streams"""
        for camera_type, config in self.camera_configs.items():
            if config.enabled:
                try:
                    stream = CameraStream(config)
                    stream.frameReady.connect(self._on_camera_frame)
                    self.camera_streams[camera_type] = stream
                    logger.info("Created stream for %s", config.name)
                except Exception as e:
                    logger.error("Failed to create stream for %s: %s", config.name, e)

    def _on_camera_frame(self, camera_type: CameraType, image: QImage):
        if camera_type == CameraType.END_EFFECTOR:
            self.endEffectorFrameReady.emit()
        elif camera_type == CameraType.BASE_FRONT:
            self.baseFrontFrameReady.emit()
        elif camera_type == CameraType.BASE_REAR:
            self.baseRearFrameReady.emit()
        elif camera_type == CameraType.CONFIGURABLE:
            self.configurableFrameReady.emit()

        self.frameReady.emit(camera_type.value)
        self._note_feed_frame(camera_type)

    def _start_feed_availability_watchdog(self) -> None:
        """Poll feed freshness on the Qt thread (same pattern as device shells)."""
        if self._watchdog is not None:
            return
        self._watchdog = AvailabilityWatchdog(
            self._check_feed_availability,
            interval_ms=STREAM_AVAILABILITY_POLL_MS,
            parent=self,
        )

    def _note_feed_frame(self, camera_type: CameraType, now: float | None = None) -> None:
        """Record a live sample for operator-facing feeds; mark available when it flips."""
        state = self._feed_availability.get(camera_type)
        if state is None:
            return
        state.record_status_update(now)
        self._set_feed_available(camera_type, True)

    def _set_feed_available(self, camera_type: CameraType, available: bool) -> None:
        state = self._feed_availability.get(camera_type)
        if state is None:
            return
        if not state.set_available(available):
            return
        if not available:
            # Drop frozen last frame so QML cannot rediscover stale pixels.
            stream = self._get_stream(camera_type)
            if stream is not None:
                stream.image_provider.clear_to_placeholder()
        signal = self._feed_available_signals.get(camera_type)
        if signal is not None:
            signal.emit()

    def _check_feed_availability(self) -> None:
        """Mark feeds unavailable after STREAM_FRAME_TIMEOUT_S without frames."""
        now = time.time()
        for camera_type, state in self._feed_availability.items():
            if state.available and not state.status_is_recent(now):
                self._set_feed_available(camera_type, False)

    def _feed_is_available(self, camera_type: CameraType) -> bool:
        state = self._feed_availability.get(camera_type)
        return bool(state.available) if state is not None else False

    @Property(bool, notify=endEffectorStreamAvailableChanged)
    def endEffectorStreamAvailable(self) -> bool:
        return self._feed_is_available(CameraType.END_EFFECTOR)

    @Property(bool, notify=baseFrontStreamAvailableChanged)
    def baseFrontStreamAvailable(self) -> bool:
        return self._feed_is_available(CameraType.BASE_FRONT)

    @Property(bool, notify=baseRearStreamAvailableChanged)
    def baseRearStreamAvailable(self) -> bool:
        return self._feed_is_available(CameraType.BASE_REAR)

    def _get_stream(self, camera_type: CameraType) -> CameraStream | None:
        """
        Thread-safe stream getter.

        Acquires lock to safely retrieve a stream from the dictionary.
        """
        with self._streams_lock:
            return self.camera_streams.get(camera_type)

    @Slot(result=int)
    def start_all_streams(self):
        """
        Start all configured camera streams with thread-safe dictionary access.

        Creates a snapshot of streams to avoid issues with concurrent modifications.
        """
        with self._startup_lock:
            if self._streams_started:
                logger.info("Video streams already started; skipping duplicate startup request")
                return 0

            with self._streams_lock:
                # Create snapshot to avoid iteration issues during concurrent modifications
                streams_copy = copy(self.camera_streams)

            total_t0 = time.perf_counter()
            success_count = 0
            for camera_type, stream in streams_copy.items():
                stream_t0 = time.perf_counter()
                if stream.start():
                    success_count += 1
                    logger.info(
                        "Started %s in %.1f ms",
                        self.camera_configs[camera_type].name,
                        (time.perf_counter() - stream_t0) * 1000.0,
                    )
                else:
                    logger.warning(
                        "Failed to start %s after %.1f ms",
                        self.camera_configs[camera_type].name,
                        (time.perf_counter() - stream_t0) * 1000.0,
                    )

            self._streams_started = success_count > 0
            logger.info(
                "Video stream startup finished in %.1f ms (%s/%s started)",
                (time.perf_counter() - total_t0) * 1000.0,
                success_count,
                len(streams_copy),
            )

            return success_count

    @Slot()
    def stop_all_streams(self):
        """
        Stop all camera streams with thread-safe dictionary access.

        Creates a snapshot of streams to avoid issues with concurrent modifications.
        """
        with self._streams_lock:
            # Create snapshot to avoid iteration issues during concurrent modifications
            streams_copy = copy(self.camera_streams)

        for camera_type, stream in streams_copy.items():
            if stream.stop():
                logger.info("Stopped %s", self.camera_configs[camera_type].name)

        with self._startup_lock:
            self._streams_started = False

    def start_stream(self, camera_type: CameraType) -> bool:
        """
        Start a specific camera stream with thread-safe access.
        """
        stream = self._get_stream(camera_type)
        if stream:
            return stream.start()
        return False

    def stop_stream(self, camera_type: CameraType) -> bool:
        """
        Stop a specific camera stream with thread-safe access.
        """
        stream = self._get_stream(camera_type)
        if stream:
            return stream.stop()
        return False

    def get_image_provider(self, camera_type: CameraType) -> ImageProvider | None:
        """
        Get image provider for a specific camera with thread-safe access.
        """
        stream = self._get_stream(camera_type)
        if stream:
            return stream.image_provider
        return None

    def enable_configurable_stream(self, port: int = None):
        try:
            if port:
                self.camera_configs[CameraType.CONFIGURABLE].port = port

            self.camera_configs[CameraType.CONFIGURABLE].enabled = True

            with self._streams_lock:
                if CameraType.CONFIGURABLE not in self.camera_streams:
                    config = self.camera_configs[CameraType.CONFIGURABLE]
                    stream = CameraStream(config)
                    stream.frameReady.connect(self._on_camera_frame)
                    self.camera_streams[CameraType.CONFIGURABLE] = stream
                    logger.info("Enabled configurable stream on port %s", config.port)
                    return True
            return True
        except Exception as e:
            logger.error("Failed to enable configurable stream: %s", e)
            return False

    def disable_configurable_stream(self):
        """
        Disable the configurable camera stream with thread-safe access.
        """
        try:
            with self._streams_lock:
                if CameraType.CONFIGURABLE in self.camera_streams:
                    self.camera_streams[CameraType.CONFIGURABLE].cleanup()
                    del self.camera_streams[CameraType.CONFIGURABLE]

            self.camera_configs[CameraType.CONFIGURABLE].enabled = False
            logger.info("Disabled configurable stream")
        except Exception as e:
            logger.error("Error disabling configurable stream: %s", e)

    def get_stream_status(self) -> dict[str, bool]:
        """
        Get status of all streams with thread-safe dictionary access.

        Creates a snapshot of streams to avoid issues with concurrent modifications.
        """
        with self._streams_lock:
            # Create snapshot to avoid iteration issues
            streams_copy = copy(self.camera_streams)

        status = {}
        for camera_type, stream in streams_copy.items():
            status[camera_type.value] = stream.is_running()
        return status

    def cleanup(self):
        """
        Clean up all streams and resources with thread-safe dictionary access.

        This method properly shuts down all camera streams and releases
        all GStreamer pipeline resources. Should be called in application
        shutdown sequence to prevent resource leaks.
        """
        try:
            logger.info("Cleaning up video streams...")

            if self._watchdog is not None:
                self._watchdog.stop()
                self._watchdog = None

            with self._streams_lock:
                # Create snapshot to avoid iteration issues during cleanup
                streams_copy = copy(self.camera_streams)

            # Step 1: Stop all streams before cleanup
            self.stop_all_streams()

            # Step 2: Call cleanup on each stream
            for camera_type, stream in streams_copy.items():
                try:
                    stream.cleanup()
                    logger.info("Cleaned up %s stream", camera_type.value)
                except Exception as e:
                    logger.error("Error cleaning up %s stream: %s", camera_type.value, e)

            # Step 3: Clear the dictionary
            with self._streams_lock:
                self.camera_streams.clear()

            with self._startup_lock:
                self._streams_started = False

            for camera_type in list(self._feed_availability):
                self._set_feed_available(camera_type, False)

            logger.info("Video stream cleanup complete")

        except Exception as e:
            logger.error("Error during video stream cleanup: %s", e)

    # Properties for backward compatibility
    @property
    def ef_image_provider(self) -> ImageProvider | None:
        """Get end effector image provider"""
        return self.get_image_provider(CameraType.END_EFFECTOR)

    @property
    def front_image_provider(self) -> ImageProvider | None:
        """Get base front image provider"""
        return self.get_image_provider(CameraType.BASE_FRONT)

    @property
    def rear_image_provider(self) -> ImageProvider | None:
        """Get base rear image provider"""
        return self.get_image_provider(CameraType.BASE_REAR)

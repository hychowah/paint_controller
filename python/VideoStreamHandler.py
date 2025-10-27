from PySide6.QtCore import QObject, Signal, QMutex, QMutexLocker
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto
import threading
from copy import copy

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst

class CameraType(Enum):
    """Enumeration of supported camera types"""
    END_EFFECTOR = "end_effector"
    BASE_FRONT = "base_front"
    BASE_REAR = "base_rear"
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
    """Enhanced image provider for camera streams with thread-safe access"""
    def __init__(self, camera_type: CameraType, width: int = 640, height: int = 480):
        super().__init__(QQuickImageProvider.Image)
        self.camera_type = camera_type
        self.image = QImage(width, height, QImage.Format_RGB888)
        self._image_lock = QMutex()  # ✅ Thread-safe Qt mutex for concurrent access

    def requestImage(self, id, size, requestedSize):
        locker = QMutexLocker(self._image_lock)
        # Return a deep copy to prevent external modifications
        return self.image.copy()

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
                f"caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, "
                f"encoding-name=(string)H264, payload=(int)96\" "
                f"! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB "
                f"! appsink name={sink_name}"
            )
            
            self.pipeline = Gst.parse_launch(pipeline_str)
            self.sink = self.pipeline.get_by_name(sink_name)
            
            if self.sink:
                self.sink.set_property('emit-signals', True)
                self.sink.connect('new-sample', self._on_new_sample)
            else:
                raise RuntimeError(f"Failed to create sink for {self.config.name}")
                
        except Exception as e:
            print(f"Error creating pipeline for {self.config.name}: {e}")
            self.pipeline = None
            self.sink = None

    def _on_new_sample(self, sink):
        sample = None
        map_info = None
        
        try:
            sample = sink.emit('pull-sample')
            if not sample:
                return Gst.FlowReturn.ERROR
            
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            if not buffer or not caps:
                return Gst.FlowReturn.ERROR
            
            structure = caps.get_structure(0)
            if not structure:
                return Gst.FlowReturn.ERROR
            
            width = structure.get_value('width')
            height = structure.get_value('height')
            
            if not width or not height:
                return Gst.FlowReturn.ERROR
            
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success or not map_info:
                return Gst.FlowReturn.ERROR
            
            try:
                image = QImage(map_info.data, width, height, width * 3, QImage.Format_RGB888)
                image_copy = image.copy()
                
                locker = QMutexLocker(self.image_provider._image_lock)
                self.image_provider.image = image_copy
                locker.unlock()
                
                self.frameReady.emit(self.config.camera_type, image_copy)
                
                return Gst.FlowReturn.OK
            
            finally:
                if map_info is not None:
                    buffer.unmap(map_info)
                    map_info = None
            
        except Exception as e:
            print(f"Error processing sample for {self.config.name}: {e}")
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
                    print(f"Started stream for {self.config.name}")
                    return True
                except Exception as e:
                    print(f"Error starting stream for {self.config.name}: {e}")
                    return False
        return False

    def stop(self):
        with self._running_lock:  # ✅ Thread-safe lock
            if self.pipeline and self._is_running:
                try:
                    self.pipeline.set_state(Gst.State.NULL)
                    self._is_running = False
                    print(f"Stopped stream for {self.config.name}")
                    return True
                except Exception as e:
                    print(f"Error stopping stream for {self.config.name}: {e}")
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
                    self.sink.disconnect('new-sample')
                except:
                    pass
            
            # This triggers garbage collection and memory release
            if self.sink is not None:
                self.sink = None
            
            if self.pipeline is not None:
                # Ensure pipeline is in NULL state before releasing
                try:
                    if self.pipeline.get_state(0)[1] != Gst.State.NULL:
                        self.pipeline.set_state(Gst.State.NULL)
                except:
                    pass
                self.pipeline = None
            
            if self.image_provider:
                self.image_provider.image = None
            
            print(f"Cleaned up stream for {self.config.name}")
            
        except Exception as e:
            print(f"Error during cleanup for {self.config.name}: {e}")

class VideoStreamHandler(QObject):
    """Unified video stream handler for multiple cameras"""
    
    # Signals for different camera frames
    endEffectorFrameReady = Signal()
    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()
    configurableFrameReady = Signal()
    
    # General frame ready signal with camera type
    frameReady = Signal(str)  # Emits camera type as string
    
    def __init__(self, configurable_port: int = 5000):
        super().__init__()
        
        # Initialize GStreamer
        Gst.init(None)
        
        # ✅ Thread-safe lock for camera_streams dictionary
        self._streams_lock = threading.RLock()
        
        # Define camera configurations
        self.camera_configs = {
            CameraType.END_EFFECTOR: CameraConfig(
                camera_type=CameraType.END_EFFECTOR,
                port=5001,
                name="End Effector Camera",
                enabled=True
            ),
            CameraType.BASE_FRONT: CameraConfig(
                camera_type=CameraType.BASE_FRONT,
                port=5002,
                name="Base Front Camera", 
                enabled=True
            ),
            CameraType.BASE_REAR: CameraConfig(
                camera_type=CameraType.BASE_REAR,
                port=5003,
                name="Base Rear Camera",
                enabled=True
            ),
            CameraType.CONFIGURABLE: CameraConfig(
                camera_type=CameraType.CONFIGURABLE,
                port=configurable_port,
                name="Configurable Camera",
                enabled=False  # Disabled by default, can be enabled if needed
            )
        }
        
        # Create camera streams
        self.camera_streams: Dict[CameraType, CameraStream] = {}
        self._create_camera_streams()

    def _create_camera_streams(self):
        """Create all configured camera streams"""
        for camera_type, config in self.camera_configs.items():
            if config.enabled:
                try:
                    stream = CameraStream(config)
                    stream.frameReady.connect(self._on_camera_frame)
                    self.camera_streams[camera_type] = stream
                    print(f"Created stream for {config.name}")
                except Exception as e:
                    print(f"Failed to create stream for {config.name}: {e}")

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

    def _get_stream(self, camera_type: CameraType) -> Optional[CameraStream]:
        """
        Thread-safe stream getter.
        
        Acquires lock to safely retrieve a stream from the dictionary.
        """
        with self._streams_lock:
            return self.camera_streams.get(camera_type)

    def start_all_streams(self):
        """
        Start all configured camera streams with thread-safe dictionary access.
        
        Creates a snapshot of streams to avoid issues with concurrent modifications.
        """
        with self._streams_lock:
            # Create snapshot to avoid iteration issues during concurrent modifications
            streams_copy = copy(self.camera_streams)
        
        success_count = 0
        for camera_type, stream in streams_copy.items():
            if stream.start():
                success_count += 1
                print(f"Started {self.camera_configs[camera_type].name}")
            else:
                print(f"Failed to start {self.camera_configs[camera_type].name}")
        
        return success_count

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
                print(f"Stopped {self.camera_configs[camera_type].name}")

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

    def get_image_provider(self, camera_type: CameraType) -> Optional[ImageProvider]:
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
                    print(f"Enabled configurable stream on port {config.port}")
                    return True
            return True
        except Exception as e:
            print(f"Failed to enable configurable stream: {e}")
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
            print("Disabled configurable stream")
        except Exception as e:
            print(f"Error disabling configurable stream: {e}")

    def get_stream_status(self) -> Dict[str, bool]:
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
            print("Cleaning up video streams...")
            
            with self._streams_lock:
                # Create snapshot to avoid iteration issues during cleanup
                streams_copy = copy(self.camera_streams)
            
            # Step 1: Stop all streams before cleanup
            self.stop_all_streams()
            
            # Step 2: Call cleanup on each stream
            for camera_type, stream in streams_copy.items():
                try:
                    stream.cleanup()
                    print(f"Cleaned up {camera_type.value} stream")
                except Exception as e:
                    print(f"Error cleaning up {camera_type.value} stream: {e}")
            
            # Step 3: Clear the dictionary
            with self._streams_lock:
                self.camera_streams.clear()
            
            print("Video stream cleanup complete")
            
        except Exception as e:
            print(f"Error during video stream cleanup: {e}")

    # Properties for backward compatibility
    @property
    def ef_image_provider(self) -> Optional[ImageProvider]:
        """Get end effector image provider"""
        return self.get_image_provider(CameraType.END_EFFECTOR)

    @property
    def front_image_provider(self) -> Optional[ImageProvider]:
        """Get base front image provider"""
        return self.get_image_provider(CameraType.BASE_FRONT)

    @property
    def rear_image_provider(self) -> Optional[ImageProvider]:
        """Get base rear image provider"""
        return self.get_image_provider(CameraType.BASE_REAR)

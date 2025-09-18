from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto

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
    """Enhanced image provider for camera streams"""
    def __init__(self, camera_type: CameraType, width: int = 640, height: int = 480):
        super().__init__(QQuickImageProvider.Image)
        self.camera_type = camera_type
        self.image = QImage(width, height, QImage.Format_RGB888)

    def requestImage(self, id, size, requestedSize):
        return self.image

class CameraStream:
    """Individual camera stream handler"""
    def __init__(self, config: CameraConfig):
        self.config = config
        self.pipeline = None
        self.sink = None
        self.image_provider = ImageProvider(config.camera_type, config.width, config.height)
        self._sample_callback = None
        self._is_running = False
        
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
        """Handle new video sample"""
        try:
            sample = sink.emit('pull-sample')
            if not sample:
                return Gst.FlowReturn.ERROR
                
            buffer = sample.get_buffer()
            caps = sample.get_caps()
            
            structure = caps.get_structure(0)
            width = structure.get_value('width')
            height = structure.get_value('height')
            
            success, map_info = buffer.map(Gst.MapFlags.READ)
            if not success:
                return Gst.FlowReturn.ERROR
            
            # Create QImage from buffer data
            data = map_info.data
            image = QImage(data, width, height, width * 3, QImage.Format_RGB888)
            
            # Update image provider with a deep copy
            self.image_provider.image = image.copy()
            
            buffer.unmap(map_info)
            
            # Call external callback if registered
            if self._sample_callback:
                self._sample_callback(self.config.camera_type, image)
                
            return Gst.FlowReturn.OK
            
        except Exception as e:
            print(f"Error processing sample for {self.config.name}: {e}")
            return Gst.FlowReturn.ERROR

    def start(self):
        """Start the camera stream"""
        if self.pipeline and not self._is_running:
            try:
                self.pipeline.set_state(Gst.State.PLAYING)
                self._is_running = True
                return True
            except Exception as e:
                print(f"Error starting stream for {self.config.name}: {e}")
                return False
        return False

    def stop(self):
        """Stop the camera stream"""
        if self.pipeline and self._is_running:
            try:
                self.pipeline.set_state(Gst.State.NULL)
                self._is_running = False
                return True
            except Exception as e:
                print(f"Error stopping stream for {self.config.name}: {e}")
                return False
        return False

    def set_sample_callback(self, callback: Callable[[CameraType, QImage], None]):
        """Set callback for new samples"""
        self._sample_callback = callback

    def is_running(self) -> bool:
        """Check if stream is running"""
        return self._is_running

    def cleanup(self):
        """Clean up resources"""
        self.stop()
        if self.pipeline:
            self.pipeline = None
        self.sink = None

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
                    stream.set_sample_callback(self._on_camera_frame)
                    self.camera_streams[camera_type] = stream
                    print(f"Created stream for {config.name}")
                except Exception as e:
                    print(f"Failed to create stream for {config.name}: {e}")

    def _on_camera_frame(self, camera_type: CameraType, image: QImage):
        """Handle new frame from any camera"""
        # Emit specific signal based on camera type
        if camera_type == CameraType.END_EFFECTOR:
            self.endEffectorFrameReady.emit()
        elif camera_type == CameraType.BASE_FRONT:
            self.baseFrontFrameReady.emit()
        elif camera_type == CameraType.BASE_REAR:
            self.baseRearFrameReady.emit()
        elif camera_type == CameraType.CONFIGURABLE:
            self.configurableFrameReady.emit()
            
        # Emit general frame ready signal
        self.frameReady.emit(camera_type.value)

    def start_all_streams(self):
        """Start all configured camera streams"""
        success_count = 0
        for camera_type, stream in self.camera_streams.items():
            if stream.start():
                success_count += 1
                print(f"Started {self.camera_configs[camera_type].name}")
            else:
                print(f"Failed to start {self.camera_configs[camera_type].name}")
        
        return success_count

    def stop_all_streams(self):
        """Stop all camera streams"""
        for camera_type, stream in self.camera_streams.items():
            if stream.stop():
                print(f"Stopped {self.camera_configs[camera_type].name}")

    def start_stream(self, camera_type: CameraType) -> bool:
        """Start a specific camera stream"""
        if camera_type in self.camera_streams:
            return self.camera_streams[camera_type].start()
        return False

    def stop_stream(self, camera_type: CameraType) -> bool:
        """Stop a specific camera stream"""
        if camera_type in self.camera_streams:
            return self.camera_streams[camera_type].stop()
        return False

    def get_image_provider(self, camera_type: CameraType) -> Optional[ImageProvider]:
        """Get image provider for a specific camera"""
        if camera_type in self.camera_streams:
            return self.camera_streams[camera_type].image_provider
        return None

    def enable_configurable_stream(self, port: int = None):
        """Enable and configure the configurable camera stream"""
        if port:
            self.camera_configs[CameraType.CONFIGURABLE].port = port
            
        self.camera_configs[CameraType.CONFIGURABLE].enabled = True
        
        # Create stream if it doesn't exist
        if CameraType.CONFIGURABLE not in self.camera_streams:
            try:
                config = self.camera_configs[CameraType.CONFIGURABLE]
                stream = CameraStream(config)
                stream.set_sample_callback(self._on_camera_frame)
                self.camera_streams[CameraType.CONFIGURABLE] = stream
                print(f"Enabled configurable stream on port {config.port}")
                return True
            except Exception as e:
                print(f"Failed to enable configurable stream: {e}")
                return False
        return True

    def disable_configurable_stream(self):
        """Disable the configurable camera stream"""
        if CameraType.CONFIGURABLE in self.camera_streams:
            self.camera_streams[CameraType.CONFIGURABLE].cleanup()
            del self.camera_streams[CameraType.CONFIGURABLE]
            
        self.camera_configs[CameraType.CONFIGURABLE].enabled = False
        print("Disabled configurable stream")

    def get_stream_status(self) -> Dict[str, bool]:
        """Get status of all streams"""
        status = {}
        for camera_type, stream in self.camera_streams.items():
            status[camera_type.value] = stream.is_running()
        return status

    def cleanup(self):
        """Clean up all streams and resources"""
        print("Cleaning up video streams...")
        for stream in self.camera_streams.values():
            stream.cleanup()
        self.camera_streams.clear()

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

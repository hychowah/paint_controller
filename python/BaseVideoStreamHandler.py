from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst

front_port = "5002"
rear_port = "5003"

class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(640, 480, QImage.Format_RGB888)

    def requestImage(self, id, size, requestedSize):
        return self.image

class BaseVideoStreamHandler(QObject):

    baseFrontFrameReady = Signal()
    baseRearFrameReady = Signal()

    def __init__(self):
        super().__init__()

        self.front_image_provider = ImageProvider()
        self.rear_image_provider = ImageProvider()

        self.front_pipeline = Gst.parse_launch(
            "udpsrc port=" + front_port + " caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=fsink"
        )
        self.front_sink = self.front_pipeline.get_by_name('fsink')
        self.front_sink.set_property('emit-signals', True)
        self.front_sink.connect('new-sample', self.on_new_front_sample)
        self.front_pipeline.set_state(Gst.State.PLAYING)

        self.rear_pipeline = Gst.parse_launch(
            "udpsrc port=" + rear_port + " caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=rsink"
        )
        self.rear_sink = self.rear_pipeline.get_by_name('rsink')
        self.rear_sink.set_property('emit-signals', True)
        self.rear_sink.connect('new-sample', self.on_new_back_sample)
        self.rear_pipeline.set_state(Gst.State.PLAYING)

    def handle_sample(self, sink, cam):
        sample = sink.emit('pull-sample')
        buffer = sample.get_buffer()
        caps = sample.get_caps()
        
        structure = caps.get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')
        
        _, map_info = buffer.map(Gst.MapFlags.READ)
        
        # Ensure the data is in the correct format (RGB)
        data = map_info.data
        
        # Create QImage directly from the buffer data
        ef_image = QImage(data, width, height, width * 3, QImage.Format_RGB888)

        if cam == 'front':
            self.front_image_provider.image = ef_image.copy()
        else:
            self.rear_image_provider.image = ef_image.copy()

        buffer.unmap(map_info)

        if cam == 'front':
            self.baseFrontFrameReady.emit()
        else:
            self.baseRearFrameReady.emit()

        return Gst.FlowReturn.OK

    def on_new_front_sample(self, sink):
        return self.handle_sample(sink, 'front')

    def on_new_back_sample(self, sink):
        return self.handle_sample(sink, 'rear')
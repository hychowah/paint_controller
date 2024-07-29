#!/usr/bin/env python3

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QResource, QThread
from PySide6.QtGui import QGuiApplication, QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, QQmlContext, qmlRegisterType
from PySide6.QtWidgets import QApplication, QWidget, QMainWindow
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQuick import QQuickPaintedItem, QQuickImageProvider
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget

import sys
import os
import numpy as np
import rclpy
import random
from rclpy.node import Node
import time
from cv_bridge import CvBridge
import cv2
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import LaserScan
from towngas_interfaces.msg import WinchStatus, WheelStatus

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstApp', '1.0')
from gi.repository import Gst, GstApp


class ImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self.image = QImage(640, 480, QImage.Format_RGB888)

    def requestImage(self, id, size, requestedSize):
        return self.image

class PaintController(Node, QObject):
    frame_ready = Signal()
    winchLengthChanged = Signal(str)
    winchSpeedChanged = Signal(str)
    winchCurrentChanged = Signal(str)
    winchAvailableChanged = Signal(bool)

    leftSpeedChanged = Signal(str)
    leftCurrentChanged = Signal(str)
    rightCurrentChanged = Signal(str)
    rightSpeedChanged = Signal(str)
    wheelAvailableChanged = Signal(bool)

    def __init__(self):
        Node.__init__(self, 'paint_controller')
        QObject.__init__(self)
        Gst.init(None)

        self.image_provider = ImageProvider()

        self.pipeline = Gst.parse_launch(
            "udpsrc port=5000 caps=\"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96\" ! rtph264depay ! avdec_h264 ! videoconvert ! video/x-raw,format=RGB ! appsink name=sink"
        )
        self.sink = self.pipeline.get_by_name('sink')
        self.sink.set_property('emit-signals', True)
        self.sink.connect('new-sample', self.on_new_sample)

        self.pipeline.set_state(Gst.State.PLAYING)

        qos_profile = rclpy.qos.QoSProfile(
            reliability=rclpy.qos.QoSReliabilityPolicy.BEST_EFFORT,
            history=rclpy.qos.QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        self.subscription = self.create_subscription(
            CompressedImage, 
            'camera/image/compressed', 
            self.camera_callback, 
            qos_profile)
        self.br = CvBridge()

        self.lidar_sub = self.create_subscription(
            LaserScan,
            'scan',
            self.lidar_sub_callback,
            1)
        self.lidar_sub  # prevent unused variable warning
        self.winch_sub = self.create_subscription(
            WinchStatus,
            'winchStatus',
            self.winch_sub_callback,
            1)
        self.winch_sub  # prevent unused variable warning
        self.wheel_sub = self.create_subscription(
            WheelStatus,
            'wheel_motor_status',
            self.wheel_sub_callback,
            1)
        self.wheel_sub

        self._left_wheel_speed = "0"
        self._right_wheel_speed = "0"
        self._left_wheel_current = "0"
        self._right_wheel_current = "0"
        self._wheel_available = False
        self.last_msg_time = time.time()

        self._winch_length = "0"
        self._winch_speed = "0"
        self._winch_curent = "0"
        self._winch_available = False

        self.scan_data = None

    @Property(bool, notify=winchAvailableChanged)
    def winch_available(self):
        return self._winch_available

    @winch_available.setter
    def winch_available(self, value):
        print(f"Setting winch available: {value}")
        if self._winch_available != value:
            self._winch_available = value
            self.winchAvailableChanged.emit(value)

    @Property(str, notify=winchLengthChanged)
    def winch_length(self):
        return self._winch_length

    @winch_length.setter
    def winch_length(self, value):
        if self._winch_length != value:
            self._winch_length = value
            self.winchLengthChanged.emit(value)

    @Property(str, notify=winchSpeedChanged)
    def winch_speed(self):
        return self._winch_speed

    @winch_speed.setter
    def winch_speed(self, value):
        if self._winch_speed != value:
            self._winch_speed = value
            self.winchSpeedChanged.emit(value)

    @Property(str, notify=winchCurrentChanged)
    def winch_current(self):
        return self._winch_curent
    
    @winch_current.setter
    def winch_current(self, value):
        if self._winch_curent != value:
            self._winch_curent = value
            self.winchCurrentChanged.emit(value)

    @Property(str, notify=leftSpeedChanged)
    def left_wheel_speed(self):
        return self._left_wheel_speed
    
    @left_wheel_speed.setter
    def left_wheel_speed(self, value):
        if self._left_wheel_speed != value:
            self._left_wheel_speed = value
            self.leftSpeedChanged.emit(value)

    @Property(str, notify=rightSpeedChanged)
    def right_wheel_speed(self):
        return self._right_wheel_speed
    
    @right_wheel_speed.setter
    def right_wheel_speed(self, value):
        if self._right_wheel_speed != value:
            self._right_wheel_speed = value
            self.rightSpeedChanged.emit(value)
    
    @Property(str, notify=leftCurrentChanged)
    def left_wheel_current(self):
        return self._left_wheel_current
    
    @left_wheel_current.setter
    def left_wheel_current(self, value):
        if self._left_wheel_current != value:
            self._left_wheel_current = value
            self.leftCurrentChanged.emit(value)

    @Property(str, notify=rightCurrentChanged)
    def right_wheel_current(self):
        return self._right_wheel_current
    
    @right_wheel_current.setter
    def right_wheel_current(self, value):
        if self._right_wheel_current != value:
            self._right_wheel_current = value
            self.rightCurrentChanged.emit(value)

    @Property(bool, notify=wheelAvailableChanged)  
    def wheel_available(self):
        return self._wheel_available
    
    @wheel_available.setter
    def wheel_available(self, value):
        if self._wheel_available != value:
            self._wheel_available = value
            self.wheelAvailableChanged.emit(value)
        
    @Slot(bool)
    def toggleSwitchChanged(self, checked):
        print(f"Toggle switch changed: {checked}")
        # Implement your function here that should be triggered by the toggle switch

    @Slot(np.ndarray)
    def update_frame(self, frame):
        print("Updating frame")
        frame_provider.update_frame(frame)
        self.video_output.update()

    def on_new_sample(self, sink):
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
        image = QImage(data, width, height, width * 3, QImage.Format_RGB888)
        
        self.image_provider.image = image.copy()  # Create a deep copy of the image
        buffer.unmap(map_info)
        
        self.frame_ready.emit()
        
        return Gst.FlowReturn.OK

    def lidar_sub_callback(self, msg):
        self.scan_data = msg
        self.get_logger().info(f'Received LiDAR Data: {len(msg.ranges)} ranges')
        print(f'Received LiDAR Data: {len(msg.ranges)} ranges')

    def winch_sub_callback(self, msg):
        print(f'Received Winch Status: {msg}')
        self.winch_length = str(msg.cable_length)
        self.winch_speed = str(msg.cable_speed)
        self.winch_current = str(msg.winch_torque)
        self.winch_available = bool(msg.available)
        print(f'Winch Length: {self.winch_length}, Winch Speed: {self.winch_speed}, Winch Available: {msg.available}')

    def wheel_sub_callback(self, msg):
        self.left_wheel_speed = f"{msg.left_wheel_speed:.2f}"
        self.right_wheel_speed = f"{msg.right_wheel_speed:.2f}"
        self.left_wheel_current = f"{msg.left_wheel_current:.2f}"
        self.right_wheel_current = f"{msg.right_wheel_current:.2f}"
        self.last_msg_time = time.time()

    def camera_callback(self, msg):
        # Decode the compressed image
        print("Received camera image")
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        self.new_frame.emit(frame)


    def update_plot(self):
        if time.time() - self.last_msg_time > 0.5:
            self.wheel_available = False
        else:
            self.wheel_available = True

        if self.scan_data is None:
            return

        angles = np.arange(self.scan_data.angle_min, self.scan_data.angle_max, self.scan_data.angle_increment)
        if len(angles) != len(self.scan_data.ranges):
            print("Mismatch in angles and ranges length")
            return

        x = np.array(self.scan_data.ranges) * np.cos(angles)
        y = np.array(self.scan_data.ranges) * np.sin(angles)
        self.plot_item.set_plot_data(x, y)


class RosThread(QThread):
    def __init__(self, node):
        super().__init__()
        self.node = node

    def run(self):
        rclpy.spin(self.node)


def main(args=None):
    rclpy.init(args=args)
    app = QApplication(sys.argv) 

    paint_controller = PaintController()

    ros_thread = RosThread(paint_controller)
    ros_thread.start()

    engine = QQmlApplicationEngine()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    qml_path = os.path.join(current_dir, 'qml', 'MainWindow.qml')
    engine.addImageProvider("live", paint_controller.image_provider)
    
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        print("Failed to load QML file.")
        sys.exit(-1)

    root = engine.rootObjects()[0]
    print(f"Root object: {root}")

    stack_view = root.findChild(QObject, "stackView")
    if stack_view is None:
        print("Could not find stackView in QML")
        sys.exit(-1)

    print("Found stackView")

    page1 = stack_view.findChild(QObject, "page1Rect")
    if page1 is None:
        print("Could not find page1 in QML")
        sys.exit(-1)

    print("Found page1")

    engine.rootContext().setContextProperty("backend", paint_controller)
    engine.rootContext().setContextProperty("videoStreamer", paint_controller)

    timer = QTimer()
    timer.timeout.connect(paint_controller.update_plot)
    timer.start(100)  # update every 100 ms

    sys.exit(app.exec())


if __name__ == '__main__':
    main()

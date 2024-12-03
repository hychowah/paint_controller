#!/usr/bin/env python3

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from PySide6.QtGui import  QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import  QQuickImageProvider


import sys
import os
import signal
import subprocess
import numpy as np
import rclpy
import random
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
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
    winchTorqueChanged = Signal(str)
    winchTemperatureChanged = Signal(str)
    winchVoltageChanged = Signal(str)
    winchBrakeChanged = Signal(bool)


    leftSpeedChanged = Signal(str)
    leftCurrentChanged = Signal(str)
    rightCurrentChanged = Signal(str)
    rightSpeedChanged = Signal(str)
    wheelAvailableChanged = Signal(bool)

    new_scan_data = Signal(list, float, float, float, float)

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

        winch_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST
        )
        self.winch_sub = self.create_subscription(
            WinchStatus,
            'winch/status',  # Match the publisher's topic name
            self.winch_sub_callback,
            winch_qos  # Use same QoS profile as publisher
        )
        
        self.winch_sub  # prevent unused variable warning
        self.wheel_sub = self.create_subscription(
            WheelStatus,
            'wheel_motor_status',
            self.wheel_sub_callback,
            1)
        self.wheel_sub

        self.latest_scan = None

        self._left_wheel_speed = "0"
        self._right_wheel_speed = "0"
        self._left_wheel_current = "0"
        self._right_wheel_current = "0"
        self._wheel_available = False
        self.last_wheel_msg_time = time.time() - 2
        self.last_winch_msg_time = time.time() - 2

        self._winch_status = {}

        self.scan_data = None

    def update_status(self):
        if time.time() - self.last_wheel_msg_time > 1:
            self.wheel_available = False
        else:
            self.wheel_available = True

        if time.time() - self.last_winch_msg_time > 1:
            self.winch_available = False
        else:
            self.winch_available = True

    @Property(bool, notify=winchAvailableChanged)
    def winch_available(self):
        return self._winch_status.get('available', False)

    @winch_available.setter 
    def winch_available(self, value):
        if self._winch_status.get('available') != value:
            self._winch_status['available'] = value
            self.winchAvailableChanged.emit(value)

    @Property(str, notify=winchLengthChanged)
    def winch_length(self):
        return self._winch_status.get('cable_length', '0.00')

    @winch_length.setter
    def winch_length(self, value):
        if self._winch_status.get('cable_length') != value:
            self._winch_status['cable_length'] = value
            self.winchLengthChanged.emit(value)

    @Property(str, notify=winchSpeedChanged)
    def winch_speed(self):
        return self._winch_status.get('cable_speed', '0.00')

    @winch_speed.setter
    def winch_speed(self, value):
        if self._winch_status.get('cable_speed') != value:
            self._winch_status['cable_speed'] = value
            self.winchSpeedChanged.emit(value)

    @Property(str, notify=winchTorqueChanged)
    def winch_torque(self):
        return self._winch_status.get('winch_torque', '0.00')

    @winch_torque.setter
    def winch_torque(self, value):
        if self._winch_status.get('winch_torque') != value:
            self._winch_status['winch_torque'] = value
            self.winchTorqueChanged.emit(value)

    @Property(str, notify=winchTemperatureChanged)
    def winch_temperature(self):
        return self._winch_status.get('motor_temperature', '0.0')

    @winch_temperature.setter
    def winch_temperature(self, value):
        if self._winch_status.get('motor_temperature') != value:
            self._winch_status['motor_temperature'] = value
            self.winchTemperatureChanged.emit(value)

    @Property(str, notify=winchVoltageChanged)
    def winch_voltage(self):
        return self._winch_status.get('motor_voltage', '0.0')

    @winch_voltage.setter
    def winch_voltage(self, value):
        if self._winch_status.get('motor_voltage') != value:
            self._winch_status['motor_voltage'] = value
            self.winchVoltageChanged.emit(value)

    @Property(bool, notify=winchBrakeChanged)
    def winch_brake(self):
        return self._winch_status.get('motor_brake', False)

    @winch_brake.setter
    def winch_brake(self, value):
        if self._winch_status.get('motor_brake') != value:
            self._winch_status['motor_brake'] = value
            self.winchBrakeChanged.emit(value)

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

    @Slot()
    def update_plot(self):
        if self.latest_scan is None:
            return

        ranges = list(self.latest_scan.ranges)
        self.new_scan_data.emit(
            ranges,
            self.latest_scan.angle_min,
            self.latest_scan.angle_increment,
            self.latest_scan.range_min,
            self.latest_scan.range_max
        )

    @Slot(np.ndarray)
    def update_frame(self, frame):
        print("Updating frame")
        frame_provider.update_frame(frame)
        self.video_output.update()

    @Slot()
    def terminateNodes(self):
        print("Terminating nodes")
        try:
            home_dir = os.path.expanduser("~")
            script_path = os.path.join(home_dir, "stop_all_nodes.bash")
            subprocess.run(["bash", script_path])
        except subprocess.CalledProcessError as e:
            print(f"Error running stop_all_nodes.bash: {e}")

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
        self.latest_scan = msg

    def winch_sub_callback(self, msg):
        """Handle winch status messages"""
        try:
            # print(f"Received winch status message: {msg}")
            self._winch_status = {
                'cable_length': f"{msg.cable_length:.2f}",
                'cable_speed': f"{msg.cable_speed:.2f}",
                'winch_torque': f"{msg.winch_torque:.2f}",
                'motor_temperature': f"{msg.motor_temperature:.1f}",
                'motor_voltage': f"{msg.motor_voltage:.1f}",
                'motor_brake': msg.motor_brake,
                'available': msg.available
            }

            self.winchAvailableChanged.emit(msg.available)
            self.winchLengthChanged.emit(self._winch_status['cable_length'])
            self.winchSpeedChanged.emit(self._winch_status['cable_speed'])
            self.winchTorqueChanged.emit(self._winch_status['winch_torque'])
            self.winchTemperatureChanged.emit(self._winch_status['motor_temperature'])
            self.winchVoltageChanged.emit(self._winch_status['motor_voltage'])
            self.winchBrakeChanged.emit(msg.motor_brake)
        except Exception as e:
            self.get_logger().error(f'Error in winch status callback: {str(e)}')

    def wheel_sub_callback(self, msg):
        self.left_wheel_speed = f"{msg.left_wheel_speed:.2f}"
        self.right_wheel_speed = f"{msg.right_wheel_speed:.2f}"
        self.left_wheel_current = f"{msg.left_wheel_current:.2f}"
        self.right_wheel_current = f"{msg.right_wheel_current:.2f}"
        self.last_msg_time = time.time()

    def camera_callback(self, msg):
        # Decode the compressed image
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        self.new_frame.emit(frame)


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

    engine.rootContext().setContextProperty("lidar_visualizer", paint_controller)
    engine.rootContext().setContextProperty("backend", paint_controller)
    engine.rootContext().setContextProperty("videoStreamer", paint_controller)

    timer = QTimer()
    timer.timeout.connect(paint_controller.update_status)
    timer.start(100)  # update every 100 ms


    sys.exit(app.exec())


if __name__ == '__main__':
    main()

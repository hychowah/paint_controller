#!/usr/bin/env python3

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QResource, QThread
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, QQmlContext, qmlRegisterType
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickPaintedItem

import sys
import os
import numpy as np
import rclpy
import random
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from towngas_interfaces.msg import WinchStatus, WheelStatus


class PlotItem(QQuickPaintedItem):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_data = None

    def set_plot_data(self, x, y):
        self.plot_data = (x, y)
        self.update()

    def paint(self, painter):
        if self.plot_data is None:
            return

        x, y = self.plot_data
        painter.setPen(Qt.black)
        for i in range(len(x)):
            painter.drawPoint(int(x[i]), int(y[i]))


class PaintController(Node, QObject):
    winchLengthChanged = Signal(str)
    winchSpeedChanged = Signal(str)
    winchCurrentChanged = Signal(str)
    leftSpeedChanged = Signal(str)
    leftCurrentChanged = Signal(str)
    rightCurrentChanged = Signal(str)
    rightSpeedChanged = Signal(str)
    winchAvailableChanged = Signal(bool)


    def __init__(self):
        Node.__init__(self, 'paint_controller')
        QObject.__init__(self)

        self.lidar_sub = self.create_subscription(
            LaserScan,
            'scan',
            self.lidar_sub_callback,
            10)
        self.lidar_sub  # prevent unused variable warning
        self.winch_sub = self.create_subscription(
            WinchStatus,
            'winchStatus',
            self.winch_sub_callback,
            10)
        self.winch_sub  # prevent unused variable warning
        self.wheel_sub = self.create_subscription(
            WheelStatus,
            'wheel_motor_status',
            self.wheel_sub_callback,
            10)
        self.wheel_sub
        self._left_wheel_speed = "0"
        self._right_wheel_speed = "0"
        self._left_wheel_current = "0"
        self._right_wheel_current = "0"

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
        print(f"Setting left wheel speed: {value}")
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
        

    @Slot(bool)
    def toggleSwitchChanged(self, checked):
        print(f"Toggle switch changed: {checked}")
        # Implement your function here that should be triggered by the toggle switch

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
        print(f'Received Wheel Status: {msg}')
        self.left_wheel_speed = f"{msg.left_wheel_speed:.2f}"
        self.right_wheel_speed = f"{msg.right_wheel_speed:.2f}"
        self.left_wheel_current = f"{msg.left_wheel_current:.2f}"
        self.right_wheel_current = f"{msg.right_wheel_current:.2f}"

    def update_plot(self):
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
    app = QApplication(sys.argv)  # Use QGuiApplication instead of QApplication

    qmlRegisterType(PlotItem, 'CustomComponents', 1, 0, 'PlotItem')

    paint_controller = PaintController()

    ros_thread = RosThread(paint_controller)
    ros_thread.start()

    engine = QQmlApplicationEngine()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    qml_path = os.path.join(current_dir, 'qml', 'MainWindow.qml')
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

    plot_container = page1.findChild(QObject, "plotContainer")
    if plot_container is None:
        print("Could not find plotContainer in QML")
        sys.exit(-1)

    print("Found plotContainer")

    plot_item = PlotItem()
    engine.rootContext().setContextProperty("plotItem", plot_item)
    engine.rootContext().setContextProperty("backend", paint_controller)

    timer = QTimer()
    timer.timeout.connect(paint_controller.update_plot)
    timer.start(100)  # update every 100 ms

    sys.exit(app.exec())

    ros_thread.quit()
    ros_thread.wait()
    paint_controller.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

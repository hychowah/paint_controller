import sys
import os
import rclpy
from rclpy.node import Node
from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt
from PySide6.QtGui import QGuiApplication, QPainter
from PySide6.QtQml import QQmlApplicationEngine, QQmlContext, qmlRegisterType
from PySide6.QtQuick import QQuickPaintedItem
from sensor_msgs.msg import LaserScan
import numpy as np

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

class PaintController(Node):
    def __init__(self, app):
        super().__init__('paint_controller')
        self.app = app
        self.subscription = self.create_subscription(
            LaserScan,
            'scan',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

        self.scan_data = None

        self.init_ui()

    def init_ui(self):
        self.engine = QQmlApplicationEngine()
        qml_path = os.path.join(os.path.dirname(__file__), 'MainWindow.qml')
        print(f"Loading QML file from: {qml_path}")
        self.engine.load(QUrl.fromLocalFile(qml_path))

        if not self.engine.rootObjects():
            print("Failed to load QML file.")
            sys.exit(-1)

        self.root = self.engine.rootObjects()[0]
        print(f"Root object: {self.root}")

        stack_view = self.root.findChild(QObject, "stackView")
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

        self.plot_item = PlotItem()
        self.engine.rootContext().setContextProperty("plotItem", self.plot_item)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # update every 100 ms

        self.engine.rootContext().setContextProperty("backend", self)

        sys.exit(self.app.exec())

    def listener_callback(self, msg):
        self.scan_data = msg
        self.get_logger().info(f'Received LiDAR Data: {len(msg.ranges)} ranges')
        print(f'Received LiDAR Data: {len(msg.ranges)} ranges')

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

    @Slot(bool)
    def toggle_program(self, is_on):
        self.program_running = is_on
        if is_on:
            self.get_logger().info('Program started')
            # Add your specific program start logic here
        else:
            self.get_logger().info('Program stopped')
            # Add your specific program stop logic here
        

def main(args=None):
    rclpy.init(args=args)
    app = QGuiApplication(sys.argv)  # Use QGuiApplication instead of QApplication
    
    qmlRegisterType(PlotItem, 'CustomComponents', 1, 0, 'PlotItem')

    paint_controller = PaintController(app)

    rclpy.spin(paint_controller)

    paint_controller.destroy_node()
    rclpy.shutdown()
    sys.exit(app.exec())  # Move the exec() call here

if __name__ == '__main__':
    main()

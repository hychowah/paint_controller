import sys
import rclpy
from rclpy.node import Node
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout
from PySide6.QtCore import QTimer
from sensor_msgs.msg import LaserScan
import numpy as np
from vispy import scene
from vispy.scene import visuals
from ui_main_window import Ui_MainWindow  # Import the generated UI module

class PaintController(Node):
    def __init__(self):
        super().__init__('paint_controller')
        self.subscription = self.create_subscription(
            LaserScan,
            'scan',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning
        
        self.scan_data = None
        
    def listener_callback(self, msg):
        self.scan_data = msg
        self.get_logger().info(f'Received LiDAR Data: {len(msg.ranges)} ranges')
        print(f'Received LiDAR Data: {len(msg.ranges)} ranges')

    def update_plot(self, scatter):
        if self.scan_data is None:
            return

        # Downsample data to reduce the number of points plotted
        downsample_rate = 10
        ranges = np.array(self.scan_data.ranges[::downsample_rate])
        num_ranges = len(ranges)
        
        angles = np.linspace(
            self.scan_data.angle_min,
            self.scan_data.angle_max,
            len(self.scan_data.ranges)
        )[::downsample_rate]

        x = ranges * np.cos(angles)
        y = ranges * np.sin(angles)
        scatter.set_data(np.c_[x, y])

class MainWindow(QMainWindow):
    def __init__(self, node):
        super().__init__()
        self.ui = Ui_MainWindow()  # Create an instance of the UI class
        self.ui.setupUi(self)  # Load the UI into the main window

        self.node = node

        # Set up the VisPy canvas in the widget designed in Qt Designer
        self.canvas = scene.SceneCanvas(keys='interactive', show=False)  # Set show=False to prevent it from opening in a new window
        self.view = self.canvas.central_widget.add_view()
        self.view.camera = 'panzoom'

        # Add a scatter plot to the view
        self.scatter = scene.visuals.Markers()
        self.view.add(self.scatter)
        self.scatter.set_gl_state('translucent', blend=True, depth_test=True)
        self.scatter.set_data(np.random.rand(100, 2), face_color='red', size=5)

        self.node.scatter = self.scatter

        # Add the VisPy canvas to the layout
        vispy_widget_layout = self.ui.vispy_widget_layout
        vispy_widget_layout.addWidget(self.canvas.native)  # Embed the VisPy canvas

        # Set up the timer for updating the plot
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.node.update_plot(self.scatter))
        self.timer.start(100)  # update every 100 ms

def main(args=None):
    rclpy.init(args=args)
    node = PaintController()
    
    app = QApplication(sys.argv)
    main_window = MainWindow(node)
    main_window.show()

    # Run the ROS2 event loop in a QTimer callback to ensure the GUI remains responsive
    def ros_spin():
        rclpy.spin_once(node, timeout_sec=0.1)

    spin_timer = QTimer()
    spin_timer.timeout.connect(ros_spin)
    spin_timer.start(10)  # Call ROS2 spin_once every 10ms

    app.exec()

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

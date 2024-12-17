#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
import rclpy
from rclpy.node import Node
from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterValue, ParameterType

class LidarControlGUI(Node):
    def __init__(self):
        super().__init__('lidar_control_gui')
        
        # Create the main window
        self.window = tk.Tk()
        self.window.title("Lidar Mount Angle Control")
        self.window.geometry("400x300")
        
        # Create and pack frames
        slider_frame = ttk.Frame(self.window, padding="10")
        slider_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create sliders
        self.roll_var = tk.DoubleVar(value=0.0)
        self.pitch_var = tk.DoubleVar(value=0.0)
        self.yaw_var = tk.DoubleVar(value=0.0)
        
        # Roll slider
        ttk.Label(slider_frame, text="Roll (degrees):").pack()
        roll_slider = ttk.Scale(slider_frame, from_=-180, to=180, 
                              variable=self.roll_var, orient=tk.HORIZONTAL,
                              command=lambda x: self.update_parameter('mount_roll'))
        roll_slider.pack(fill=tk.X, pady=5)
        
        # Pitch slider
        ttk.Label(slider_frame, text="Pitch (degrees):").pack()
        pitch_slider = ttk.Scale(slider_frame, from_=-180, to=180, 
                               variable=self.pitch_var, orient=tk.HORIZONTAL,
                               command=lambda x: self.update_parameter('mount_pitch'))
        pitch_slider.pack(fill=tk.X, pady=5)
        
        # Yaw slider
        ttk.Label(slider_frame, text="Yaw (degrees):").pack()
        yaw_slider = ttk.Scale(slider_frame, from_=-180, to=180, 
                             variable=self.yaw_var, orient=tk.HORIZONTAL,
                             command=lambda x: self.update_parameter('mount_yaw'))
        yaw_slider.pack(fill=tk.X, pady=5)
        
        # Status label
        self.status_label = ttk.Label(slider_frame, text="Ready")
        self.status_label.pack(pady=10)
        
        # Create service client
        self.param_client = self.create_client(
            SetParameters,
            '/unitre_lidar_ros2_node/set_parameters'
        )
    
    def update_parameter(self, param_name):
        if not self.param_client.wait_for_service(timeout_sec=1.0):
            self.status_label.config(text="Service not available")
            return
        
        # Get the corresponding value based on parameter name
        if param_name == 'mount_roll':
            value = self.roll_var.get()
        elif param_name == 'mount_pitch':
            value = self.pitch_var.get()
        else:  # mount_yaw
            value = self.yaw_var.get()
        
        # Create parameter message
        parameter = Parameter()
        parameter.name = param_name
        parameter.value.type = ParameterType.PARAMETER_DOUBLE
        parameter.value.double_value = value
        
        # Create request
        request = SetParameters.Request()
        request.parameters = [parameter]
        
        # Call service
        future = self.param_client.call_async(request)
        future.add_done_callback(
            lambda f: self.status_label.config(
                text=f"Updated {param_name} to {value:.2f} degrees"
            )
        )
    
    def run(self):
        self.window.mainloop()

def main():
    rclpy.init()
    gui = LidarControlGUI()
    
    # Use MultiThreadedExecutor to handle callbacks
    from rclpy.executors import MultiThreadedExecutor
    executor = MultiThreadedExecutor()
    executor.add_node(gui)
    
    # Run the GUI and ROS node
    import threading
    thread = threading.Thread(target=executor.spin, daemon=True)
    thread.start()
    
    try:
        gui.run()
    except KeyboardInterrupt:
        pass
    finally:
        gui.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
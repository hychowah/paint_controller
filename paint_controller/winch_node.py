#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Int32
from teknic_interfaces.msg import MotorStatus, TeknicStatus, MoveTeknicPos, MoveTeknicVel, TeknicCommand
from towngas_interfaces.msg import WinchStatus, MoveWinchLength
from time import time
import sys
import tkinter as tk
from tkinter import ttk
import threading

SPOOL_DIAMETER = 105.0  # mm
LENGTH_PER_REV = SPOOL_DIAMETER * 3.1415926  # mm
MOTOR_CNT_PER_REV = 6400.0
WINCH_GEAR_RATIO = 40.0
MOTOR_MAX_RPM = 1000.0

class WinchNode(Node):
    def __init__(self):
        super().__init__('winch_node')
        
        self.zero_length_cnt = 0
        self.current_motor_cnt = 0
        self.current_motor_vel = 0
        self.current_motor_torque = 0
        self.last_feedback_time = time()
        
        # Create subscriptions
        self.motor_feedback_sub = self.create_subscription(TeknicStatus, 'teknicStatus', self.motor_feedback_callback, 1)
        self.get_logger().info("Subscribed to teknicStatus topic")
        self.move_winch_length_sub = self.create_subscription(MoveWinchLength, 'moveWinchLength', self.move_winch_length_callback, 1)
        self.move_winch_speed_sub = self.create_subscription(Int32, 'move_winch_speed', self.move_winch_speed_callback, 1)

        # Create publisher for winch status
        self.winch_status_pub = self.create_publisher(WinchStatus, 'winchStatus', 1)

        # Create publishers for motor commands
        self.move_pos_pub = self.create_publisher(MoveTeknicPos, 'move_teknic_pos', 1)
        self.move_vel_pub = self.create_publisher(MoveTeknicVel, 'move_teknic_vel', 1)
        self.teknic_command_pub = self.create_publisher(TeknicCommand, 'teknic_command', 1)
        
        # Create a timer to check command timeout
        self.command_timeout_timer = self.create_timer(0.1, self.publish_status)

        # Initialize internal state
        self.current_motor_status = MotorStatus()
        self.winch_enabled = False
        self.available = False

    def motor_feedback_callback(self, msg: TeknicStatus):
        self.current_motor_cnt = msg.motors[0].pos
        self.current_motor_vel = msg.motors[0].speed
        self.current_motor_torque = msg.motors[0].torque
        self.winch_enabled = msg.motors[0].motor_enabled
        self.available = True
        self.last_feedback_time = time()  # Update last feedback time


    def publish_status(self):
        # Publish the current status of the winch
        status_msg = WinchStatus()
        status_msg.cable_length = int(self.get_length_mm())
        status_msg.cable_speed = int(self.get_cable_speed())
        status_msg.winch_torque = int(self.current_motor_torque)
        status_msg.available = self.winch_enabled
        status_msg.available = time() - self.last_feedback_time <= 0.5  # Check if feedback was received recently
        self.winch_status_pub.publish(status_msg)
        # self.get_logger().info(f'Published winch status: {status_msg}')

    def get_length_mm(self):
        return (self.current_motor_cnt - self.zero_length_cnt) * LENGTH_PER_REV / MOTOR_CNT_PER_REV / WINCH_GEAR_RATIO
    
    def get_cable_speed(self):
        return float(self.current_motor_vel) * LENGTH_PER_REV / MOTOR_CNT_PER_REV / WINCH_GEAR_RATIO
    
    def move_winch_length_callback(self, msg: MoveWinchLength):
        if not self.winch_enabled:
            self.get_logger().info('Winch is not enabled.')
            return
        target_length = msg.length_mm
        target_speed = msg.speed_mm_s
        target_cnt = target_length * MOTOR_CNT_PER_REV * WINCH_GEAR_RATIO / LENGTH_PER_REV 
        target_speed_rpm = target_speed * MOTOR_CNT_PER_REV * WINCH_GEAR_RATIO / LENGTH_PER_REV
        command_msg = MoveTeknicPos()
        command_msg.motor_cnt = [target_cnt]
        command_msg.motor_vel = [target_speed_rpm]
        command_msg.relative = True
        self.get_logger().info(f'Sent winch command: {command_msg}')
        self.move_pos_pub.publish(command_msg)

    def move_winch_speed_callback(self, msg: Int32):
        if not self.winch_enabled:
            self.get_logger().info('Winch is not enabled.')
            return
        target_speed = msg.data
        target_speed_rpm = int(target_speed * 60 * WINCH_GEAR_RATIO / LENGTH_PER_REV)
        if abs(target_speed_rpm) > MOTOR_MAX_RPM:
            target_speed_rpm = 0
            self.get_logger().info(f'target speed exceed the limit')
        command_msg = MoveTeknicVel()
        command_msg.motor_vel = [target_speed_rpm]
        self.get_logger().info(f'Sent winch command: {command_msg}')
        self.move_vel_pub.publish(command_msg)

    def enable_motor(self):
        command_msg = TeknicCommand()
        command_msg.motor_enable = True
        command_msg.e_stop = False
        self.teknic_command_pub.publish(command_msg)
        self.get_logger().info('Sent enable motor command.')

    def disable_motor(self):
        command_msg = TeknicCommand()
        command_msg.motor_enable = False
        command_msg.e_stop = False
        self.teknic_command_pub.publish(command_msg)
        self.get_logger().info('Sent disable motor command.')

    def set_zero(self):
        self.zero_length_cnt = self.current_motor_cnt
        self.get_logger().info('Set zero position.')

    def check_command_timeout(self):
        if time() - self.last_feedback_time > 0.5:
            self.current_motor_cnt = 0
            self.current_motor_vel = 0
            self.current_motor_torque = 0
            self.available = False
            self.get_logger().info('No motor feedback received for 0.5 seconds, resetting winch status.')
            self.publish_status()

class WinchGUI:
    def __init__(self, winch_node):
        self.winch_node = winch_node
        self.root = tk.Tk()
        self.root.title("Winch Control Panel")
        
        # Length control
        self.length_label = ttk.Label(self.root, text="Length (mm):")
        self.length_label.grid(row=0, column=0)
        self.length_entry = ttk.Entry(self.root)
        self.length_entry.grid(row=0, column=1)
        
        # Speed control
        self.speed_label = ttk.Label(self.root, text="Speed (mm/s):")
        self.speed_label.grid(row=1, column=0)
        self.speed_entry = ttk.Entry(self.root)
        self.speed_entry.grid(row=1, column=1)
        
        # Send length command button
        self.send_length_button = ttk.Button(self.root, text="Send Length Command", command=self.send_length_command)
        self.send_length_button.grid(row=2, column=0, columnspan=2)
        
        # Send speed command button
        self.send_speed_button = ttk.Button(self.root, text="Send Speed Command", command=self.send_speed_command)
        self.send_speed_button.grid(row=3, column=0, columnspan=2)
        
        # Set zero button
        self.set_zero_button = ttk.Button(self.root, text="Set Zero", command=self.winch_node.set_zero)
        self.set_zero_button.grid(row=4, column=0, columnspan=2)
        
        # Enable motor button
        self.enable_button = ttk.Button(self.root, text="Enable Motor", command=self.winch_node.enable_motor)
        self.enable_button.grid(row=5, column=0, columnspan=2)
        
        # Disable motor button
        self.disable_button = ttk.Button(self.root, text="Disable Motor", command=self.winch_node.disable_motor)
        self.disable_button.grid(row=6, column=0, columnspan=2)
        
        # Status display
        self.status_label = ttk.Label(self.root, text="Winch Status:")
        self.status_label.grid(row=7, column=0, columnspan=2)
        self.status_text = tk.Text(self.root, height=10, width=50)
        self.status_text.grid(row=8, column=0, columnspan=2)

        self.update_status()

    def send_length_command(self):
        if not self.winch_node.winch_enabled:
            self.winch_node.logger.info("Winch is not enabled.")
            return
        try:
            length = int(self.length_entry.get())
            speed = int(self.speed_entry.get())
            msg = MoveWinchLength()
            msg.length_mm = length
            msg.speed_mm_s = speed
            self.winch_node.move_winch_length_callback(msg)
        except ValueError:
            print("Invalid input")

    def send_speed_command(self):
        if not self.winch_node.winch_enabled:
            self.winch_node.logger.info("Winch is not enabled.")
            return
        try:
            speed_mm_s = int(self.speed_entry.get())
            target_rpm = int(speed_mm_s * WINCH_GEAR_RATIO * 60 / LENGTH_PER_REV)
            msg = MoveTeknicVel()
            msg.motor_vel = [target_rpm]
            self.winch_node.move_vel_pub.publish(msg)
            print(f'Sent speed command: {target_rpm}')
        except ValueError:
            print("Invalid input")
    
    def update_status(self):
        self.status_text.delete(1.0, tk.END)
        status = (
            f"Length: {self.winch_node.get_length_mm()} mm\n"
            f"Speed: {self.winch_node.get_cable_speed()} mm/s\n"
            f"Torque: {self.winch_node.current_motor_torque} Nm\n"
            f"Enabled: {self.winch_node.winch_enabled}\n"
            f"Available: {self.winch_node.available}\n"
        )
        self.status_text.insert(tk.END, status)
        self.root.after(1000, self.update_status)  # Update every 1000 milliseconds (1 second)

    def run(self):
        self.update_status()  # Start the status update loop
        self.root.mainloop()
        

def main(args=None):
    rclpy.init(args=args)
    node = WinchNode()

    def ros_spin():
        rclpy.spin(node)

    ros_thread = threading.Thread(target=ros_spin)
    ros_thread.start()

    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        gui = WinchGUI(node)
        gui.run()

    # Wait for the ROS thread to finish before exiting
    ros_thread.join()
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
    

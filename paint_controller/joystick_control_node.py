#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from towngas_interfaces.msg import MoveWheelSpeeds, DisableWheelMotor  # Replace 'towngas_interfaces' with your package name where the messages are defined
import time
import evdev
from evdev import InputDevice, ecodes, list_devices
from std_msgs.msg import Int32
import threading
from teknic_interfaces.msg import TeknicCommand

SPEED_LIMIT = 15

ZERO_ZONE = 1300

class JoystickControlNode(Node):
    def __init__(self):
        super().__init__('joystick_control_node')
        self.disable_motor_pub = self.create_publisher(DisableWheelMotor, 'disable_wheel_motor', 1)
        self.wheel_speeds_pub = self.create_publisher(MoveWheelSpeeds, 'move_wheel_speeds', 1)
        self.winch_speed_pub = self.create_publisher(Int32, 'move_winch_speed', 1)
        self.teknic_command_pub = self.create_publisher(TeknicCommand, 'teknic_command', 1)
        
        self.joystick = None
        self.joystick_thread = None
        self.motor_disabled = False  # Track motor state
        self.winch_motor_disabled = False  # Track winch motor state

        # Initial motor enabling
        self.publish_disable_motor(False)
        self.publish_disable_winch_motor(False)

        # Start the joystick reading thread
        self.joystick_thread = threading.Thread(target=self.joystick_loop)
        self.joystick_thread.daemon = True
        self.joystick_thread.start()

        # Create a timer to publish wheel speeds at 20 Hz
        self.timer = self.create_timer(0.05, self.publish_wheel_speeds)

        # Initialize joystick values
        self.values = {'ABS_X': 0, 'ABS_Y': 0, 'ABS_RX': 0, 'ABS_RY': 0}
        self.last_values = {'ABS_X': 0, 'ABS_Y': 0, 'ABS_RX': 0, 'ABS_RY': 0}
        self.threshold = 150  # Adjust the threshold as needed

    def publish_disable_motor(self, disable):
        msg = DisableWheelMotor()
        msg.disable = bool(disable)
        self.disable_motor_pub.publish(msg)
        self.get_logger().info(f'Published disable_motor with disable={disable}')

    def publish_disable_winch_motor(self, disable):
        msg = TeknicCommand()
        msg.motor_enable = not bool(disable)
        msg.e_stop = False
        self.teknic_command_pub.publish(msg)
        state = "disabled" if disable else "enabled"
        self.get_logger().info(f'Winch motor {state}')

    def publish_wheel_speeds(self):
        if not self.motor_disabled and self.is_significant_change('ABS_X', 'ABS_Y'):
            right_speed = float(self.calculate_left_wheel_speed())
            left_speed = float(self.calculate_right_wheel_speed())
            msg = MoveWheelSpeeds()
            msg.left_wheel_speed = left_speed
            msg.right_wheel_speed = right_speed
            self.wheel_speeds_pub.publish(msg)
            self.get_logger().info(f'Published wheel_speeds with left_wheel_speed={left_speed} right_wheel_speed={right_speed}')
            self.update_last_values('ABS_X', 'ABS_Y')

        if not self.winch_motor_disabled and self.is_significant_change('ABS_RX', 'ABS_RY'):
            winch_speed = int(self.calculate_winch_speed())
            msg = Int32()
            msg.data = winch_speed
            self.winch_speed_pub.publish(msg)
            self.get_logger().info(f'Published winch speed: {winch_speed}')
            self.update_last_values('ABS_RX', 'ABS_RY')

    def cubic_map(self, value, max_input, max_output):
        # Normalize the value to the range [-1, 1]
        normalized_value = value / max_input
        # Preserve the sign and apply cubic mapping
        mapped_value = (abs(normalized_value) ** 3) * (1 if normalized_value >= 0 else -1)
        # Map to the output range
        return mapped_value * max_output
    
    def linear_map(self, value, max_input, max_output):
        # Normalize the value to the range [-1, 1]
        normalized_value = value / max_input
        # Map to the output range
        return normalized_value * max_output

    def calculate_left_wheel_speed(self):
        if self.is_in_zero_zone(self.values['ABS_Y']):
            return 0.0
        base_speed = self.linear_map(self.values['ABS_Y'], 32767.0, SPEED_LIMIT)
        differential = 1.0 + (abs(self.values['ABS_X']) / 32767.0) * 1.5

        if abs(base_speed) < 1.5:
            base_speed = 0.0
            return base_speed

        if self.values['ABS_Y'] > 0:
            if self.values['ABS_X'] < 0:
                return base_speed
            else:
                return base_speed * differential
        elif self.values['ABS_Y'] < 0:
            if self.values['ABS_X'] < 0:
                return base_speed 
            else:
                return base_speed * differential
        else:
            return 0.0

    def calculate_right_wheel_speed(self):
        if self.is_in_zero_zone(self.values['ABS_Y']): 
            return 0.0

        base_speed = self.linear_map(self.values['ABS_Y'], 32767.0, SPEED_LIMIT)
        differential = 1.0 + (abs(self.values['ABS_X']) / 32767.0)
        if abs(base_speed) < 1.5:
            base_speed = 0.0
            return base_speed
        if self.values['ABS_Y'] > 0:
            if self.values['ABS_X'] < 0:
                return base_speed * differential
            else:
                return base_speed 
        elif self.values['ABS_Y'] < 0:
            if self.values['ABS_X'] < 0:
                return base_speed * differential
            else:
                return base_speed
        else:
            return 0.0
        

    def calculate_winch_speed(self):
        if self.is_in_zero_zone(self.values['ABS_RY']):
            return 0.0
        else:
            return self.cubic_map(self.values['ABS_RY'], 32767.0, 100.0)  # Adjust max_output as needed

    def is_in_zero_zone(self, value):
        return (abs(value) < ZERO_ZONE);

    def find_joystick(self):
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if 'Steam Deck' in device.name:
                return device
        return None

    def joystick_loop(self):
        self.joystick = self.find_joystick()
        if not self.joystick:
            self.get_logger().error('Joystick not found')
            return

        self.get_logger().info(f'Joystick device: {self.joystick.name}')
        for event in self.joystick.read_loop():
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    self.values['ABS_X'] = event.value
                elif event.code == ecodes.ABS_Y:
                    self.values['ABS_Y'] = event.value
                elif event.code == ecodes.ABS_RX:
                    self.values['ABS_RX'] = event.value
                elif event.code == ecodes.ABS_RY:
                    self.values['ABS_RY'] = event.value
            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TL and event.value == 1:
                self.toggle_motor_state()
            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TR and event.value == 1:
                self.toggle_winch_motor_state()

    def toggle_motor_state(self):
        self.motor_disabled = not self.motor_disabled
        self.publish_disable_motor(self.motor_disabled)
        state = "disabled" if self.motor_disabled else "enabled"
        self.get_logger().info(f'Motor {state} due to BTN_TL press')

    def toggle_winch_motor_state(self):
        self.winch_motor_disabled = not self.winch_motor_disabled
        self.publish_disable_winch_motor(self.winch_motor_disabled)
        state = "disabled" if self.winch_motor_disabled else "enabled"
        self.get_logger().info(f'Winch motor {state} due to BTN_TR press')

    def is_significant_change(self, *axes):
        return any(abs(self.values[axis] - self.last_values[axis]) > self.threshold for axis in axes)

    def update_last_values(self, *axes):
        for axis in axes:
            self.last_values[axis] = self.values[axis]

def main(args=None):
    rclpy.init(args=args)
    node = JoystickControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

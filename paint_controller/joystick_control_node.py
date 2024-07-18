#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool
from towngas_interfaces.msg import WheelSpeeds  # Replace 'towngas_interfaces' with your package name where the WheelSpeeds.msg is defined
import evdev
from evdev import InputDevice, ecodes, list_devices
import threading

class JoystickControlNode(Node):
    def __init__(self):
        super().__init__('joystick_control_node')
        self.disable_motor_pub = self.create_publisher(Bool, 'disable_motor', 10)
        self.wheel_speeds_pub = self.create_publisher(WheelSpeeds, 'wheel_speeds', 10)
        self.joystick = None
        self.joystick_thread = None

        # Initial motor enabling
        self.publish_disable_motor(False)

        # Start the joystick reading thread
        self.joystick_thread = threading.Thread(target=self.joystick_loop)
        self.joystick_thread.daemon = True
        self.joystick_thread.start()

        # Create a timer to publish wheel speeds at 20 Hz
        self.timer = self.create_timer(0.1, self.publish_wheel_speeds)

        # Initialize joystick values
        self.values = {'ABS_X': 0, 'ABS_Y': 0, 'R2': 0}

    def publish_disable_motor(self, disable):
        msg = Bool()
        msg.data = disable
        self.disable_motor_pub.publish(msg)
        self.get_logger().info(f'Published disable_motor with disable={disable}')

    def publish_wheel_speeds(self):
        left_speed = float(self.calculate_left_wheel_speed())
        right_speed = float(self.calculate_right_wheel_speed())
        msg = WheelSpeeds()
        msg.left_wheel_speed = left_speed
        msg.right_wheel_speed = right_speed
        self.wheel_speeds_pub.publish(msg)
        self.get_logger().info(f'Published wheel_speeds with left_wheel_speed={left_speed} right_wheel_speed={right_speed}')

    def cubic_map(self, value, max_input, max_output):
        # Normalize the value to the range [-1, 1]
        normalized_value = value / max_input
        # Apply cubic mapping
        mapped_value = normalized_value ** 3
        # Map to the output range
        return mapped_value * max_output

    def calculate_left_wheel_speed(self):
        base_speed = self.cubic_map(self.values['R2'], 32767.0, 40.0)
        differential = 1.0 + abs(self.values['ABS_X']) * 0.3 / 32767.0
        if self.values['ABS_Y'] > 0:
            if self.values['ABS_X'] < 0:
                return base_speed * differential
            else:
                return base_speed
        elif self.values['ABS_Y'] < 0:
            if self.values['ABS_X'] < 0:
                return -base_speed * differential
            else:
                return -base_speed
        else:
            return 0

    def calculate_right_wheel_speed(self):
        base_speed = self.cubic_map(self.values['R2'], 32767.0, 40.0)
        differential = 1.0 + abs(self.values['ABS_X']) * 0.3 / 32767.0
        if self.values['ABS_Y'] > 10000:
            if self.values['ABS_X'] > 0:
                return base_speed * differential
            else:
                return base_speed
        elif self.values['ABS_Y'] < -10000:
            if self.values['ABS_X'] > 0:
                return -base_speed * differential
            else:
                return -base_speed
        else:
            return 0

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
                elif event.code == 20:  # Event code for R2
                    self.values['R2'] = event.value

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

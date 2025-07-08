from dataclasses import dataclass
from typing import Dict, Optional
from std_msgs.msg import Float32, Int32
from geometry_msgs.msg import Twist, Vector3
import time
from UIHeartbeatHandler import HeartbeatStatus

@dataclass
class ControlConfig:
    scale: float
    min_interval: float  # Minimum time between commands in seconds
    offset: float = 0
    min_value: float = float('-inf')
    max_value: float = float('inf')
    msg_type: type = Float32

class ControlProcessor:
    def __init__(self, robot_controller):
        self.robot = robot_controller
        self.last_command_times = {}
        self.last_message_time = 0
        self.message_interval = 0.2  \
        
        self.current_values = {
            'left_mode': '',
            'left_value': 0.0,
            'right_mode': '',
            'right_value': 0.0
        }
        
        # Control configurations
        self.controls = {
            "Winch Speed": ControlConfig(
                scale=55/32768,
                min_interval=0.1,  # 10Hz
            ),
            "Left Wheel Speed": ControlConfig(
                scale=6/32768,
                min_interval=0.1  # 10Hz
            ),
            "Right Wheel Speed": ControlConfig(
                scale=6/32768,
                min_interval=0.1  # 10Hz
            ),
            "EF arm": ControlConfig(
                scale=1000/32768,
                min_interval=0.1  # 10Hz
            ),
            "EF prop joint": ControlConfig(
                scale=60.0/32768.0,
                min_interval=0.1  # 20Hz
            ),
            "EF spray trigger": ControlConfig(
                scale=400/32768,
                min_interval=0.2,  # 5Hz
                offset=1000,
                min_value=1000,
                msg_type=Int32
            ),
            "EF top rail": ControlConfig(
                scale=1000/32768,
                min_interval=0.1  # 10Hz
            ),
            "EF prop pwm": ControlConfig(
                scale=600/32768,
                min_interval=0.1,  # 10Hz
                offset=1000,
                min_value=1000,
                msg_type=Int32
            ),
            "EF spray gimbal": ControlConfig(
                scale=100/32768,
                min_interval=0.2,  # 5Hz
                msg_type=Int32
            ),
            "EF Yaw Angle": ControlConfig(
                scale=0.6/32768,
                min_interval=0.1  # 10Hz
            ),
            "EF Force": ControlConfig(
                scale=1.6/32768,  # Maps full joystick range to -1 to 1
                min_interval=0.1  # 10Hz
            )
        }

    def _update_display(self):
        """Update the display with current control values at 5Hz"""
        if self._can_send_message():
            if self.robot.overlayController.get_left_selected_option() == "None":
                left_part = "None"
            else:
                left_mode = self.current_values['left_mode']
                left_value = self.current_values['left_value']
                
                # Add LOCKED indicator for Winch Speed when locked
                if left_mode == "Winch Speed" and self._is_winch_control_locked():
                    left_part = f"{left_mode} {left_value:.2f} (LOCKED)" if left_mode else "None"
                elif left_mode == "EF Force":
                    # left_value contains a tuple (Fx, Fy) for EF Force
                    if isinstance(left_value, tuple):
                        left_part = f"{left_mode} Fx:{left_value[0]:.2f} Fy:{left_value[1]:.2f}"
                    else:
                        left_part = f"{left_mode} {left_value:.2f}"
                else:
                    left_part = f"{left_mode} {left_value:.2f}" if left_mode else "None"

            if self.robot.overlayController.get_right_selected_option() == "None":
                right_part = "None"
            else:
                right_mode = self.current_values['right_mode']
                right_value = self.current_values['right_value']
                
                # Add LOCKED indicator for Winch Speed when locked
                if right_mode == "Winch Speed" and self._is_winch_control_locked():
                    right_part = f"{right_mode} {right_value:.2f} (LOCKED)" if right_mode else "None"
                elif right_mode == "EF Force":
                    # right_value contains a tuple (Fx, Fy) for EF Force
                    if isinstance(right_value, tuple):
                        right_part = f"{right_mode} Fx:{right_value[0]:.2f} Fy:{right_value[1]:.2f}"
                    else:
                        right_part = f"{right_mode} {right_value:.2f}"
                else:
                    right_part = f"{right_mode} {right_value:.2f}" if right_mode else "None"
                    
            message = f"LEFT: {left_part} | RIGHT: {right_part}"
            self.robot.display_message(message)

    def _can_send_message(self) -> bool:
        """Check if we should update the display"""
        current_time = time.monotonic()
        if current_time - self.last_message_time >= self.message_interval:
            self.last_message_time = current_time
            return True
        return False
    
    def _can_send_command(self, mode: str) -> bool:
        """Check if enough time has passed to send another command"""
        current_time = time.monotonic()
        last_time = self.last_command_times.get(mode, 0)
        config = self.controls.get(mode)
        
        if config and current_time - last_time >= config.min_interval:
            self.last_command_times[mode] = current_time
            return True
        return False

    def _process_joint_control(self, input_state: Dict, mode: str, stick: str):
        """Handle prop joint specific control"""
        config = self.controls[mode]
        command_angle = input_state[f'{stick}_stick']['x'] * config.scale
        msg = Float32(data=command_angle)
        neg_msg = Float32(data=-command_angle)
        self.robot.teensy_controller.prop_left_pwm_pub.publish(msg)
        self.robot.teensy_controller.prop_left_pwm_pub.publish(neg_msg)
        
        # Update current values
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = -command_angle
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = command_angle

    def _process_ef_force_control(self, input_state: Dict, mode: str, stick: str):
        """Handle EF Force specific control - reads both x and y axes"""
        config = self.controls[mode]
        
        # Read both x and y axes from the joystick
        x_input = input_state[f'{stick}_stick']['x']
        y_input = input_state[f'{stick}_stick']['y']
        
        # Map joystick input (-32768 to 32767) to force values (-1 to 1)
        Fx = x_input * config.scale
        Fy = y_input * config.scale
        
        # Update current values with both Fx and Fy
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = (Fx, Fy)
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = (Fx, Fy)
        
        self.robot.teensy_controller.set_ef_force(Fx, Fy)

    def _process_yaw_control(self, input_state: Dict, mode: str, stick: str):
        """Handle EF Yaw Angle specific control"""
        config = self.controls[mode]
        command_angle = - float(input_state[f'{stick}_stick']['x']) * config.scale + config.offset
        config.offset = command_angle
        self.robot.teensy_controller.setYawAngle(command_angle)

        # Update current values
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = command_angle
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = command_angle
            

    def _publish_value(self, value: float, publisher, config: ControlConfig):
        """Publish a value with proper typing"""
        if config.msg_type == Int32:
            value = int(value)
        msg = config.msg_type(data=value)
        publisher.publish(msg)

    def _process_standard_control(self, input_state: Dict, mode: str, stick: str):
        """Handle standard control modes"""
        config = self.controls[mode]
        value = input_state[f'{stick}_stick']['y'] * config.scale + config.offset
        
        if value < config.min_value:
            value = 0.0
            
        # Update current values
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = value
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = value

        # Special handling for Winch Speed
        if mode == "Winch Speed":
            try:
                if not self.robot.winch_controller.get_available():
                    print("Winch not available")
                    return
                
                if self.robot.winch_controller.get_motor_brake():
                    print("Winch motor brake is on")
                    return
                
                if self._is_winch_control_locked():
                    print("Winch control locked: Base or EF is in ONTASK state")
                    return
                
                print(f"Commanding winch speed: {value}")
                self.robot.winch_controller.command_speed(value)

            except Exception as e:
                print(f"Error commanding winch speed: {str(e)}")
            return
        

        if value >= config.min_value:
            # Map modes to their publishers
            publishers = {
                "EF arm": self.robot.teensy_controller.ef_move_arm_rail_speed_pub,
                "EF spray trigger": self.robot.teensy_controller.ef_spray_trigger_pub,
                "EF top rail": self.robot.teensy_controller.ef_move_top_rail_speed_pub,
                "EF prop pwm": [self.robot.teensy_controller.prop_left_pwm_pub, self.robot.teensy_controller.prop_right_pwm_pub],
                "EF spray gimbal": self.robot.teensy_controller.ef_spray_gimbal_speed_pub,
                "Left Wheel Speed": self.robot.wheel_controller._left_wheel_speed_pub,
                "Right Wheel Speed": self.robot.wheel_controller._right_wheel_speed_pub
            }
            
            if publisher := publishers.get(mode):
                if isinstance(publisher, list):
                    for pub in publisher:
                        self._publish_value(value, pub, config)
                else:
                    self._publish_value(value, publisher, config)

    def process_input(self, input_state: Dict):
        """Process all control inputs with rate limiting"""
        try:
            # Process left joystick
            left_mode = self.robot.overlayController.get_left_selected_option()
            if left_mode in self.controls and self._can_send_command(left_mode):
                if left_mode == "EF prop joint":
                    self._process_joint_control(input_state, left_mode, 'left')
                elif left_mode == "EF Yaw Angle":
                    self._process_yaw_control(input_state, left_mode, 'left')
                elif left_mode == "EF Force":
                    self._process_ef_force_control(input_state, left_mode, 'left')
                else:
                    self._process_standard_control(input_state, left_mode, 'left')
            

            # Process right joystick
            right_mode = self.robot.overlayController.get_right_selected_option()
            if right_mode in self.controls and self._can_send_command(right_mode):
                if right_mode == "EF prop joint":
                    self._process_joint_control(input_state, right_mode, 'right')
                elif right_mode == "EF Yaw Angle":
                    self._process_yaw_control(input_state, right_mode, 'right')
                elif right_mode == "EF Force":
                    self._process_ef_force_control(input_state, right_mode, 'right')
                else:
                    self._process_standard_control(input_state, right_mode, 'right')

            if left_mode != "EF Yaw Angle" and right_mode != "EF Yaw Angle":
                self.controls["EF Yaw Angle"].offset = float(self.robot.ui_data_model.teensy_imu_yaw) * 100
                # print("Resetting EF Yaw Angle offset to:", self.controls["EF Yaw Angle"].offset)

            # Update display at 5Hz
            self._update_display()

        except Exception as e:
            print(f"Error processing control input: {str(e)}")
            self.robot.display_message(f"Error processing control input: {str(e)}")


    def set_winch_speed_limit(self, limit):
        """Set the winch speed limit"""
        self.controls["Winch Speed"].scale = abs(limit) / 32768

    def _is_winch_control_locked(self) -> bool:
        """
        Check if winch control should be locked based on heartbeat status
        Returns:
            bool: True if winch control should be locked, False otherwise
        """
        # Get the current heartbeat status for base and EF
        base_status = self.robot.heartbeat_handler.get_base_status()
        ef_status = self.robot.heartbeat_handler.get_ef_status()
        
        # Check if either component is in ONTASK status (0x01)
        if base_status == HeartbeatStatus.ONTASK.value or ef_status == HeartbeatStatus.ONTASK.value:
            return True
            
        return False
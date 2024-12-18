from dataclasses import dataclass
from typing import Dict, Callable, List, Optional
from std_msgs.msg import Float32, Int32
import math

@dataclass
class JoystickConfig:
    scale_factor: float
    offset: float = 0
    min_value: float = float('-inf')
    max_value: float = float('inf')
    data_type: type = Float32
    use_x_axis: bool = False  # Whether to use x-axis instead of y-axis
    invert_secondary: bool = False  # For modes that need inverted secondary output

class ControlProcessor:
    def __init__(self):
        # Shared configuration for both joysticks
        self.control_configs = {
            "EF arm": JoystickConfig(scale_factor=1000/32768),
            "EF prop joint": JoystickConfig(
                scale_factor=60.0/32768.0,
                use_x_axis=True,
                invert_secondary=True
            ),
            "EF spray trigger": JoystickConfig(
                scale_factor=1000/32768,
                offset=1000,
                min_value=1000,
                data_type=Int32
            ),
            "Winch Speed": JoystickConfig(scale_factor=self.config.max_winch_speed/32768),
            "EF top rail": JoystickConfig(scale_factor=1000/32768),
            "EF prop pwm": JoystickConfig(
                scale_factor=600/32768,
                offset=1000,
                min_value=1000,
                data_type=Int32
            ),
            "EF spray gimbal": JoystickConfig(
                scale_factor=100/32768,
                data_type=Int32
            )
        }

        # Cache publishers
        self.publishers = {
            "EF arm": self.ef_move_arm_rail_speed_pub,
            "EF prop joint": [self.prop_left_joint_pub, self.prop_right_joint_pub],
            "EF spray trigger": self.ef_spray_trigger_pub,
            "EF top rail": self.ef_move_top_rail_speed_pub,
            "EF prop pwm": [self.prop_left_pwm_pub, self.prop_right_pwm_pub],
            "EF spray gimbal": self.ef_spray_gimbal_speed_pub
        }

    def _process_value(self, raw_value: float, config: JoystickConfig) -> float:
        """Process a raw joystick value according to the configuration"""
        value = raw_value * config.scale_factor + config.offset
        return max(min(value, config.max_value), config.min_value)

    def _publish_value(self, value: float, publisher, config: JoystickConfig):
        """Publish a value to one or multiple publishers"""
        msg = config.data_type(data=value if config.data_type == Float32 else int(value))
        if isinstance(publisher, list):
            for i, pub in enumerate(publisher):
                # If it's a secondary publisher and inversion is needed
                pub_value = -value if (i > 0 and config.invert_secondary) else value
                pub.publish(config.data_type(data=pub_value if config.data_type == Float32 else int(pub_value)))
        else:
            publisher.publish(msg)

    def _handle_joystick(self, stick_input: Dict, mode: str, stick_name: str) -> None:
        """Handle processing for a single joystick"""
        if config := self.control_configs.get(mode):
            # Special handling for winch
            if mode == "Winch Speed":
                if self.ui_data_model.winch_available and not self.ui_data_model.winch_brake:
                    value = self._process_value(stick_input['y'], config)
                    self.winch_controller.command_speed(value)
                    self.display_message(f"Sending Winch Speed: {value:.2f}")
                else:
                    self.display_message("Winch not available")
                return

            # Get the appropriate axis value
            axis_value = stick_input['x' if config.use_x_axis else 'y']
            value = self._process_value(axis_value, config)
            
            # Only publish if above minimum value
            if value >= config.min_value:
                self._publish_value(value, self.publishers[mode], config)
                
                # Don't spam messages for prop PWM
                if mode != "EF prop pwm":
                    self.display_message(f"Sending {mode} ({stick_name}): {value:.2f}")

    def _process_control_input(self, input_state: Dict):
        """Process control inputs and update UI accordingly"""
        try:
            # Process both joysticks with their selected modes
            left_mode = self.overlayController.get_left_selected_option()
            right_mode = self.overlayController.get_right_selected_option()
            
            self._handle_joystick(input_state['left_stick'], left_mode, "Left")
            self._handle_joystick(input_state['right_stick'], right_mode, "Right")

        except Exception as e:
            self.display_message(f"Error processing control input: {str(e)}")
from dataclasses import dataclass
from typing import Dict, Optional
from std_msgs.msg import Float32, Int32
from geometry_msgs.msg import Twist, Vector3
import time
from UIHeartbeatHandler import HeartbeatStatus
from PySide6.QtCore import QObject, Signal, Property

@dataclass
class ControlConfig:
    scale: float
    min_interval: float  # Minimum time between commands in seconds
    offset: float = 0
    min_value: float = float('-inf')
    max_value: float = float('inf')
    msg_type: type = Float32

class ControlProcessor(QObject):
    # Signals for control info changes
    left_control_mode_changed = Signal(str)
    left_control_value_changed = Signal(str)
    right_control_mode_changed = Signal(str)
    right_control_value_changed = Signal(str)
    def __init__(self, robot_controller):
        super().__init__()
        self.robot = robot_controller
        self.last_command_times = {}
        self.last_message_time = 0
        
        # Initialize control info properties
        self._left_control_mode = "None"
        self._left_control_value = ""
        self._right_control_mode = "None"
        self._right_control_value = ""
        
        # Valve turn deadzone tracking
        self.valve_turn_in_deadzone = False
        self.valve_turn_deadzone_start_time = 0
        self.valve_turn_should_send = True
        
        # Arm rail speed deadzone tracking
        self.arm_rail_speed_in_deadzone = False
        self.arm_rail_speed_deadzone_start_time = 0
        self.arm_rail_speed_should_send = True
        
        # ===== CONFIGURATION CONSTANTS =====
        
        # Display and messaging
        self.MESSAGE_UPDATE_INTERVAL = 0.2  # seconds, 5Hz display update rate
        
        # Track control parameters
        self.TRACK_MAX_SPEED = 25.0         # Maximum track speed
        self.TRACK_MIN_SPEED = 15.0         # Minimum speed to overcome friction
        self.TRACK_DEAD_ZONE = 0.05         # 5% joystick dead zone
        self.TRACK_FINE_CONTROL_THRESHOLD = 0.6  # 60% of joystick for fine control (10-30 speed)
        self.TRACK_FINE_CURVE_FACTOR = 2.0  # Exponential curve for fine control range
        self.TRACK_COARSE_CURVE_FACTOR = 0.8  # Exponential curve for coarse control range
        
        # Joystick input constants
        self.JOYSTICK_MAX_VALUE = 32768.0   # Maximum joystick input value
        
        # Control command intervals (Hz rates)
        self.WINCH_UPDATE_INTERVAL = 0.1    # 10Hz
        self.TRACK_UPDATE_INTERVAL = 0.1    # 10Hz  
        self.EF_ARM_UPDATE_INTERVAL = 0.1   # 10Hz
        self.EF_JOINT_UPDATE_INTERVAL = 0.1 # 10Hz
        self.EF_TRIGGER_UPDATE_INTERVAL = 0.2  # 5Hz
        self.EF_RAIL_UPDATE_INTERVAL = 0.1  # 10Hz
        self.EF_PWM_UPDATE_INTERVAL = 0.1   # 10Hz
        self.EF_GIMBAL_UPDATE_INTERVAL = 0.2  # 5Hz
        self.EF_YAW_UPDATE_INTERVAL = 0.1   # 10Hz
        self.EF_FORCE_UPDATE_INTERVAL = 0.1 # 10Hz
        self.VALVE_TURN_UPDATE_INTERVAL = 0.3  # 10Hz
        
        # Control scaling factors
        self.WINCH_SCALE = 55 / self.JOYSTICK_MAX_VALUE
        self.TRACK_SCALE = self.TRACK_MAX_SPEED / self.JOYSTICK_MAX_VALUE
        self.EF_ARM_SCALE = 300 / self.JOYSTICK_MAX_VALUE
        self.EF_JOINT_SCALE = 60.0 / self.JOYSTICK_MAX_VALUE
        self.EF_TRIGGER_SCALE = 400 / self.JOYSTICK_MAX_VALUE
        self.EF_RAIL_SCALE = 1000 / self.JOYSTICK_MAX_VALUE
        self.EF_PWM_SCALE = 600 / self.JOYSTICK_MAX_VALUE
        self.EF_GIMBAL_SCALE = 30 / self.JOYSTICK_MAX_VALUE
        self.EF_YAW_SCALE = 2 / self.JOYSTICK_MAX_VALUE
        self.EF_FORCE_SCALE = 1.6 / self.JOYSTICK_MAX_VALUE
        self.VALVE_TURN_SCALE = 6.0 / self.JOYSTICK_MAX_VALUE  # Maps 0-32768 to 0-6.0
        self.VALVE_TURN_DEADZONE = 0.05  # 5% deadzone threshold
        self.VALVE_TURN_DEADZONE_TIMEOUT = 2.0  # seconds
        self.ARM_RAIL_SPEED_SCALE = 50.0 / self.JOYSTICK_MAX_VALUE  # Maps 0-32768 to 0-50.0
        self.ARM_RAIL_SPEED_DEADZONE = 0.05  # 5% deadzone threshold
        self.ARM_RAIL_SPEED_DEADZONE_TIMEOUT = 2.0  # seconds
        
        # Control offsets and limits
        self.EF_TRIGGER_OFFSET = 1000
        self.EF_TRIGGER_MIN_VALUE = 1000
        self.EF_PWM_OFFSET = 1000
        self.EF_PWM_MIN_VALUE = 1000
        self.EF_YAW_IMU_SCALE = 100.0       # Scale factor for IMU yaw conversion
        
        # ===== END CONFIGURATION =====
        
        self.current_values = {
            'left_mode': '',
            'left_value': 0.0,
            'right_mode': '',
            'right_value': 0.0
        }
        
        # Control configurations
        self.controls = {
            "Winch Speed": ControlConfig(
                scale=self.WINCH_SCALE,
                min_interval=self.WINCH_UPDATE_INTERVAL,
            ),
            "Track Control Left": ControlConfig(
                scale=self.TRACK_SCALE,
                min_interval=self.TRACK_UPDATE_INTERVAL
            ),
            "Track Control Right": ControlConfig(
                scale=self.TRACK_SCALE,
                min_interval=self.TRACK_UPDATE_INTERVAL
            ),
            "EF arm": ControlConfig(
                scale=self.EF_ARM_SCALE,
                min_interval=self.EF_ARM_UPDATE_INTERVAL
            ),
            "EF prop joint": ControlConfig(
                scale=self.EF_JOINT_SCALE,
                min_interval=self.EF_JOINT_UPDATE_INTERVAL
            ),
            "EF spray trigger": ControlConfig(
                scale=self.EF_TRIGGER_SCALE,
                min_interval=self.EF_TRIGGER_UPDATE_INTERVAL,
                offset=self.EF_TRIGGER_OFFSET,
                min_value=self.EF_TRIGGER_MIN_VALUE,
                msg_type=Int32
            ),
            "EF top rail": ControlConfig(
                scale=self.EF_RAIL_SCALE,
                min_interval=self.EF_RAIL_UPDATE_INTERVAL
            ),
            "EF prop pwm": ControlConfig(
                scale=self.EF_PWM_SCALE,
                min_interval=self.EF_PWM_UPDATE_INTERVAL,
                offset=self.EF_PWM_OFFSET,
                min_value=self.EF_PWM_MIN_VALUE,
                msg_type=Int32
            ),
            "EF spray gimbal": ControlConfig(
                scale=self.EF_GIMBAL_SCALE,
                min_interval=self.EF_GIMBAL_UPDATE_INTERVAL,
                msg_type=Int32
            ),
            "EF Yaw Angle": ControlConfig(
                scale=self.EF_YAW_SCALE,
                min_interval=self.EF_YAW_UPDATE_INTERVAL
            ),
            "EF Force": ControlConfig(
                scale=self.EF_FORCE_SCALE,
                min_interval=self.EF_FORCE_UPDATE_INTERVAL
            ),
            "Valve Turn": ControlConfig(
                scale=self.VALVE_TURN_SCALE,
                min_interval=self.VALVE_TURN_UPDATE_INTERVAL
            ),
            "Arm Rail Speed": ControlConfig(
                scale=self.ARM_RAIL_SPEED_SCALE,
                min_interval=self.EF_RAIL_UPDATE_INTERVAL
            )
        }

    def _update_display(self):
        """Update the display with current control values at 5Hz"""
        if self._can_send_message():
            if self.robot.overlayController.get_left_selected_option() == "None":
                left_part = "None"
                left_mode = "None"
                left_value = ""
            else:
                left_mode = self.current_values['left_mode']
                left_value = self.current_values['left_value']
                
                # Add LOCKED indicator for Winch Speed when locked
                if left_mode == "Winch Speed" and self._is_winch_control_locked():
                    left_part = f"{left_mode} {left_value:.2f} (LOCKED)" if left_mode else "None"
                elif left_mode in ["Track Control Left", "Track Control Right"]:
                    # Track Control already returns a formatted string
                    left_part = f"{left_mode} {left_value}" if left_mode else "None"
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
                right_mode = "None"
                right_value = ""
            else:
                right_mode = self.current_values['right_mode']
                right_value = self.current_values['right_value']
                
                # Add LOCKED indicator for Winch Speed when locked
                if right_mode == "Winch Speed" and self._is_winch_control_locked():
                    right_part = f"{right_mode} {right_value:.2f} (LOCKED)" if right_mode else "None"
                elif right_mode in ["Track Control Left", "Track Control Right"]:
                    # Track Control already returns a formatted string
                    right_part = f"{right_mode} {right_value}" if right_mode else "None"
                elif right_mode == "EF Force":
                    # right_value contains a tuple (Fx, Fy) for EF Force
                    if isinstance(right_value, tuple):
                        right_part = f"{right_mode} Fx:{right_value[0]:.2f} Fy:{right_value[1]:.2f}"
                    else:
                        right_part = f"{right_mode} {right_value:.2f}"
                else:
                    right_part = f"{right_mode} {right_value:.2f}" if right_mode else "None"
                    
            message = f"LEFT: {left_part} | RIGHT: {right_part}"
            self.robot.display_message = message
            
            # Update control processor properties for overlay display
            self.left_control_mode = left_mode if left_mode else "None"
            self.left_control_value = str(left_value) if isinstance(left_value, str) else (
                f"L:{left_value:.1f}" if isinstance(left_value, (int, float)) else str(left_value)
            )
            self.right_control_mode = right_mode if right_mode else "None"
            self.right_control_value = str(right_value) if isinstance(right_value, str) else (
                f"R:{right_value:.1f}" if isinstance(right_value, (int, float)) else str(right_value)
            )

    def _can_send_message(self) -> bool:
        """Check if we should update the display"""
        current_time = time.monotonic()
        if current_time - self.last_message_time >= self.MESSAGE_UPDATE_INTERVAL:
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

    def _apply_nonlinear_curve(self, normalized_input: float) -> float:
        """Apply non-linear response curve optimized for track control with friction
        
        The curve is designed to provide:
        - Immediate start at min_speed when joystick leaves dead zone
        - Fine control in min_speed to max_speed range with emphasis on lower speeds
        
        Args:
            normalized_input: Input value normalized to -1.0 to 1.0 range
        
        Returns:
            Non-linear mapped output scaled between min_speed and max_speed
        """
        if normalized_input == 0:
            return 0
        
        # Preserve sign
        sign = 1 if normalized_input > 0 else -1
        abs_input = abs(normalized_input)
        
        # Apply dead zone
        if abs_input <= self.TRACK_DEAD_ZONE:
            return 0
        
        # Normalize input after dead zone
        normalized_active = (abs_input - self.TRACK_DEAD_ZONE) / (1.0 - self.TRACK_DEAD_ZONE)
        
        # Two-stage curve for fine control in different ranges
        if normalized_active <= self.TRACK_FINE_CONTROL_THRESHOLD:
            # First portion for fine control with high precision
            curve_output = pow(normalized_active / self.TRACK_FINE_CONTROL_THRESHOLD, self.TRACK_FINE_CURVE_FACTOR) * 0.5
        else:
            # Last portion for reaching full speed
            remaining_input = (normalized_active - self.TRACK_FINE_CONTROL_THRESHOLD) / (1.0 - self.TRACK_FINE_CONTROL_THRESHOLD)
            remaining_output = pow(remaining_input, self.TRACK_COARSE_CURVE_FACTOR) * 0.5
            curve_output = 0.5 + remaining_output
        
        # Scale to actual speed range: min_speed to max_speed
        speed_range = self.TRACK_MAX_SPEED - self.TRACK_MIN_SPEED
        speed_output = self.TRACK_MIN_SPEED + (curve_output * speed_range)
        
        return sign * speed_output

    def _process_track_control(self, input_state: Dict, mode: str, stick: str):
        """Handle Track Control using two joysticks (Independent tank drive)
        "Track Control Left": Controls left track speed
        "Track Control Right": Controls right track speed
        
        Each option independently controls its corresponding track with smooth
        non-linear response optimized for friction characteristics.
        """
        config = self.controls[mode]
        
        # Get joystick Y-axis input (raw values from -32768 to 32767)
        track_input = input_state[f'{stick}_stick']['y']  # Y-axis for track speed
        
        # Normalize input to -1.0 to 1.0 range for curve application
        track_normalized = track_input / self.JOYSTICK_MAX_VALUE
        
        # Apply non-linear curve optimized for friction characteristics
        track_curved = self._apply_nonlinear_curve(track_normalized)
        
        # Use curved input directly as track speed
        track_speed = track_curved
        
        # Clamp value to configured max speed range
        track_speed = max(-self.TRACK_MAX_SPEED, min(self.TRACK_MAX_SPEED, track_speed))
        
        # Determine which track to control based on mode
        is_left_track = "Left" in mode
        
        # Command the appropriate track
        try:
            if is_left_track:
                self.current_values['left_mode'] = mode
                self.current_values['left_value'] = f"L:{track_speed:.1f}"
                self.robot.wheel_controller.command_left_wheel_speed(track_speed)
            else:
                self.current_values['right_mode'] = mode
                self.current_values['right_value'] = f"R:{track_speed:.1f}"
                self.robot.wheel_controller.command_right_wheel_speed(track_speed)
        except Exception as e:
            print(f"Error commanding track control ({mode}): {str(e)}")

    def _process_joint_control(self, input_state: Dict, mode: str, stick: str):
        """Handle prop joint specific control"""
        config = self.controls[mode]
        command_angle = input_state[f'{stick}_stick']['x'] * config.scale
        msg = Float32(data=command_angle)
        neg_msg = Float32(data=-command_angle)
        self.robot.teensy_controller.prop_left_joint_pub.publish(msg)
        self.robot.teensy_controller.prop_right_joint_pub.publish(neg_msg)
        
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

        # hardcode x to 0 for now
        Fx = 0.0
        
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

    def _process_valve_turn(self, input_state: Dict):
        """Handle valve turn control using right analog trigger
        
        Maps the right trigger (0-32767) to valve turn range (0.0-6.0)
        Stops sending commands after 2 seconds in deadzone until trigger moves beyond deadzone
        """
        # Get right trigger value (0-32767)
        right_trigger = input_state.get('triggers', {}).get('right', 0)
        
        # Map trigger value to valve turn range (0.0-6.0)
        valve_turn_value = right_trigger * self.VALVE_TURN_SCALE
        
        # Clamp to the valid range [0.0, 6.0]
        valve_turn_value = max(0.0, min(6.0, valve_turn_value))
        
        # Normalize to 0-1 range for deadzone check
        normalized_value = valve_turn_value / 6.0
        
        current_time = time.monotonic()
        
        # Check if we're in deadzone
        if normalized_value <= self.VALVE_TURN_DEADZONE:
            if not self.valve_turn_in_deadzone:
                # Just entered deadzone
                self.valve_turn_in_deadzone = True
                self.valve_turn_deadzone_start_time = current_time
                self.valve_turn_should_send = True
            else:
                # Already in deadzone - check if timeout has elapsed
                if current_time - self.valve_turn_deadzone_start_time >= self.VALVE_TURN_DEADZONE_TIMEOUT:
                    self.valve_turn_should_send = False
        else:
            # Outside deadzone - reset and allow sending
            self.valve_turn_in_deadzone = False
            self.valve_turn_should_send = True
        
        # Only send command if we should send
        if self.valve_turn_should_send:
            try:
                self.robot.teensy_controller.setValveTurn(valve_turn_value)
                # print(f"Commanding valve turn: {valve_turn_value}")
            except Exception as e:
                print(f"Error commanding valve turn: {str(e)}")
    
    def _process_arm_rail_speed(self, input_state: Dict):
        """Handle arm rail speed control using left analog trigger
        
        Maps the left trigger (0-32767) to arm rail speed range (0.0-50.0)
        Stops sending commands after 2 seconds in deadzone until trigger moves beyond deadzone
        """
        # Get left trigger value (0-32767)
        left_trigger = input_state.get('triggers', {}).get('left', 0)
        
        # Map trigger value to arm rail speed range (0.0-50.0)
        arm_rail_speed_value = left_trigger * self.ARM_RAIL_SPEED_SCALE
        
        # Clamp to the valid range [0.0, 50.0]
        arm_rail_speed_value = max(0.0, min(50.0, arm_rail_speed_value))
        
        # Normalize to 0-1 range for deadzone check
        normalized_value = arm_rail_speed_value / 50.0
        
        current_time = time.monotonic()
        
        # Check if we're in deadzone
        if normalized_value <= self.ARM_RAIL_SPEED_DEADZONE:
            if not self.arm_rail_speed_in_deadzone:
                # Just entered deadzone
                self.arm_rail_speed_in_deadzone = True
                self.arm_rail_speed_deadzone_start_time = current_time
                self.arm_rail_speed_should_send = True
            else:
                # Already in deadzone - check if timeout has elapsed
                if current_time - self.arm_rail_speed_deadzone_start_time >= self.ARM_RAIL_SPEED_DEADZONE_TIMEOUT:
                    self.arm_rail_speed_should_send = False
        else:
            # Outside deadzone - reset and allow sending
            self.arm_rail_speed_in_deadzone = False
            self.arm_rail_speed_should_send = True
        
        # Only send command if we should send
        if self.arm_rail_speed_should_send:
            try:
                self.robot.teensy_controller.setArmRailSpeed(arm_rail_speed_value)
                # print(f"Commanding arm rail speed: {arm_rail_speed_value}")
            except Exception as e:
                print(f"Error commanding arm rail speed: {str(e)}")

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
                if left_mode in ["Track Control Left", "Track Control Right"]:
                    self._process_track_control(input_state, left_mode, 'left')
                elif left_mode == "EF prop joint":
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
                if right_mode in ["Track Control Left", "Track Control Right"]:
                    self._process_track_control(input_state, right_mode, 'right')
                elif right_mode == "EF prop joint":
                    self._process_joint_control(input_state, right_mode, 'right')
                elif right_mode == "EF Yaw Angle":
                    self._process_yaw_control(input_state, right_mode, 'right')
                elif right_mode == "EF Force":
                    self._process_ef_force_control(input_state, right_mode, 'right')
                else:
                    self._process_standard_control(input_state, right_mode, 'right')
            
            # Process right trigger for valve turn command (continuous mapping)
            if self._can_send_command("Valve Turn"):
                self._process_valve_turn(input_state)
            
            # Process left trigger for arm rail speed command (continuous mapping)
            if self._can_send_command("Arm Rail Speed"):
                self._process_arm_rail_speed(input_state)

            if left_mode != "EF Yaw Angle" and right_mode != "EF Yaw Angle":
                # Get IMU yaw from TeensyController instead of UIDataModel
                teensy_imu_yaw = self.robot.teensy_controller.get_status_value('imu_yaw') or 0.0
                self.controls["EF Yaw Angle"].offset = float(teensy_imu_yaw) * self.EF_YAW_IMU_SCALE
                # print("Resetting EF Yaw Angle offset to:", self.controls["EF Yaw Angle"].offset)

            # Update display at 5Hz
            self._update_display()

        except Exception as e:
            print(f"Error processing control input: {str(e)}")
            self.robot.display_message = f"Error processing control input: {str(e)}"


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

    # Properties for left control info
    @Property(str, notify=left_control_mode_changed)
    def left_control_mode(self) -> str:
        return self._left_control_mode
    
    @left_control_mode.setter
    def left_control_mode(self, mode: str) -> None:
        if self._left_control_mode != mode:
            self._left_control_mode = mode
            self.left_control_mode_changed.emit(mode)

    @Property(str, notify=left_control_value_changed)
    def left_control_value(self) -> str:
        return self._left_control_value
    
    @left_control_value.setter
    def left_control_value(self, value: str) -> None:
        if self._left_control_value != value:
            self._left_control_value = value
            self.left_control_value_changed.emit(value)

    # Properties for right control info
    @Property(str, notify=right_control_mode_changed)
    def right_control_mode(self) -> str:
        return self._right_control_mode
    
    @right_control_mode.setter
    def right_control_mode(self, mode: str) -> None:
        if self._right_control_mode != mode:
            self._right_control_mode = mode
            self.right_control_mode_changed.emit(mode)

    @Property(str, notify=right_control_value_changed)
    def right_control_value(self) -> str:
        return self._right_control_value
    
    @right_control_value.setter
    def right_control_value(self, value: str) -> None:
        if self._right_control_value != value:
            self._right_control_value = value
            self.right_control_value_changed.emit(value)
# pyright: reportRedeclaration=false
"""Continuous teleop owner (sticks / triggers) — not the discrete action gate.

This module owns **continuous** machine motion from operator axes:

- Entry: ``ControlProcessor.process_input`` (status timer in ``SignalWiring``, ~60 Hz).
- Does **not** call ``AdminActionGate``. Gate covers discrete ``*Actions`` / settings slots only.
- Teleop policy instead: per-mode rate limits, deadzone timeouts, winch ONTASK lock,
  winch stick-activation gate. Effector helpers: ``winch_teleop``, ``wheel_travel_teleop``.

Discrete buttons/admin: QML → ``*Actions`` → ``AdminActionGate`` → controllers
(see ``ARCHITECTURE.md`` §7). Shared hard stop: ``SafetyCoordinator.halt_all_effectors``.

Post-halt stick inhibit is product policy elsewhere — not implemented here (TD-046 residual).
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import TYPE_CHECKING, Any

from std_msgs.msg import Float32, Int32
from paint_controller.handlers import wheel_travel_teleop, winch_teleop
from paint_controller.utils.constants import JoystickControl
from paint_controller.utils.input import DeadzoneTracker
from PySide6.QtCore import QObject, Signal, Property

if TYPE_CHECKING:
    from paint_controller.controllers.esp32_valve import ESP32ValveController
    from paint_controller.controllers.teensy import TeensyController
    from paint_controller.controllers.wheel import WheelController
    from paint_controller.controllers.winch import WinchController
    from paint_controller.core.settings import SettingsManager
    from paint_controller.core.state_store import StateStore
    from paint_controller.handlers.heartbeat import UIHeartbeatHandler
    from paint_controller.models.joystick_selection import JoystickSelectionModel

logger = logging.getLogger(__name__)

ControlMessageType = type[Float32] | type[Int32]
DisplayValue = str | float | tuple[float, float]

@dataclass
class ControlConfig:
    scale: float
    min_interval: float  # Minimum time between commands in seconds
    offset: float = 0
    min_value: float = float('-inf')
    max_value: float = float('inf')
    msg_type: ControlMessageType = Float32
    bidirectional: bool = False  # True for controls that support negative values (e.g., winch speed)

class ControlProcessor(QObject):
    # Signals for control info changes
    left_control_mode_changed = Signal(str)
    left_control_value_changed = Signal(str)
    right_control_mode_changed = Signal(str)
    right_control_value_changed = Signal(str)
    left_control_mode_display_changed = Signal(str)
    right_control_mode_display_changed = Signal(str)

    def __init__(
        self,
        wheel: WheelController,
        winch: WinchController,
        teensy: TeensyController,
        esp32_valve: ESP32ValveController,
        selection_model: JoystickSelectionModel,
        heartbeat_handler: UIHeartbeatHandler,
        settings_manager: SettingsManager | None,
        state_store: StateStore,
    ) -> None:
        super().__init__()
        self._wheel = wheel
        self._winch = winch
        self._teensy = teensy
        self._esp32_valve = esp32_valve
        self._selection_model = selection_model
        self._heartbeat_handler = heartbeat_handler
        self._settings_manager = settings_manager
        self._state_store = state_store
        self._last_selection_pair = (
            self._selection_model.get_left_selected_option(),
            self._selection_model.get_right_selected_option(),
        )

        self.last_command_times: dict[str, float] = {}
        self.last_message_time = 0.0
        
        # Initialize control info properties
        self._left_control_mode = "None"
        self._left_control_value = ""
        self._right_control_mode = "None"
        self._right_control_value = ""
        self._left_control_mode_display = "None"
        self._right_control_mode_display = "None"

        # Deadzone trackers for controls that need timed suppression
        self._valve_turn_deadzone = DeadzoneTracker(timeout=2.0)
        self._arm_rail_speed_deadzone = DeadzoneTracker(timeout=2.0)
        self._winch_speed_deadzone = DeadzoneTracker(timeout=1.0)
        self.winch_speed_has_been_active = False  # Only send commands after joystick moves outside deadzone
        
        # Wheel travel position tracking (accumulated values, not sent until button press)
        self._left_wheel_travel_mm = 0.0
        self._right_wheel_travel_mm = 0.0
        
        self.current_values: dict[str, DisplayValue] = {
            'left_mode': '',
            'left_value': 0.0,
            'right_mode': '',
            'right_value': 0.0
        }
        
        self._setup_settings(settings_manager)
        self._setup_constants()
        self._setup_controls()

    def _setup_settings(self, settings_manager: SettingsManager | None) -> None:
        """Load settings from settings_manager and subscribe to changes."""
        self.MESSAGE_UPDATE_INTERVAL = 0.2  # seconds, 5Hz display update rate

        if settings_manager is not None:
            sm = settings_manager
            self.TRACK_MAX_SPEED = sm.get('track_max_speed') or 500.0
            self.TRACK_MIN_SPEED = sm.get('track_min_speed') or 50.0
            self._valve_turn_max = sm.get('valve_turn_max') or 20.0
            self._winch_max_speed_mmps = sm.get('winch_max_speed_mmps') or 400.0
            self._wheel_travel_max = sm.get('wheel_travel_max') or 500.0
            self._wheel_travel_rate = sm.get('wheel_travel_rate') or 100.0
            self._wheel_travel_rpm = sm.get('wheel_travel_rpm') or 200
            # Subscribe to settings changes
            sm.track_max_speed_changed.connect(self._on_track_max_speed_changed)
            sm.track_min_speed_changed.connect(self._on_track_min_speed_changed)
            sm.valve_turn_max_changed.connect(self._on_valve_turn_max_changed)
            sm.winch_max_speed_mmps_changed.connect(self._on_winch_max_speed_mmps_changed)
            sm.wheel_travel_max_changed.connect(self._on_wheel_travel_max_changed)
            sm.wheel_travel_rate_changed.connect(self._on_wheel_travel_rate_changed)
            sm.wheel_travel_rpm_changed.connect(self._on_wheel_travel_rpm_changed)
        else:
            self.TRACK_MAX_SPEED = 500.0
            self.TRACK_MIN_SPEED = 50.0
            self._valve_turn_max = 6.0
            self._winch_max_speed_mmps = 400.0
            self._wheel_travel_max = 500.0
            self._wheel_travel_rate = 100.0
            self._wheel_travel_rpm = 300

    def _setup_constants(self) -> None:
        """Initialize control constants and scaling factors."""
        self.JOYSTICK_MAX_VALUE = 32768.0

        # Track control
        self.TRACK_DEAD_ZONE = 0.05
        self.TRACK_FINE_CONTROL_THRESHOLD = 0.6
        self.TRACK_FINE_CURVE_FACTOR = 2.0
        self.TRACK_COARSE_CURVE_FACTOR = 0.8

        # Command update intervals (seconds)
        self.WINCH_UPDATE_INTERVAL = 0.1
        self.TRACK_UPDATE_INTERVAL = 0.1
        self.EF_ARM_UPDATE_INTERVAL = 0.1
        self.EF_JOINT_UPDATE_INTERVAL = 0.1
        self.EF_TRIGGER_UPDATE_INTERVAL = 0.2
        self.EF_RAIL_UPDATE_INTERVAL = 0.1
        self.EF_PWM_UPDATE_INTERVAL = 0.1
        self.EF_PITCH_UPDATE_INTERVAL = 0.2
        self.EF_YAW_UPDATE_INTERVAL = 0.1
        self.EF_FORCE_UPDATE_INTERVAL = 0.1
        self.VALVE_TURN_UPDATE_INTERVAL = 0.3
        self.WHEEL_TRAVEL_UPDATE_INTERVAL = 0.1

        # Control scaling factors
        self.WINCH_SCALE = self._winch_max_speed_mmps / self.JOYSTICK_MAX_VALUE
        self.TRACK_SCALE = self.TRACK_MAX_SPEED / self.JOYSTICK_MAX_VALUE
        self.EF_ARM_SCALE = 300 / self.JOYSTICK_MAX_VALUE
        self.EF_JOINT_SCALE = 60.0 / self.JOYSTICK_MAX_VALUE
        self.EF_TRIGGER_SCALE = 400 / self.JOYSTICK_MAX_VALUE
        self.EF_RAIL_SCALE = 1000 / self.JOYSTICK_MAX_VALUE
        self.EF_PWM_SCALE = 600 / self.JOYSTICK_MAX_VALUE
        self.EF_PITCH_SCALE = 30 / self.JOYSTICK_MAX_VALUE
        self.EF_YAW_SCALE = 2 / self.JOYSTICK_MAX_VALUE
        self.EF_FORCE_SCALE = 1.6 / self.JOYSTICK_MAX_VALUE
        self.VALVE_TURN_SCALE = self._valve_turn_max / self.JOYSTICK_MAX_VALUE
        self.ARM_RAIL_SPEED_SCALE = 50.0 / self.JOYSTICK_MAX_VALUE

        # Deadzone thresholds
        self.VALVE_TURN_DEADZONE = 0.05
        self.VALVE_TURN_DEADZONE_TIMEOUT = 2.0
        self.ARM_RAIL_SPEED_DEADZONE = 0.05
        self.ARM_RAIL_SPEED_DEADZONE_TIMEOUT = 2.0
        self.WINCH_SPEED_DEADZONE = 0.05
        self.WINCH_SPEED_DEADZONE_TIMEOUT = 1.0

        # EF offsets and limits
        self.EF_TRIGGER_OFFSET = 1000
        self.EF_TRIGGER_MIN_VALUE = 1000
        self.EF_PWM_OFFSET = 1000
        self.EF_PWM_MIN_VALUE = 1000
        self.EF_YAW_IMU_SCALE = 100.0

    def _setup_controls(self) -> None:
        """Initialize control configurations and handler dispatch table."""
        self.controls = {
            "Winch Speed": ControlConfig(
                scale=self.WINCH_SCALE,
                min_interval=self.WINCH_UPDATE_INTERVAL,
                min_value=-self._winch_max_speed_mmps,
                max_value=self._winch_max_speed_mmps,
                bidirectional=True
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
            "EF spray pitch": ControlConfig(
                scale=self.EF_PITCH_SCALE,
                min_interval=self.EF_PITCH_UPDATE_INTERVAL,
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
            ),
            "Wheel Travel Left": ControlConfig(
                scale=self._get_wheel_travel_scale(),
                min_interval=self.WHEEL_TRAVEL_UPDATE_INTERVAL,
                min_value=-self._wheel_travel_max,
                max_value=self._wheel_travel_max,
                bidirectional=True
            ),
            "Wheel Travel Right": ControlConfig(
                scale=self._get_wheel_travel_scale(),
                min_interval=self.WHEEL_TRAVEL_UPDATE_INTERVAL,
                min_value=-self._wheel_travel_max,
                max_value=self._wheel_travel_max,
                bidirectional=True
            )
        }
        
        # Control handler dispatch table
        # Maps control names to their specialized handler methods.
        # Controls not in this table use _process_standard_control as the default handler.
        self._control_handlers = {
            "Track Control Left": self._process_track_control,
            "Track Control Right": self._process_track_control,
            "EF prop joint": self._process_joint_control,
            "EF Yaw Angle": self._process_yaw_control,
            "EF Force": self._process_ef_force_control,
            "Winch Speed": self._process_winch_speed,
            "Wheel Travel Left": self._process_wheel_travel,
            "Wheel Travel Right": self._process_wheel_travel,
        }

    def _update_display(self):
        """Update the display with current control values at 5Hz"""
        if self._can_send_message():
            if self._selection_model.get_left_selected_option() == "None":
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
                elif left_mode in ["Wheel Travel Left", "Wheel Travel Right"]:
                    # Show wheel travel distance in mm
                    left_part = f"{left_mode} {left_value:.0f}mm"
                elif left_mode == "EF Force":
                    # left_value contains a tuple (Fx, Fy) for EF Force
                    if isinstance(left_value, tuple):
                        left_part = f"{left_mode} Fx:{left_value[0]:.2f} Fy:{left_value[1]:.2f}"
                    else:
                        left_part = f"{left_mode} {left_value:.2f}"
                else:
                    left_part = f"{left_mode} {left_value:.2f}" if left_mode else "None"

            if self._selection_model.get_right_selected_option() == "None":
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
                elif right_mode in ["Wheel Travel Left", "Wheel Travel Right"]:
                    # Show wheel travel distance in mm
                    right_part = f"{right_mode} {right_value:.0f}mm"
                elif right_mode == "EF Force":
                    # right_value contains a tuple (Fx, Fy) for EF Force
                    if isinstance(right_value, tuple):
                        right_part = f"{right_mode} Fx:{right_value[0]:.2f} Fy:{right_value[1]:.2f}"
                    else:
                        right_part = f"{right_mode} {right_value:.2f}"
                else:
                    right_part = f"{right_mode} {right_value:.2f}" if right_mode else "None"
                    
            message = f"LEFT: {left_part} | RIGHT: {right_part}"
            self._state_store.display_message = message
            
            # Update control processor properties for overlay display
            self.left_control_mode = left_mode if left_mode else "None"
            self.left_control_value = str(left_value) if isinstance(left_value, str) else (
                f"Fx:{left_value[0]:.1f} Fy:{left_value[1]:.1f}" if isinstance(left_value, tuple) else (
                    f"L:{left_value:.1f}" if isinstance(left_value, (int, float)) else str(left_value)
                )
            )
            self.right_control_mode = right_mode if right_mode else "None"
            self.right_control_value = str(right_value) if isinstance(right_value, str) else (
                f"Fx:{right_value[0]:.1f} Fy:{right_value[1]:.1f}" if isinstance(right_value, tuple) else (
                    f"R:{right_value:.1f}" if isinstance(right_value, (int, float)) else str(right_value)
                )
            )
            self.left_control_mode_display = self._selection_model.display_name_for_option(
                str(left_mode if left_mode else "None")
            )
            self.right_control_mode_display = self._selection_model.display_name_for_option(
                str(right_mode if right_mode else "None")
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

    def _process_track_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
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
                self._wheel.command_left_wheel_speed(track_speed)
            else:
                self.current_values['right_mode'] = mode
                self.current_values['right_value'] = f"R:{track_speed:.1f}"
                self._wheel.command_right_wheel_speed(track_speed)
        except Exception as e:
            logger.error("Error commanding track control (%s): %s", mode, e)

    def _process_joint_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        """Handle prop joint specific control"""
        config = self.controls[mode]
        command_angle = input_state[f'{stick}_stick']['x'] * config.scale
        msg = Float32(data=command_angle)
        neg_msg = Float32(data=-command_angle)
        self._teensy.prop_left_joint_pub.publish(msg)
        self._teensy.prop_right_joint_pub.publish(neg_msg)
        
        # Update current values
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = -command_angle
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = command_angle

    def _process_ef_force_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
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

        # # hardcode x to 0 for now
        # Fx = 0.0
        
        self._teensy.set_ef_force(Fx, Fy)

    def _process_yaw_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        """Handle EF Yaw Angle specific control"""
        config = self.controls[mode]
        command_angle = - float(input_state[f'{stick}_stick']['x']) * config.scale + config.offset
        config.offset = command_angle
        self._teensy.setYawAngle(command_angle)

        # Update current values
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = command_angle
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = command_angle
            

    def _publish_value(self, value: float, publisher: Any, config: ControlConfig) -> None:
        """Publish a value with proper typing"""
        if config.msg_type == Int32:
            value = int(value)
        msg = config.msg_type(data=value)
        publisher.publish(msg)

    def _process_valve_turn(self, input_state: dict[str, Any]) -> None:
        """Handle valve turn control using right analog trigger
        
        Maps the right trigger (0-32767) to valve turn range 
        Stops sending commands after 2 seconds in deadzone until trigger moves beyond deadzone
        """
        # Get right trigger value (0-32767)
        right_trigger = input_state.get('triggers', {}).get('right', 0)
        
        # Map trigger value to valve turn range (0.0-valve_turn_max)
        valve_turn_value = right_trigger * self.VALVE_TURN_SCALE
        
        # Clamp to the valid range [0.0, valve_turn_max]
        valve_turn_value = max(0.0, min(self._valve_turn_max, valve_turn_value))
        
        # Normalize to 0-1 range for deadzone check
        normalized_value = valve_turn_value / self._valve_turn_max if self._valve_turn_max > 0 else 0
        
        # Update deadzone tracker
        should_send = self._valve_turn_deadzone.update(normalized_value, self.VALVE_TURN_DEADZONE)
        
        # Only send command if we should send
        if should_send:
            try:
                self._esp32_valve.setValveTurn(valve_turn_value)
                # print(f"Commanding valve turn: {valve_turn_value}")
            except Exception as e:
                logger.error("Error commanding valve turn: %s", e)
    
    def _process_arm_rail_speed(self, input_state: dict[str, Any]) -> None:
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
        
        # Update deadzone tracker
        should_send = self._arm_rail_speed_deadzone.update(normalized_value, self.ARM_RAIL_SPEED_DEADZONE)
        
        # Only send command if we should send
        if should_send:
            try:
                self._teensy.setArmRailSpeed(arm_rail_speed_value)
                # print(f"Commanding arm rail speed: {arm_rail_speed_value}")
            except Exception as e:
                logger.error("Error commanding arm rail speed: %s", e)

    def _process_winch_speed(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        """Handle winch speed control using joystick Y-axis (delegates to winch_teleop)."""
        self.winch_speed_has_been_active = winch_teleop.process_winch_speed(
            input_state,
            mode,
            stick,
            config=self.controls[mode],
            current_values=self.current_values,
            deadzone=self._winch_speed_deadzone,
            deadzone_threshold=self.WINCH_SPEED_DEADZONE,
            has_been_active=self.winch_speed_has_been_active,
            winch=self._winch,
            heartbeat_handler=self._heartbeat_handler,
        )

    def _process_wheel_travel(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        """Accumulate wheel travel from stick (command on A button via send_wheel_travel_command)."""
        self._left_wheel_travel_mm, self._right_wheel_travel_mm = (
            wheel_travel_teleop.accumulate_wheel_travel(
                input_state,
                mode,
                stick,
                left_mm=self._left_wheel_travel_mm,
                right_mm=self._right_wheel_travel_mm,
                scale=self._get_wheel_travel_scale(),
                travel_max=self._wheel_travel_max,
                current_values=self.current_values,
            )
        )
    def _process_standard_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        """Handle standard control modes"""
        config = self.controls[mode]
        value = input_state[f'{stick}_stick']['y'] * config.scale + config.offset
        
        # Apply value constraints based on control type
        if config.bidirectional:
            # Bidirectional controls (e.g., winch): clamp to [min_value, max_value]
            value = max(config.min_value, min(config.max_value, value))
        elif value < config.min_value:
            # Unidirectional controls (e.g., triggers): zero out if below threshold
            value = 0.0
            
        # Update current values
        if stick == 'left':
            self.current_values['left_mode'] = mode
            self.current_values['left_value'] = value
        else:
            self.current_values['right_mode'] = mode
            self.current_values['right_value'] = value

        if value >= config.min_value:
            # Map modes to their publishers
            publishers = {
                "EF arm": self._teensy.ef_move_arm_rail_speed_pub,
                "EF spray trigger": self._teensy.ef_spray_trigger_pub,
                "EF top rail": self._teensy.ef_move_top_rail_speed_pub,
                "EF prop pwm": [self._teensy.prop_left_pwm_pub, self._teensy.prop_right_pwm_pub],
                "EF spray pitch": self._teensy.ef_spray_pitch_speed_pub,
            }
            
            if publisher := publishers.get(mode):
                if isinstance(publisher, list):
                    for pub in publisher:
                        self._publish_value(value, pub, config)
                else:
                    self._publish_value(value, publisher, config)

    def _process_control_with_dispatch(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        """Process control input using dispatch table
        
        Args:
            input_state: Current input state
            mode: Control mode name
            stick: 'left' or 'right' joystick
        """
        # Get handler from dispatch table, defaulting to standard control
        handler = self._control_handlers.get(mode, self._process_standard_control)
        handler(input_state, mode, stick)

    def _sync_selection_state(self) -> tuple[str, str]:
        """Track joystick control selection changes and seed yaw target on selection updates."""
        left_mode = self._selection_model.get_left_selected_option()
        right_mode = self._selection_model.get_right_selected_option()
        selection_pair = (left_mode, right_mode)

        if selection_pair != self._last_selection_pair:
            if "EF Yaw Angle" in selection_pair:
                teensy_imu_yaw = self._teensy.get_status_value('imu_yaw') or 0.0
                self.controls["EF Yaw Angle"].offset = float(teensy_imu_yaw)
            self._last_selection_pair = selection_pair

        self.left_control_mode_display = self._selection_model.display_name_for_option(left_mode)
        self.right_control_mode_display = self._selection_model.display_name_for_option(right_mode)

        return selection_pair

    def process_input(self, input_state: dict[str, Any]) -> None:
        """Process all control inputs with rate limiting"""
        try:
            left_mode, right_mode = self._sync_selection_state()

            # Process left joystick
            if left_mode in self.controls and self._can_send_command(left_mode):
                self._process_control_with_dispatch(input_state, left_mode, 'left')

            # Process right joystick
            if right_mode in self.controls and self._can_send_command(right_mode):
                self._process_control_with_dispatch(input_state, right_mode, 'right')
            
            # Process right trigger for valve turn command (continuous mapping)
            if self._can_send_command("Valve Turn"):
                self._process_valve_turn(input_state)
            
            # Process left trigger for arm rail speed command (continuous mapping)
            if self._can_send_command("Arm Rail Speed"):
                self._process_arm_rail_speed(input_state)

            if left_mode != "EF Yaw Angle" and right_mode != "EF Yaw Angle":
                # Get IMU yaw from TeensyController instead of UIDataModel
                teensy_imu_yaw = self._teensy.get_status_value('imu_yaw') or 0.0
                self.controls["EF Yaw Angle"].offset = float(teensy_imu_yaw) * self.EF_YAW_IMU_SCALE
                # print("Resetting EF Yaw Angle offset to:", self.controls["EF Yaw Angle"].offset)

            # Update display at 5Hz
            self._update_display()

        except Exception as e:
            logger.error("Error processing control input: %s", e)
            self._state_store.display_message = f"Error processing control input: {str(e)}"


    def set_winch_speed_limit(self, limit: float) -> None:
        """Set the winch speed limit"""
        self.controls["Winch Speed"].scale = abs(limit) / 32768
    
    def reset_winch_activation(self):
        """Reset winch activation state - call when switching to EF mode to prevent spurious commands"""
        self.winch_speed_has_been_active = False
        winch_teleop.reset_winch_activation(self._winch_speed_deadzone)

    def _is_winch_control_locked(self) -> bool:
        """Check if winch control should be locked based on heartbeat status."""
        return winch_teleop.is_winch_control_locked(self._heartbeat_handler)
    
    # Settings change callbacks
    def _on_track_max_speed_changed(self, new_value: float):
        """Handle track_max_speed change from SettingsManager"""
        self.TRACK_MAX_SPEED = new_value
        self.TRACK_SCALE = self.TRACK_MAX_SPEED / self.JOYSTICK_MAX_VALUE
        # Update control config
        self.controls["Track Control Left"].scale = self.TRACK_SCALE
        self.controls["Track Control Right"].scale = self.TRACK_SCALE
        logger.info("Track max speed updated to: %s", new_value)
    
    def _on_track_min_speed_changed(self, new_value: float):
        """Handle track_min_speed change from SettingsManager"""
        self.TRACK_MIN_SPEED = new_value
        logger.info("Track min speed updated to: %s", new_value)
    
    def _on_valve_turn_max_changed(self, new_value: float):
        """Handle valve_turn_max change from SettingsManager"""
        self._valve_turn_max = new_value
        self.VALVE_TURN_SCALE = self._valve_turn_max / self.JOYSTICK_MAX_VALUE
        self.controls["Valve Turn"].scale = self.VALVE_TURN_SCALE
        logger.info("Valve turn max updated to: %s", new_value)
    
    def _on_winch_max_speed_mmps_changed(self, new_value: float):
        """Handle winch_max_speed_mmps change from SettingsManager"""
        self._winch_max_speed_mmps = new_value
        self.WINCH_SCALE = self._winch_max_speed_mmps / self.JOYSTICK_MAX_VALUE
        # Update control config - including min/max values for proper clamping
        self.controls["Winch Speed"].scale = self.WINCH_SCALE
        self.controls["Winch Speed"].min_value = -self._winch_max_speed_mmps
        self.controls["Winch Speed"].max_value = self._winch_max_speed_mmps
        logger.info("Winch max speed updated to: %s mm/s", new_value)

    def _get_wheel_travel_scale(self) -> float:
        """mm per update at full joystick deflection."""
        return wheel_travel_teleop.travel_scale(
            self._wheel_travel_rate,
            self.WHEEL_TRAVEL_UPDATE_INTERVAL,
            self.JOYSTICK_MAX_VALUE,
        )

    def _on_wheel_travel_max_changed(self, new_value: float):
        """Handle wheel_travel_max change from SettingsManager"""
        self._wheel_travel_max = new_value
        # Update control config min/max values for both Left and Right
        self.controls["Wheel Travel Left"].min_value = -self._wheel_travel_max
        self.controls["Wheel Travel Left"].max_value = self._wheel_travel_max
        self.controls["Wheel Travel Right"].min_value = -self._wheel_travel_max
        self.controls["Wheel Travel Right"].max_value = self._wheel_travel_max
        logger.info("Wheel travel max updated to: %s mm", new_value)

    def _on_wheel_travel_rate_changed(self, new_value: float):
        """Handle wheel_travel_rate change from SettingsManager"""
        self._wheel_travel_rate = new_value
        # Update control config scale for both Left and Right
        self.controls["Wheel Travel Left"].scale = self._get_wheel_travel_scale()
        self.controls["Wheel Travel Right"].scale = self._get_wheel_travel_scale()
        logger.info("Wheel travel rate updated to: %s mm/sec", new_value)

    def _on_wheel_travel_rpm_changed(self, new_value: int):
        """Handle wheel_travel_rpm change from SettingsManager"""
        self._wheel_travel_rpm = new_value
        logger.info("Wheel travel RPM updated to: %s", new_value)

    def send_wheel_travel_command(self):
        """Send accumulated wheel travel position command (A-button path from input handler)."""
        wheel_travel_teleop.send_wheel_travel_command(
            self._wheel,
            left_mm=self._left_wheel_travel_mm,
            right_mm=self._right_wheel_travel_mm,
            rpm=self._wheel_travel_rpm,
        )

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

    # Properties for compact control-mode display labels
    @Property(str, notify=left_control_mode_display_changed)
    def left_control_mode_display(self) -> str:
        return self._left_control_mode_display

    @left_control_mode_display.setter
    def left_control_mode_display(self, display: str) -> None:
        if self._left_control_mode_display != display:
            self._left_control_mode_display = display
            self.left_control_mode_display_changed.emit(display)

    @Property(str, notify=right_control_mode_display_changed)
    def right_control_mode_display(self) -> str:
        return self._right_control_mode_display

    @right_control_mode_display.setter
    def right_control_mode_display(self, display: str) -> None:
        if self._right_control_mode_display != display:
            self._right_control_mode_display = display
            self.right_control_mode_display_changed.emit(display)
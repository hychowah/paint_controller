"""Non-Qt continuous teleop motion core (TD-055 Phase 8).

Owns rate limits, control map mutation, device commands, and stick/trigger
dispatch. ``ControlProcessor`` is a thin Qt façade over this engine.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from paint_controller.handlers import wheel_travel_teleop, winch_teleop
from paint_controller.handlers.policy.teleop_control_map import (
    ControlConfig,
    TeleopScaleConstants,
    build_default_control_configs,
    scale_joystick_axis,
)
from paint_controller.ports.teensy import SupportsTeensyTeleop
from paint_controller.ports.valve import SupportsValveCommand
from paint_controller.ports.wheel import SupportsWheelTeleop
from paint_controller.ports.winch import SupportsWinchTeleop
from paint_controller.utils.input import DeadzoneTracker

logger = logging.getLogger(__name__)

DisplayValue = str | float | tuple[float, float]


class ContinuousTeleopEngine:
    """Deep continuous-motion owner — no QObject / no QML properties."""

    def __init__(
        self,
        wheel: SupportsWheelTeleop,
        winch: SupportsWinchTeleop,
        teensy: SupportsTeensyTeleop,
        esp32_valve: SupportsValveCommand,
        *,
        is_winch_locked: Callable[[], bool],
        track_max_speed: float = 500.0,
        track_min_speed: float = 50.0,
        valve_turn_max: float = 6.0,
        winch_max_speed_mmps: float = 400.0,
        wheel_travel_max: float = 500.0,
        wheel_travel_rate: float = 100.0,
        wheel_travel_rpm: int = 300,
    ) -> None:
        self._wheel = wheel
        self._winch = winch
        self._teensy = teensy
        self._esp32_valve = esp32_valve
        self._is_winch_locked = is_winch_locked

        self.last_command_times: dict[str, float] = {}
        self._valve_turn_deadzone = DeadzoneTracker(timeout=2.0)
        self._arm_rail_speed_deadzone = DeadzoneTracker(timeout=2.0)
        self._winch_speed_deadzone = DeadzoneTracker(timeout=1.0)
        self.winch_speed_has_been_active = False
        self._left_wheel_travel_mm = 0.0
        self._right_wheel_travel_mm = 0.0
        self.current_values: dict[str, DisplayValue] = {
            "left_mode": "",
            "left_value": 0.0,
            "right_mode": "",
            "right_value": 0.0,
        }
        self._last_selection_pair: tuple[str, str] = ("", "")

        self.TRACK_MAX_SPEED = track_max_speed
        self.TRACK_MIN_SPEED = track_min_speed
        self._valve_turn_max = valve_turn_max
        self._winch_max_speed_mmps = winch_max_speed_mmps
        self._wheel_travel_max = wheel_travel_max
        self._wheel_travel_rate = wheel_travel_rate
        self._wheel_travel_rpm = wheel_travel_rpm
        self._setup_constants()
        self._setup_controls()

    def _setup_constants(self) -> None:
        self.JOYSTICK_MAX_VALUE = 32768.0
        self.TRACK_DEAD_ZONE = 0.05
        self.TRACK_FINE_CONTROL_THRESHOLD = 0.6
        self.TRACK_FINE_CURVE_FACTOR = 2.0
        self.TRACK_COARSE_CURVE_FACTOR = 0.8
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
        self.VALVE_TURN_DEADZONE = 0.05
        self.ARM_RAIL_SPEED_DEADZONE = 0.05
        self.WINCH_SPEED_DEADZONE = 0.05
        self.EF_TRIGGER_OFFSET = 1000
        self.EF_TRIGGER_MIN_VALUE = 1000
        self.EF_PWM_OFFSET = 1000
        self.EF_PWM_MIN_VALUE = 1000
        self.EF_YAW_IMU_SCALE = 100.0

    def _setup_controls(self) -> None:
        self.controls = build_default_control_configs(
            TeleopScaleConstants(
                winch_scale=self.WINCH_SCALE,
                winch_update_interval=self.WINCH_UPDATE_INTERVAL,
                winch_max_speed_mmps=self._winch_max_speed_mmps,
                track_scale=self.TRACK_SCALE,
                track_update_interval=self.TRACK_UPDATE_INTERVAL,
                ef_arm_scale=self.EF_ARM_SCALE,
                ef_arm_update_interval=self.EF_ARM_UPDATE_INTERVAL,
                ef_joint_scale=self.EF_JOINT_SCALE,
                ef_joint_update_interval=self.EF_JOINT_UPDATE_INTERVAL,
                ef_trigger_scale=self.EF_TRIGGER_SCALE,
                ef_trigger_update_interval=self.EF_TRIGGER_UPDATE_INTERVAL,
                ef_trigger_offset=self.EF_TRIGGER_OFFSET,
                ef_trigger_min_value=self.EF_TRIGGER_MIN_VALUE,
                ef_rail_scale=self.EF_RAIL_SCALE,
                ef_rail_update_interval=self.EF_RAIL_UPDATE_INTERVAL,
                ef_pwm_scale=self.EF_PWM_SCALE,
                ef_pwm_update_interval=self.EF_PWM_UPDATE_INTERVAL,
                ef_pwm_offset=self.EF_PWM_OFFSET,
                ef_pwm_min_value=self.EF_PWM_MIN_VALUE,
                ef_pitch_scale=self.EF_PITCH_SCALE,
                ef_pitch_update_interval=self.EF_PITCH_UPDATE_INTERVAL,
                ef_yaw_scale=self.EF_YAW_SCALE,
                ef_yaw_update_interval=self.EF_YAW_UPDATE_INTERVAL,
                ef_force_scale=self.EF_FORCE_SCALE,
                ef_force_update_interval=self.EF_FORCE_UPDATE_INTERVAL,
                valve_turn_scale=self.VALVE_TURN_SCALE,
                valve_turn_update_interval=self.VALVE_TURN_UPDATE_INTERVAL,
                arm_rail_speed_scale=self.ARM_RAIL_SPEED_SCALE,
                wheel_travel_scale=self._get_wheel_travel_scale(),
                wheel_travel_update_interval=self.WHEEL_TRAVEL_UPDATE_INTERVAL,
                wheel_travel_max=self._wheel_travel_max,
            )
        )
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

    def _get_wheel_travel_scale(self) -> float:
        return wheel_travel_teleop.travel_scale(
            self._wheel_travel_rate,
            self.WHEEL_TRAVEL_UPDATE_INTERVAL,
            self.JOYSTICK_MAX_VALUE,
        )

    def _can_send_command(self, mode: str) -> bool:
        current_time = time.monotonic()
        last_time = self.last_command_times.get(mode, 0)
        config = self.controls.get(mode)
        if config and current_time - last_time >= config.min_interval:
            self.last_command_times[mode] = current_time
            return True
        return False

    def note_selection(self, left_mode: str, right_mode: str) -> None:
        pair = (left_mode, right_mode)
        if pair != self._last_selection_pair:
            if "EF Yaw Angle" in pair:
                teensy_imu_yaw = self._teensy.get_status_value("imu_yaw") or 0.0
                self.controls["EF Yaw Angle"].offset = float(teensy_imu_yaw)
            self._last_selection_pair = pair

    def tick(self, input_state: dict[str, Any], left_mode: str, right_mode: str) -> None:
        """Process one continuous-teleop frame (modes from selection model)."""
        self.note_selection(left_mode, right_mode)
        if left_mode in self.controls and self._can_send_command(left_mode):
            self._process_control_with_dispatch(input_state, left_mode, "left")
        if right_mode in self.controls and self._can_send_command(right_mode):
            self._process_control_with_dispatch(input_state, right_mode, "right")
        if self._can_send_command("Valve Turn"):
            self._process_valve_turn(input_state)
        if self._can_send_command("Arm Rail Speed"):
            self._process_arm_rail_speed(input_state)
        if left_mode != "EF Yaw Angle" and right_mode != "EF Yaw Angle":
            teensy_imu_yaw = self._teensy.get_status_value("imu_yaw") or 0.0
            self.controls["EF Yaw Angle"].offset = float(teensy_imu_yaw) * self.EF_YAW_IMU_SCALE

    def _process_control_with_dispatch(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        handler = self._control_handlers.get(mode, self._process_standard_control)
        handler(input_state, mode, stick)

    def _apply_nonlinear_curve(self, normalized_input: float) -> float:
        if normalized_input == 0:
            return 0
        sign = 1 if normalized_input > 0 else -1
        abs_input = abs(normalized_input)
        if abs_input <= self.TRACK_DEAD_ZONE:
            return 0
        normalized_active = (abs_input - self.TRACK_DEAD_ZONE) / (1.0 - self.TRACK_DEAD_ZONE)
        if normalized_active <= self.TRACK_FINE_CONTROL_THRESHOLD:
            curve_output = (
                pow(normalized_active / self.TRACK_FINE_CONTROL_THRESHOLD, self.TRACK_FINE_CURVE_FACTOR) * 0.5
            )
        else:
            remaining_input = (normalized_active - self.TRACK_FINE_CONTROL_THRESHOLD) / (
                1.0 - self.TRACK_FINE_CONTROL_THRESHOLD
            )
            remaining_output = pow(remaining_input, self.TRACK_COARSE_CURVE_FACTOR) * 0.5
            curve_output = 0.5 + remaining_output
        speed_range = self.TRACK_MAX_SPEED - self.TRACK_MIN_SPEED
        return sign * (self.TRACK_MIN_SPEED + (curve_output * speed_range))

    def _process_track_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        track_input = input_state[f"{stick}_stick"]["y"]
        track_normalized = track_input / self.JOYSTICK_MAX_VALUE
        track_speed = self._apply_nonlinear_curve(track_normalized)
        track_speed = max(-self.TRACK_MAX_SPEED, min(self.TRACK_MAX_SPEED, track_speed))
        is_left_track = "Left" in mode
        try:
            if is_left_track:
                self.current_values["left_mode"] = mode
                self.current_values["left_value"] = f"L:{track_speed:.1f}"
                self._wheel.command_left_wheel_speed(track_speed)
            else:
                self.current_values["right_mode"] = mode
                self.current_values["right_value"] = f"R:{track_speed:.1f}"
                self._wheel.command_right_wheel_speed(track_speed)
        except Exception as e:
            logger.error("Error commanding track control (%s): %s", mode, e)

    def _process_joint_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        config = self.controls[mode]
        command_angle = input_state[f"{stick}_stick"]["x"] * config.scale
        self._teensy.setLeftPropJoint(command_angle)
        self._teensy.setRightPropJoint(-command_angle)
        if stick == "left":
            self.current_values["left_mode"] = mode
            self.current_values["left_value"] = -command_angle
        else:
            self.current_values["right_mode"] = mode
            self.current_values["right_value"] = command_angle

    def _process_ef_force_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        config = self.controls[mode]
        Fx = input_state[f"{stick}_stick"]["x"] * config.scale
        Fy = input_state[f"{stick}_stick"]["y"] * config.scale
        if stick == "left":
            self.current_values["left_mode"] = mode
            self.current_values["left_value"] = (Fx, Fy)
        else:
            self.current_values["right_mode"] = mode
            self.current_values["right_value"] = (Fx, Fy)
        self._teensy.set_ef_force(Fx, Fy)

    def _process_yaw_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        config = self.controls[mode]
        command_angle = -float(input_state[f"{stick}_stick"]["x"]) * config.scale + config.offset
        config.offset = command_angle
        self._teensy.setYawAngle(command_angle)
        if stick == "left":
            self.current_values["left_mode"] = mode
            self.current_values["left_value"] = command_angle
        else:
            self.current_values["right_mode"] = mode
            self.current_values["right_value"] = command_angle

    def _process_valve_turn(self, input_state: dict[str, Any]) -> None:
        right_trigger = input_state.get("triggers", {}).get("right", 0)
        valve_turn_value = right_trigger * self.VALVE_TURN_SCALE
        valve_turn_value = max(0.0, min(self._valve_turn_max, valve_turn_value))
        normalized_value = valve_turn_value / self._valve_turn_max if self._valve_turn_max > 0 else 0
        should_send = self._valve_turn_deadzone.update(normalized_value, self.VALVE_TURN_DEADZONE)
        if should_send:
            try:
                self._esp32_valve.setValveTurn(valve_turn_value)
            except Exception as e:
                logger.error("Error commanding valve turn: %s", e)

    def _process_arm_rail_speed(self, input_state: dict[str, Any]) -> None:
        left_trigger = input_state.get("triggers", {}).get("left", 0)
        arm_rail_speed_value = left_trigger * self.ARM_RAIL_SPEED_SCALE
        arm_rail_speed_value = max(0.0, min(50.0, arm_rail_speed_value))
        normalized_value = arm_rail_speed_value / 50.0
        should_send = self._arm_rail_speed_deadzone.update(normalized_value, self.ARM_RAIL_SPEED_DEADZONE)
        if should_send:
            try:
                self._teensy.setArmRailSpeed(arm_rail_speed_value)
            except Exception as e:
                logger.error("Error commanding arm rail speed: %s", e)

    def _process_winch_speed(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        result = winch_teleop.process_winch_speed(
            input_state,
            mode,
            stick,
            config=self.controls[mode],
            deadzone=self._winch_speed_deadzone,
            deadzone_threshold=self.WINCH_SPEED_DEADZONE,
            has_been_active=self.winch_speed_has_been_active,
            winch=self._winch,
            is_locked=self._is_winch_locked,
        )
        self.winch_speed_has_been_active = result.has_been_active
        if stick == "left":
            self.current_values["left_mode"] = mode
            self.current_values["left_value"] = result.display_value
        else:
            self.current_values["right_mode"] = mode
            self.current_values["right_value"] = result.display_value

    def _process_wheel_travel(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        result = wheel_travel_teleop.accumulate_wheel_travel(
            input_state,
            mode,
            stick,
            left_mm=self._left_wheel_travel_mm,
            right_mm=self._right_wheel_travel_mm,
            scale=self._get_wheel_travel_scale(),
            travel_max=self._wheel_travel_max,
        )
        self._left_wheel_travel_mm = result.left_mm
        self._right_wheel_travel_mm = result.right_mm
        if stick == "left":
            self.current_values["left_mode"] = mode
            self.current_values["left_value"] = result.display_value
        else:
            self.current_values["right_mode"] = mode
            self.current_values["right_value"] = result.display_value

    def _process_standard_control(self, input_state: dict[str, Any], mode: str, stick: str) -> None:
        config = self.controls[mode]
        value = scale_joystick_axis(float(input_state[f"{stick}_stick"]["y"]), config, apply_offset=True)
        if stick == "left":
            self.current_values["left_mode"] = mode
            self.current_values["left_value"] = value
        else:
            self.current_values["right_mode"] = mode
            self.current_values["right_value"] = value
        if value >= config.min_value:
            if config.value_cast == "int":
                command: float | int = int(value)
            else:
                command = float(value)
            if mode == "EF arm":
                self._teensy.setArmRailSpeed(float(command))
            elif mode == "EF spray trigger":
                self._teensy.setSprayTrigger(int(command))
            elif mode == "EF top rail":
                self._teensy.setTopRailSpeed(float(command))
            elif mode == "EF prop pwm":
                pwm = int(command)
                self._teensy.setLeftPropPWM(pwm)
                self._teensy.setRightPropPWM(pwm)
            elif mode == "EF spray pitch":
                self._teensy.setSprayPitchSpeed(int(command))

    def send_wheel_travel_command(self) -> bool:
        return wheel_travel_teleop.send_wheel_travel_command(
            self._wheel,
            left_mm=self._left_wheel_travel_mm,
            right_mm=self._right_wheel_travel_mm,
            rpm=int(self._wheel_travel_rpm),
        )

    def reset_winch_activation(self) -> None:
        winch_teleop.reset_winch_activation(self._winch_speed_deadzone)
        self.winch_speed_has_been_active = False

    def set_winch_speed_limit(self, max_speed_mmps: float) -> None:
        self._winch_max_speed_mmps = max_speed_mmps
        self.WINCH_SCALE = self._winch_max_speed_mmps / self.JOYSTICK_MAX_VALUE
        self.controls["Winch Speed"].scale = self.WINCH_SCALE
        self.controls["Winch Speed"].min_value = -self._winch_max_speed_mmps
        self.controls["Winch Speed"].max_value = self._winch_max_speed_mmps

    def set_track_max_speed(self, value: float) -> None:
        self.TRACK_MAX_SPEED = value
        self.TRACK_SCALE = self.TRACK_MAX_SPEED / self.JOYSTICK_MAX_VALUE
        self.controls["Track Control Left"].scale = self.TRACK_SCALE
        self.controls["Track Control Right"].scale = self.TRACK_SCALE

    def set_track_min_speed(self, value: float) -> None:
        self.TRACK_MIN_SPEED = value

    def set_valve_turn_max(self, value: float) -> None:
        self._valve_turn_max = value
        self.VALVE_TURN_SCALE = self._valve_turn_max / self.JOYSTICK_MAX_VALUE
        self.controls["Valve Turn"].scale = self.VALVE_TURN_SCALE

    def set_wheel_travel_max(self, value: float) -> None:
        self._wheel_travel_max = value
        self.controls["Wheel Travel Left"].min_value = -value
        self.controls["Wheel Travel Left"].max_value = value
        self.controls["Wheel Travel Right"].min_value = -value
        self.controls["Wheel Travel Right"].max_value = value

    def set_wheel_travel_rate(self, value: float) -> None:
        self._wheel_travel_rate = value
        scale = self._get_wheel_travel_scale()
        self.controls["Wheel Travel Left"].scale = scale
        self.controls["Wheel Travel Right"].scale = scale

    def set_wheel_travel_rpm(self, value: int) -> None:
        self._wheel_travel_rpm = value

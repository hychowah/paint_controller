"""Pure teleop control-config tables (TD-055 Phase 3).

``ControlProcessor`` owns timers, display, and device calls; this module owns
the mode→scale/interval map so rules can be unit-tested without Qt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ValueCast = Literal["float", "int"]


@dataclass
class ControlConfig:
    scale: float
    min_interval: float  # Minimum time between commands in seconds
    offset: float = 0
    min_value: float = float("-inf")
    max_value: float = float("inf")
    value_cast: ValueCast = "float"
    bidirectional: bool = False  # True for controls that support negative values


@dataclass(frozen=True)
class TeleopScaleConstants:
    """Numeric scales / intervals used to build the default control map."""

    winch_scale: float
    winch_update_interval: float
    winch_max_speed_mmps: float
    track_scale: float
    track_update_interval: float
    ef_arm_scale: float
    ef_arm_update_interval: float
    ef_joint_scale: float
    ef_joint_update_interval: float
    ef_trigger_scale: float
    ef_trigger_update_interval: float
    ef_trigger_offset: float
    ef_trigger_min_value: float
    ef_rail_scale: float
    ef_rail_update_interval: float
    ef_pwm_scale: float
    ef_pwm_update_interval: float
    ef_pwm_offset: float
    ef_pwm_min_value: float
    ef_pitch_scale: float
    ef_pitch_update_interval: float
    ef_yaw_scale: float
    ef_yaw_update_interval: float
    ef_force_scale: float
    ef_force_update_interval: float
    valve_turn_scale: float
    valve_turn_update_interval: float
    arm_rail_speed_scale: float
    wheel_travel_scale: float
    wheel_travel_update_interval: float
    wheel_travel_max: float


def build_default_control_configs(constants: TeleopScaleConstants) -> dict[str, ControlConfig]:
    """Build the production mode→ControlConfig table from scale constants."""
    return {
        "Winch Speed": ControlConfig(
            scale=constants.winch_scale,
            min_interval=constants.winch_update_interval,
            min_value=-constants.winch_max_speed_mmps,
            max_value=constants.winch_max_speed_mmps,
            bidirectional=True,
        ),
        "Track Control Left": ControlConfig(
            scale=constants.track_scale, min_interval=constants.track_update_interval
        ),
        "Track Control Right": ControlConfig(
            scale=constants.track_scale, min_interval=constants.track_update_interval
        ),
        "EF arm": ControlConfig(scale=constants.ef_arm_scale, min_interval=constants.ef_arm_update_interval),
        "EF prop joint": ControlConfig(
            scale=constants.ef_joint_scale, min_interval=constants.ef_joint_update_interval
        ),
        "EF spray trigger": ControlConfig(
            scale=constants.ef_trigger_scale,
            min_interval=constants.ef_trigger_update_interval,
            offset=constants.ef_trigger_offset,
            min_value=constants.ef_trigger_min_value,
            value_cast="int",
        ),
        "EF top rail": ControlConfig(
            scale=constants.ef_rail_scale, min_interval=constants.ef_rail_update_interval
        ),
        "EF prop pwm": ControlConfig(
            scale=constants.ef_pwm_scale,
            min_interval=constants.ef_pwm_update_interval,
            offset=constants.ef_pwm_offset,
            min_value=constants.ef_pwm_min_value,
            value_cast="int",
        ),
        "EF spray pitch": ControlConfig(
            scale=constants.ef_pitch_scale,
            min_interval=constants.ef_pitch_update_interval,
            value_cast="int",
        ),
        "EF Yaw Angle": ControlConfig(
            scale=constants.ef_yaw_scale, min_interval=constants.ef_yaw_update_interval
        ),
        "EF Force": ControlConfig(
            scale=constants.ef_force_scale, min_interval=constants.ef_force_update_interval
        ),
        "Valve Turn": ControlConfig(
            scale=constants.valve_turn_scale, min_interval=constants.valve_turn_update_interval
        ),
        "Arm Rail Speed": ControlConfig(
            scale=constants.arm_rail_speed_scale, min_interval=constants.ef_rail_update_interval
        ),
        "Wheel Travel Left": ControlConfig(
            scale=constants.wheel_travel_scale,
            min_interval=constants.wheel_travel_update_interval,
            min_value=-constants.wheel_travel_max,
            max_value=constants.wheel_travel_max,
            bidirectional=True,
        ),
        "Wheel Travel Right": ControlConfig(
            scale=constants.wheel_travel_scale,
            min_interval=constants.wheel_travel_update_interval,
            min_value=-constants.wheel_travel_max,
            max_value=constants.wheel_travel_max,
            bidirectional=True,
        ),
    }


def scale_joystick_axis(
    raw_axis: float,
    config: ControlConfig,
    *,
    apply_offset: bool = True,
) -> float:
    """Map a raw stick axis through scale/offset and clamp for the control config."""
    value = float(raw_axis) * config.scale
    if apply_offset:
        value = value + config.offset
    if config.bidirectional:
        return max(config.min_value, min(config.max_value, value))
    if value < config.min_value:
        return 0.0
    return value

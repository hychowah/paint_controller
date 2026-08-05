"""Pure teleop control-config types and axis scaling (TD-055 Phase 3).

``ControlConfig`` / ``TeleopScaleConstants`` / ``scale_joystick_axis`` live here.
The production mode→config table is owned by ``teleop_modes`` (catalog SOT);
``build_default_control_configs`` re-exports that builder for stable imports.
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
    # Simple display formatting (ControlProcessor); special modes keep explicit code.
    display_decimals: int | None = 2  # None = no float formatting (use str/value_cast)
    display_unit: str = ""  # e.g. "mm"; empty = no unit suffix


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
    """Build the production mode→ControlConfig table (delegates to teleop catalog)."""
    # Local import avoids import cycle: teleop_modes imports ControlConfig from here.
    from paint_controller.handlers.policy.teleop_modes import build_control_configs

    return build_control_configs(constants)


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

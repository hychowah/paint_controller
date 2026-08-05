"""Teleop mode catalog — runtime source of truth for continuous stick modes.

Deep public surface (prefer these over reading internal rows):

- ``menu_labels()`` / ``display_name()`` — overlay selection
- ``build_control_configs()`` — scale/interval map for the engine
- ``apply_standard()`` — closed STANDARD device apply (after engine scale/cast)
- ``autorun_clear_labels()`` / ``duplicate_allowed_labels()`` — selection policy
- label set helpers for integrity tests

Layering: may import ``ports/*`` Protocols and ``ControlConfig`` types.
Must not import Qt, rclpy, or ``controllers/*``.

SPECIAL stick math stays in ``ContinuousTeleopEngine`` handlers; this module
only names which menu modes are SPECIAL for integrity and selection.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Final

from paint_controller.handlers.policy.teleop_control_map import ControlConfig, TeleopScaleConstants
from paint_controller.ports.teensy import SupportsTeensyTeleop

StandardApply = Callable[[SupportsTeensyTeleop, float | int], None]


class TeleopKind(str, Enum):
    STANDARD = "standard"
    SPECIAL = "special"
    SIDE_CHANNEL = "side_channel"


# --- STANDARD device apply (closed callables; multi-call allowed) ---------------


def _apply_ef_arm(teensy: SupportsTeensyTeleop, command: float | int) -> None:
    teensy.setArmRailSpeed(float(command))


def _apply_ef_spray_trigger(teensy: SupportsTeensyTeleop, command: float | int) -> None:
    teensy.setSprayTrigger(int(command))


def _apply_ef_top_rail(teensy: SupportsTeensyTeleop, command: float | int) -> None:
    teensy.setTopRailSpeed(float(command))


def _apply_ef_prop_pwm(teensy: SupportsTeensyTeleop, command: float | int) -> None:
    pwm = int(command)
    teensy.setLeftPropPWM(pwm)
    teensy.setRightPropPWM(pwm)


def _apply_ef_spray_pitch(teensy: SupportsTeensyTeleop, command: float | int) -> None:
    teensy.setSprayPitchSpeed(int(command))


_STANDARD_APPLY: Final[dict[str, StandardApply]] = {
    "EF arm": _apply_ef_arm,
    "EF spray trigger": _apply_ef_spray_trigger,
    "EF top rail": _apply_ef_top_rail,
    "EF prop pwm": _apply_ef_prop_pwm,
    "EF spray pitch": _apply_ef_spray_pitch,
}

# Ordered stick-menu labels (index 0 = sentinel "None"). Product muscle memory.
_MENU_LABELS: Final[tuple[str, ...]] = (
    "None",
    "Winch Speed",
    "Track Control Left",
    "Track Control Right",
    "Wheel Travel Left",
    "Wheel Travel Right",
    "EF arm",
    "EF top rail",
    "EF prop pwm",
    "EF prop joint",
    "EF spray trigger",
    "EF spray pitch",
    "EF Yaw Angle",
    "EF Force",
)

_DISPLAY_NAMES: Final[dict[str, str]] = {
    "None": "None",
    "Winch Speed": "Winch",
    "Track Control Left": "Track Left",
    "Track Control Right": "Track Right",
    "Wheel Travel Left": "Wheel Left",
    "Wheel Travel Right": "Wheel Right",
    "EF arm": "EF Arm",
    "EF top rail": "Top Rail",
    "EF prop pwm": "Prop PWM",
    "EF prop joint": "Prop Joint",
    "EF spray trigger": "Spray Trigger",
    "EF spray pitch": "Spray Pitch",
    "EF Yaw Angle": "Yaw",
    "EF Force": "EF Force",
}

# Former avoidAutoRunOverwrite indices 1, 8, 9
_AUTORUN_CLEAR: Final[frozenset[str]] = frozenset(
    {
        "Winch Speed",
        "EF prop pwm",
        "EF prop joint",
    }
)

# Former dual-select indices 2, 3
_DUPLICATE_ALLOWED: Final[frozenset[str]] = frozenset(
    {
        "Track Control Left",
        "Track Control Right",
    }
)

_SPECIAL_MENU: Final[frozenset[str]] = frozenset(
    {
        "Winch Speed",
        "Track Control Left",
        "Track Control Right",
        "Wheel Travel Left",
        "Wheel Travel Right",
        "EF prop joint",
        "EF Yaw Angle",
        "EF Force",
    }
)

_SIDE_CHANNELS: Final[frozenset[str]] = frozenset(
    {
        "Valve Turn",
        "Arm Rail Speed",
    }
)

# Engine _control_handlers keys for SPECIAL menu modes (parity target).
SPECIAL_HANDLER_KEYS: Final[frozenset[str]] = frozenset(
    {
        "Track Control Left",
        "Track Control Right",
        "EF prop joint",
        "EF Yaw Angle",
        "EF Force",
        "Winch Speed",
        "Wheel Travel Left",
        "Wheel Travel Right",
    }
)


def menu_labels() -> list[str]:
    """Ordered joystick overlay options (includes sentinel ``None``)."""
    return list(_MENU_LABELS)


def display_name(menu_label: str) -> str:
    """Compact ControlInfoPanel label; unknown labels pass through."""
    return _DISPLAY_NAMES.get(menu_label, menu_label)


def autorun_clear_labels() -> frozenset[str]:
    """Modes cleared to None when avoidAutoRunOverwrite runs."""
    return _AUTORUN_CLEAR


def duplicate_allowed_labels() -> frozenset[str]:
    """Modes that may be selected on both sticks (tracks)."""
    return _DUPLICATE_ALLOWED


def standard_mode_labels() -> frozenset[str]:
    return frozenset(_STANDARD_APPLY)


def special_mode_labels() -> frozenset[str]:
    return _SPECIAL_MENU


def side_channel_labels() -> frozenset[str]:
    return _SIDE_CHANNELS


def build_control_configs(constants: TeleopScaleConstants) -> dict[str, ControlConfig]:
    """Production mode → ControlConfig map (menu modes + side-channels; not ``None``)."""
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
            display_decimals=0,
            display_unit="mm",
        ),
        "Wheel Travel Right": ControlConfig(
            scale=constants.wheel_travel_scale,
            min_interval=constants.wheel_travel_update_interval,
            min_value=-constants.wheel_travel_max,
            max_value=constants.wheel_travel_max,
            bidirectional=True,
            display_decimals=0,
            display_unit="mm",
        ),
    }


def apply_standard(teensy: SupportsTeensyTeleop, mode: str, command: float | int) -> None:
    """Apply a STANDARD mode command to the Teensy teleop surface.

    Call only after the engine has scaled/cast the stick axis. Raises ``KeyError``
    if ``mode`` is not a STANDARD catalog entry (avoids silent no-ops).
    """
    apply = _STANDARD_APPLY.get(mode)
    if apply is None:
        raise KeyError(f"Not a STANDARD teleop mode: {mode!r}")
    apply(teensy, command)


def assert_catalog_invariants() -> None:
    """Raise AssertionError if the catalog is internally inconsistent.

    Intended for import-time or unit tests — keeps incomplete modes unrepresentable
    as a coherent catalog even when residual dual sources (enum, engine handlers)
    need separate parity tests.
    """
    menu = set(_MENU_LABELS)
    if "None" not in menu:
        raise AssertionError("menu must include sentinel None")
    if _MENU_LABELS[0] != "None":
        raise AssertionError("sentinel None must be first menu entry")

    menu_teleop = menu - {"None"}
    standard = set(_STANDARD_APPLY)
    special = set(_SPECIAL_MENU)
    side = set(_SIDE_CHANNELS)

    if standard & special:
        raise AssertionError(f"modes cannot be both STANDARD and SPECIAL: {standard & special}")
    if standard & side or special & side:
        raise AssertionError("side-channels must not overlap menu kinds")
    if menu_teleop != standard | special:
        raise AssertionError(
            f"menu teleop modes must equal STANDARD∪SPECIAL; "
            f"only menu={menu_teleop - (standard | special)}; "
            f"only kinds={(standard | special) - menu_teleop}"
        )
    if special != set(SPECIAL_HANDLER_KEYS):
        raise AssertionError(
            f"SPECIAL menu set must match SPECIAL_HANDLER_KEYS: "
            f"{special.symmetric_difference(SPECIAL_HANDLER_KEYS)}"
        )

    for label in menu:
        if label not in _DISPLAY_NAMES:
            raise AssertionError(f"missing display name for menu label {label!r}")

    if not _AUTORUN_CLEAR <= menu_teleop:
        raise AssertionError("autorun-clear labels must be menu teleop modes")
    if not _DUPLICATE_ALLOWED <= menu_teleop:
        raise AssertionError("duplicate-allowed labels must be menu teleop modes")

    # Config keys checked when constants are available (build path); structural
    # membership: every STANDARD/SPECIAL/side-channel is expected in build output.
    expected_config_keys = standard | special | side
    # Build with dummy constants only validates key set shape in tests; here we
    # just ensure STANDARD apply keys are non-empty.
    if not standard:
        raise AssertionError("catalog must define at least one STANDARD mode")
    _ = expected_config_keys


assert_catalog_invariants()

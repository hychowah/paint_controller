"""Integrity and parity tests for the teleop mode catalog (SOT)."""

from __future__ import annotations

import pytest

from paint_controller.handlers.continuous_teleop_engine import ContinuousTeleopEngine
from paint_controller.handlers.policy.teleop_control_map import (
    TeleopScaleConstants,
    build_default_control_configs,
)
from paint_controller.handlers.policy import teleop_modes
from paint_controller.utils.constants import JoystickControl


def _sample_constants() -> TeleopScaleConstants:
    return TeleopScaleConstants(
        winch_scale=0.01,
        winch_update_interval=0.1,
        winch_max_speed_mmps=500.0,
        track_scale=0.02,
        track_update_interval=0.1,
        ef_arm_scale=0.01,
        ef_arm_update_interval=0.1,
        ef_joint_scale=0.01,
        ef_joint_update_interval=0.1,
        ef_trigger_scale=0.01,
        ef_trigger_update_interval=0.2,
        ef_trigger_offset=1000,
        ef_trigger_min_value=1000,
        ef_rail_scale=0.01,
        ef_rail_update_interval=0.1,
        ef_pwm_scale=0.01,
        ef_pwm_update_interval=0.1,
        ef_pwm_offset=1000,
        ef_pwm_min_value=1000,
        ef_pitch_scale=0.01,
        ef_pitch_update_interval=0.2,
        ef_yaw_scale=0.01,
        ef_yaw_update_interval=0.1,
        ef_force_scale=0.01,
        ef_force_update_interval=0.1,
        valve_turn_scale=0.01,
        valve_turn_update_interval=0.3,
        arm_rail_speed_scale=0.01,
        wheel_travel_scale=1.0,
        wheel_travel_update_interval=0.1,
        wheel_travel_max=1000.0,
    )


# Golden ordered menu — operator muscle memory / product order.
_EXPECTED_MENU_ORDER = [
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
]


def test_menu_labels_golden_order() -> None:
    assert teleop_modes.menu_labels() == _EXPECTED_MENU_ORDER


def test_catalog_invariants_hold_at_import() -> None:
    teleop_modes.assert_catalog_invariants()


def test_every_menu_teleop_mode_has_control_config() -> None:
    configs = teleop_modes.build_control_configs(_sample_constants())
    for label in teleop_modes.menu_labels():
        if label == "None":
            assert label not in configs
            continue
        assert label in configs, f"missing config for menu mode {label!r}"


def test_every_config_key_is_menu_or_side_channel() -> None:
    configs = teleop_modes.build_control_configs(_sample_constants())
    menu_teleop = set(teleop_modes.menu_labels()) - {"None"}
    allowed = menu_teleop | teleop_modes.side_channel_labels()
    assert set(configs) == allowed


def test_build_default_control_configs_delegates_to_catalog() -> None:
    constants = _sample_constants()
    assert set(build_default_control_configs(constants)) == set(
        teleop_modes.build_control_configs(constants)
    )


def test_display_names_cover_all_menu_modes() -> None:
    for label in teleop_modes.menu_labels():
        name = teleop_modes.display_name(label)
        assert name  # non-empty
        # Catalog maps known modes; unknown pass through
        if label != "None":
            assert name == teleop_modes.display_name(label)


def test_autorun_and_duplicate_policy_sets() -> None:
    assert teleop_modes.autorun_clear_labels() == frozenset(
        {"Winch Speed", "EF prop pwm", "EF prop joint"}
    )
    assert teleop_modes.duplicate_allowed_labels() == frozenset(
        {"Track Control Left", "Track Control Right"}
    )


def test_default_stick_pair_labels_are_catalog_members() -> None:
    menu = set(teleop_modes.menu_labels())
    base_pair = teleop_modes.default_stick_pair("base")
    ef_pair = teleop_modes.default_stick_pair("ef")

    assert base_pair == ("Track Control Left", "Track Control Right")
    assert ef_pair == ("None", "Winch Speed")
    for label in (*base_pair, *ef_pair):
        assert label in menu


class _FakeTeensy:
    def __init__(self) -> None:
        self.arm_speeds: list[float] = []
        self.triggers: list[int] = []
        self.top_rails: list[float] = []
        self.left_pwms: list[int] = []
        self.right_pwms: list[int] = []
        self.pitch_speeds: list[int] = []

    def setArmRailSpeed(self, speed: float) -> None:
        self.arm_speeds.append(float(speed))

    def setSprayTrigger(self, value: int) -> None:
        self.triggers.append(int(value))

    def setTopRailSpeed(self, speed: float) -> None:
        self.top_rails.append(float(speed))

    def setLeftPropPWM(self, pwm: int) -> None:
        self.left_pwms.append(int(pwm))

    def setRightPropPWM(self, pwm: int) -> None:
        self.right_pwms.append(int(pwm))

    def setSprayPitchSpeed(self, speed: int) -> None:
        self.pitch_speeds.append(int(speed))

    def get_status_value(self, key: str) -> float:
        return 0.0


def test_every_standard_mode_dispatches() -> None:
    teensy = _FakeTeensy()
    teleop_modes.apply_standard(teensy, "EF arm", 12.5)
    teleop_modes.apply_standard(teensy, "EF spray trigger", 1100)
    teleop_modes.apply_standard(teensy, "EF top rail", 3.0)
    teleop_modes.apply_standard(teensy, "EF prop pwm", 1200)
    teleop_modes.apply_standard(teensy, "EF spray pitch", 15)

    assert teensy.arm_speeds == [12.5]
    assert teensy.triggers == [1100]
    assert teensy.top_rails == [3.0]
    assert teensy.left_pwms == [1200]
    assert teensy.right_pwms == [1200]
    assert teensy.pitch_speeds == [15]


def test_apply_standard_rejects_unknown_mode() -> None:
    with pytest.raises(KeyError, match="Not a STANDARD"):
        teleop_modes.apply_standard(_FakeTeensy(), "Winch Speed", 1.0)


def test_special_handler_keys_match_engine_map() -> None:
    engine = ContinuousTeleopEngine(
        wheel=object(),  # type: ignore[arg-type]
        winch=object(),  # type: ignore[arg-type]
        teensy=_FakeTeensy(),  # type: ignore[arg-type]
        esp32_valve=object(),  # type: ignore[arg-type]
        is_winch_locked=lambda: False,
    )
    handler_keys = set(engine._control_handlers)
    assert teleop_modes.SPECIAL_HANDLER_KEYS == handler_keys
    assert teleop_modes.special_mode_labels() == handler_keys


def test_joystick_control_enum_matches_catalog() -> None:
    """JoystickControl is a typed mirror; catalog is SOT for labels."""
    enum_values = {m.value for m in JoystickControl}
    menu = set(teleop_modes.menu_labels())
    side = teleop_modes.side_channel_labels()
    # Enum covers menu (incl None) plus non-menu side-channels used by engine.
    assert menu <= enum_values
    assert side <= enum_values
    # No stray enum values outside catalog populations.
    assert enum_values <= (menu | side)


def test_wheel_travel_display_metadata_from_catalog() -> None:
    configs = teleop_modes.build_control_configs(_sample_constants())
    for label in ("Wheel Travel Left", "Wheel Travel Right"):
        assert configs[label].display_decimals == 0
        assert configs[label].display_unit == "mm"


def test_special_handler_keys_remain_explicit_in_engine_source() -> None:
    """SPECIAL physics stays as explicit dict keys, not a dynamic registry."""
    from pathlib import Path

    engine_src = (
        Path(__file__).resolve().parent.parent
        / "python"
        / "paint_controller"
        / "handlers"
        / "continuous_teleop_engine.py"
    ).read_text()
    assert "_control_handlers = {" in engine_src
    for key in teleop_modes.SPECIAL_HANDLER_KEYS:
        assert f'"{key}"' in engine_src

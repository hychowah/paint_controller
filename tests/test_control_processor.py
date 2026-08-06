"""Tests for paint_controller.handlers.control_processor.ControlProcessor.

ControlProcessor is the safety-critical joystick→hardware command dispatcher.
It maps Steam Deck joystick input to track, winch, wheel, and EF motor commands.
"""

from __future__ import annotations

import importlib
import math
from typing import Any

from tests.fakes import (
    FakeEsp32Valve,
    FakeHeartbeatHandler,
    FakeOverlay,
    FakeStateStore,
    FakeTeensy,
    FakeWheel,
    FakeWinch,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

JOYSTICK_MAX = 32768.0
TRACK_DEAD_ZONE = 0.05
TRACK_MAX_SPEED = 500.0
TRACK_MIN_SPEED = 50.0


def _cp_module():
    return importlib.import_module("paint_controller.handlers.control_processor")


def _make_cp(
    wheel=None,
    winch=None,
    teensy=None,
    esp32_valve=None,
    overlay=None,
    heartbeat=None,
    state_store=None,
    settings_manager=None,
    safety_coordinator=None,
) -> Any:
    """Create a ControlProcessor with all-fake dependencies."""
    ControlProcessor = _cp_module().ControlProcessor
    return ControlProcessor(
        wheel=wheel or FakeWheel(),
        winch=winch or FakeWinch(),
        teensy=teensy or FakeTeensy(),
        esp32_valve=esp32_valve or FakeEsp32Valve(),
        selection_model=overlay or FakeOverlay(),
        heartbeat_handler=heartbeat or FakeHeartbeatHandler(),
        settings_manager=settings_manager,
        state_store=state_store or FakeStateStore(),
        safety_coordinator=safety_coordinator,
    )


def _stick_state(ly: float = 0.0, lx: float = 0.0, ry: float = 0.0, rx: float = 0.0) -> dict:
    """Build a minimal input_state dictionary."""
    return {
        "left_stick": {"y": ly, "x": lx},
        "right_stick": {"y": ry, "x": rx},
        "triggers": {"left": 0, "right": 0},
    }


# ---------------------------------------------------------------------------
# Settings defaults
# ---------------------------------------------------------------------------


def test_settings_manager_none_uses_hardcoded_defaults(qt_app) -> None:
    """When no settings_manager is provided, safe hardcoded defaults are used."""
    cp = _make_cp()
    assert cp.TRACK_MAX_SPEED == TRACK_MAX_SPEED
    assert cp.TRACK_MIN_SPEED == TRACK_MIN_SPEED
    assert cp._winch_max_speed_mmps == 400.0
    assert cp._wheel_travel_max == 500.0


def test_process_input_skips_engine_when_continuous_motion_latched(qt_app) -> None:
    """TD-054: after halt latch, process_input must not command wheel/winch."""
    from paint_controller.handlers.safety_coordinator import SafetyCoordinator

    wheel = FakeWheel()
    winch = FakeWinch()
    safety = SafetyCoordinator(wheel=wheel, winch=winch, teensy=FakeTeensy(), esp32_valve=FakeEsp32Valve())
    safety.halt_all_effectors("test")
    wheel.left_speed_commands.clear()
    wheel.right_speed_commands.clear()
    winch.rpm_commands.clear()

    overlay = FakeOverlay()
    overlay.left_option = "Track Control Left"
    overlay.right_option = "None"
    cp = _make_cp(wheel=wheel, winch=winch, overlay=overlay, safety_coordinator=safety)
    cp.process_input(_stick_state(ly=JOYSTICK_MAX))

    assert wheel.left_speed_commands == []
    assert wheel.right_speed_commands == []
    assert winch.rpm_commands == []


def test_process_input_idle_skip_when_modes_none_and_sticks_centered(qt_app) -> None:
    """P-03: no engine tick when both modes None and sticks idle (e-stop still external)."""
    from paint_controller.utils.perf_counters import PERF

    PERF.set_enabled(True)
    PERF.reset()
    wheel = FakeWheel()
    overlay = FakeOverlay(left="None", right="None")
    cp = _make_cp(wheel=wheel, overlay=overlay)
    # Patch engine.tick to detect calls without relying on HW side effects.
    calls = {"n": 0}
    original = cp._engine.tick

    def _counting_tick(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    cp._engine.tick = _counting_tick  # type: ignore[method-assign]
    cp.process_input(_stick_state())
    assert calls["n"] == 0
    assert PERF.count("teleop_idle_skip") == 1
    # Active stick with mode still ticks.
    cp2 = _make_cp(wheel=wheel, overlay=FakeOverlay(left="Track Control Left", right="None"))
    calls2 = {"n": 0}
    original2 = cp2._engine.tick

    def _counting_tick2(*args, **kwargs):
        calls2["n"] += 1
        return original2(*args, **kwargs)

    cp2._engine.tick = _counting_tick2  # type: ignore[method-assign]
    cp2.process_input(_stick_state(ly=JOYSTICK_MAX))
    assert calls2["n"] == 1
    PERF.set_enabled(False)
    PERF.reset()


def test_process_input_still_ticks_when_mode_selected_but_sticks_idle(qt_app) -> None:
    """P-03: selected modes must tick so zero/deadzone paths still run."""
    overlay = FakeOverlay(left="Track Control Left", right="None")
    cp = _make_cp(overlay=overlay)
    calls = {"n": 0}
    original = cp._engine.tick

    def _counting_tick(*args, **kwargs):
        calls["n"] += 1
        return original(*args, **kwargs)

    cp._engine.tick = _counting_tick  # type: ignore[method-assign]
    cp.process_input(_stick_state())  # sticks centered, mode selected
    assert calls["n"] == 1


def test_process_input_deselect_track_zeros_wheel_with_sticks_centered(qt_app) -> None:
    """P-03 fix: deselect Track Control → None must still tick and zero the track.

    Idle early-out must not skip note_selection/_zero_tracks_leaving_selection when
    the selection pair changes to None with sticks already centered.
    """
    wheel = FakeWheel()

    class _MutableOverlay:
        def __init__(self) -> None:
            self.left = "Track Control Left"
            self.right = "None"

        def get_left_selected_option(self) -> str:
            return self.left

        def get_right_selected_option(self) -> str:
            return self.right

        def display_name_for_option(self, option: str) -> str:
            return option

    overlay = _MutableOverlay()
    cp = _make_cp(wheel=wheel, overlay=overlay)

    # Drive left track at full stick so a non-zero command is latched.
    cp.process_input(_stick_state(ly=JOYSTICK_MAX))
    assert wheel.left_speed_commands, "expected a non-zero track command while mode active"
    assert wheel.left_speed_commands[-1] != 0.0

    # Deselect with sticks centered — must still zero the leaving track side.
    overlay.left = "None"
    cp.process_input(_stick_state())
    assert wheel.left_speed_commands[-1] == 0.0


# ---------------------------------------------------------------------------
# Nonlinear curve (_apply_nonlinear_curve)
# ---------------------------------------------------------------------------


def test_nonlinear_curve_zero_returns_zero(qt_app) -> None:
    cp = _make_cp()
    assert cp._apply_nonlinear_curve(0.0) == 0.0


def test_nonlinear_curve_inside_deadzone_returns_zero(qt_app) -> None:
    """Any input ≤ TRACK_DEAD_ZONE (5%) must produce zero — no creep."""
    cp = _make_cp()
    assert cp._apply_nonlinear_curve(TRACK_DEAD_ZONE) == 0.0
    assert cp._apply_nonlinear_curve(TRACK_DEAD_ZONE * 0.99) == 0.0


def test_nonlinear_curve_preserves_sign(qt_app) -> None:
    cp = _make_cp()
    positive = cp._apply_nonlinear_curve(0.5)
    negative = cp._apply_nonlinear_curve(-0.5)
    assert positive > 0
    assert negative < 0
    assert math.isclose(positive, -negative, rel_tol=1e-9)


def test_nonlinear_curve_max_input_at_most_track_max_speed(qt_app) -> None:
    cp = _make_cp()
    assert abs(cp._apply_nonlinear_curve(1.0)) <= TRACK_MAX_SPEED
    assert abs(cp._apply_nonlinear_curve(-1.0)) <= TRACK_MAX_SPEED


def test_nonlinear_curve_output_is_at_least_min_speed_outside_deadzone(qt_app) -> None:
    """Once outside the deadzone, output must be ≥ TRACK_MIN_SPEED so motors start."""
    cp = _make_cp()
    just_outside = TRACK_DEAD_ZONE + 0.001
    speed = cp._apply_nonlinear_curve(just_outside)
    assert speed >= TRACK_MIN_SPEED


def test_nonlinear_curve_monotonically_increasing_magnitude(qt_app) -> None:
    """Larger joystick input must always produce larger (or equal) speed."""
    cp = _make_cp()
    inputs = [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    speeds = [cp._apply_nonlinear_curve(x) for x in inputs]
    for a, b in zip(speeds, speeds[1:]):
        assert b >= a, f"Speed decreased from {a} to {b}"


# ---------------------------------------------------------------------------
# Track control (_process_track_control)
# ---------------------------------------------------------------------------


def test_track_left_joystick_in_deadzone_sends_no_command(qt_app) -> None:
    """Joystick at exactly 0 (center) must not command wheel motion."""
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    cp._process_track_control(_stick_state(ly=0), "Track Control Left", "left")
    assert wheel.left_speed_commands == [0.0]  # zero-speed is still sent (motor hold)


def test_track_left_sends_command_to_left_wheel_only(qt_app) -> None:
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    cp._process_track_control(_stick_state(ly=JOYSTICK_MAX), "Track Control Left", "left")
    assert len(wheel.left_speed_commands) == 1
    assert wheel.right_speed_commands == []


def test_track_right_sends_command_to_right_wheel_only(qt_app) -> None:
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    cp._process_track_control(_stick_state(ry=JOYSTICK_MAX), "Track Control Right", "right")
    assert len(wheel.right_speed_commands) == 1
    assert wheel.left_speed_commands == []


def test_track_command_clamped_to_max_speed(qt_app) -> None:
    """Joystick at maximum deflection must never command speed above TRACK_MAX_SPEED."""
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    cp._process_track_control(_stick_state(ly=JOYSTICK_MAX), "Track Control Left", "left")
    assert abs(wheel.left_speed_commands[0]) <= TRACK_MAX_SPEED


def test_track_reverse_direction(qt_app) -> None:
    """Negative joystick deflection must produce a negative (reverse) track command."""
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    cp._process_track_control(_stick_state(ly=-JOYSTICK_MAX), "Track Control Left", "left")
    assert wheel.left_speed_commands[0] < 0


def test_track_nonlinear_result_less_than_linear_at_half_deflection(qt_app) -> None:
    """At 50% deflection the nonlinear curve must give less than 50% of max speed
    (curve is designed to provide fine control at low speeds)."""
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    half_joystick = JOYSTICK_MAX * 0.5
    cp._process_track_control(_stick_state(ly=half_joystick), "Track Control Left", "left")
    commanded = wheel.left_speed_commands[0]
    linear_half = TRACK_MAX_SPEED * 0.5
    assert commanded < linear_half, f"Expected nonlinear speed ({commanded:.1f}) < linear half ({linear_half:.1f})"


# ---------------------------------------------------------------------------
# Winch speed (_process_winch_speed)
# ---------------------------------------------------------------------------


def _full_winch_input() -> dict:
    """Input state with joystick at maximum (produces value ≈ max_speed)."""
    return _stick_state(ly=JOYSTICK_MAX)


def _make_active_cp_with_winch(winch: FakeWinch) -> Any:
    """Create ControlProcessor with winch already activated (joystick moved once)."""
    cp = _make_cp(winch=winch)
    cp.winch_speed_has_been_active = True  # simulate prior joystick movement
    return cp


def test_winch_rejected_when_not_available(qt_app) -> None:
    winch = FakeWinch(available=False)
    cp = _make_active_cp_with_winch(winch)
    cp._process_winch_speed(_full_winch_input(), "Winch Speed", "left")
    assert winch.speed_commands == []


def test_winch_rejected_when_motor_brake_on(qt_app) -> None:
    winch = FakeWinch(available=True, motor_brake=True)
    cp = _make_active_cp_with_winch(winch)
    cp._process_winch_speed(_full_winch_input(), "Winch Speed", "left")
    assert winch.speed_commands == []


def test_winch_locked_when_base_is_ontask(qt_app) -> None:
    """Winch must be locked when base heartbeat reports ONTASK (0x01)."""
    from paint_controller.handlers.heartbeat import HeartbeatStatus

    winch = FakeWinch(available=True)
    heartbeat = FakeHeartbeatHandler(base_status=HeartbeatStatus.ONTASK.value)
    cp = _make_cp(winch=winch, heartbeat=heartbeat)
    cp.winch_speed_has_been_active = True
    cp._process_winch_speed(_full_winch_input(), "Winch Speed", "left")
    assert winch.speed_commands == []


def test_winch_locked_when_ef_is_ontask(qt_app) -> None:
    """Winch must be locked when EF heartbeat reports ONTASK (0x01)."""
    from paint_controller.handlers.heartbeat import HeartbeatStatus

    winch = FakeWinch(available=True)
    heartbeat = FakeHeartbeatHandler(ef_status=HeartbeatStatus.ONTASK.value)
    cp = _make_cp(winch=winch, heartbeat=heartbeat)
    cp.winch_speed_has_been_active = True
    cp._process_winch_speed(_full_winch_input(), "Winch Speed", "left")
    assert winch.speed_commands == []


def test_winch_not_locked_when_both_idle(qt_app) -> None:
    """Winch must be able to move when both heartbeats report IDLE (0x00)."""
    winch = FakeWinch(available=True)
    heartbeat = FakeHeartbeatHandler(base_status=0x00, ef_status=0x00)
    cp = _make_cp(winch=winch, heartbeat=heartbeat)
    cp.winch_speed_has_been_active = True
    cp._process_winch_speed(_full_winch_input(), "Winch Speed", "left")
    assert len(winch.speed_commands) == 1


class _MutableOverlay:
    def __init__(self, left: str = "None", right: str = "None") -> None:
        self.left = left
        self.right = right

    def get_left_selected_option(self) -> str:
        return self.left

    def get_right_selected_option(self) -> str:
        return self.right

    def display_name_for_option(self, option: str) -> str:
        return option


def test_process_input_seeds_yaw_offset_when_selection_changes_to_yaw(qt_app) -> None:
    teensy = FakeTeensy()
    teensy._imu_yaw = 12.5
    overlay = _MutableOverlay(left="None", right="None")
    cp = _make_cp(teensy=teensy, overlay=overlay)

    cp.controls["EF Yaw Angle"].offset = -1.0
    overlay.left = "EF Yaw Angle"

    cp.process_input(_stick_state())

    assert cp.controls["EF Yaw Angle"].offset == 12.5
    assert teensy.yaw_commands == [12.5]


def test_process_input_does_not_reseed_yaw_offset_when_selection_is_unchanged(qt_app) -> None:
    teensy = FakeTeensy()
    teensy._imu_yaw = 7.0
    overlay = _MutableOverlay(left="EF Yaw Angle", right="None")
    cp = _make_cp(teensy=teensy, overlay=overlay)

    cp.controls["EF Yaw Angle"].offset = 3.0

    cp.process_input(_stick_state())

    assert cp.controls["EF Yaw Angle"].offset == 3.0
    assert teensy.yaw_commands == [3.0]


def test_process_input_reseeds_yaw_offset_when_selection_changes_but_yaw_remains_active(qt_app) -> None:
    teensy = FakeTeensy()
    teensy._imu_yaw = 21.0
    overlay = _MutableOverlay(left="EF Yaw Angle", right="None")
    cp = _make_cp(teensy=teensy, overlay=overlay)

    cp.controls["EF Yaw Angle"].offset = 5.0
    overlay.right = "Track Control Right"

    cp.process_input(_stick_state())

    assert cp.controls["EF Yaw Angle"].offset == 21.0
    assert teensy.yaw_commands == [21.0]


# ---------------------------------------------------------------------------
# EF teleop method ports (TD-049 — was raw Teensy pubs)
# ---------------------------------------------------------------------------


def test_joint_control_sends_opposite_signed_angles(qt_app) -> None:
    """Left joint = +angle, right joint = −angle (hardware dual-sign semantics)."""
    teensy = FakeTeensy()
    cp = _make_cp(teensy=teensy)
    stick_x = JOYSTICK_MAX * 0.5
    cp._process_joint_control(_stick_state(lx=stick_x), "EF prop joint", "left")
    expected = stick_x * cp.controls["EF prop joint"].scale
    assert len(teensy.left_joint_commands) == 1
    assert len(teensy.right_joint_commands) == 1
    assert math.isclose(teensy.left_joint_commands[0], expected, rel_tol=1e-9)
    assert math.isclose(teensy.right_joint_commands[0], -expected, rel_tol=1e-9)


def test_ef_arm_stick_commands_arm_rail_speed(qt_app) -> None:
    teensy = FakeTeensy()
    cp = _make_cp(teensy=teensy)
    cp._process_standard_control(_stick_state(ly=JOYSTICK_MAX), "EF arm", "left")
    assert len(teensy.rail_speed_commands) == 1
    assert teensy.rail_speed_commands[0] > 0


def test_ef_top_rail_commands_top_rail_speed(qt_app) -> None:
    teensy = FakeTeensy()
    cp = _make_cp(teensy=teensy)
    cp._process_standard_control(_stick_state(ly=JOYSTICK_MAX), "EF top rail", "left")
    assert len(teensy.top_rail_speed_commands) == 1
    assert teensy.top_rail_speed_commands[0] > 0


def test_ef_spray_trigger_sends_int_trigger(qt_app) -> None:
    teensy = FakeTeensy()
    cp = _make_cp(teensy=teensy)
    # value = y * scale + offset(1000); full stick clears min_value 1000
    cp._process_standard_control(_stick_state(ly=JOYSTICK_MAX), "EF spray trigger", "left")
    assert len(teensy.trigger_values) == 1
    assert isinstance(teensy.trigger_values[0], int)
    assert teensy.trigger_values[0] >= 1000


def test_ef_prop_pwm_sends_same_int_to_both_props(qt_app) -> None:
    teensy = FakeTeensy()
    cp = _make_cp(teensy=teensy)
    cp._process_standard_control(_stick_state(ly=JOYSTICK_MAX), "EF prop pwm", "left")
    assert len(teensy.left_pwm_commands) == 1
    assert len(teensy.right_pwm_commands) == 1
    assert teensy.left_pwm_commands[0] == teensy.right_pwm_commands[0]
    assert isinstance(teensy.left_pwm_commands[0], int)
    assert teensy.left_pwm_commands[0] >= 1000


def test_ef_spray_pitch_sends_int_pitch_speed(qt_app) -> None:
    teensy = FakeTeensy()
    cp = _make_cp(teensy=teensy)
    cp._process_standard_control(_stick_state(ly=JOYSTICK_MAX), "EF spray pitch", "left")
    assert len(teensy.pitch_speed_commands) == 1
    assert isinstance(teensy.pitch_speed_commands[0], int)


def test_winch_activation_gate_blocks_until_joystick_moved(qt_app) -> None:
    """Winch must NOT send commands until the joystick has been moved outside
    the deadzone at least once (prevents spurious commands on mode switch)."""
    winch = FakeWinch(available=True)
    cp = _make_cp(winch=winch)
    assert cp.winch_speed_has_been_active is False
    # Even with joystick in deadzone and should_send=True, gate blocks command
    cp._process_winch_speed(_stick_state(ly=0), "Winch Speed", "left")
    assert winch.speed_commands == []


def test_winch_activation_gate_opens_after_joystick_moves(qt_app) -> None:
    """After joystick first moves outside deadzone, commands must flow."""
    winch = FakeWinch(available=True)
    cp = _make_cp(winch=winch)
    # Joystick at full deflection: outside deadzone → sets winch_speed_has_been_active=True
    cp._process_winch_speed(_full_winch_input(), "Winch Speed", "left")
    assert cp.winch_speed_has_been_active is True
    assert len(winch.speed_commands) == 1


def test_reset_winch_activation_clears_gate_and_deadzone(qt_app) -> None:
    """reset_winch_activation() must re-arm the activation gate (called on mode switch)."""
    cp = _make_cp()
    cp.winch_speed_has_been_active = True
    cp.reset_winch_activation()
    assert cp.winch_speed_has_been_active is False


# ---------------------------------------------------------------------------
# Wheel travel (_process_wheel_travel)
# ---------------------------------------------------------------------------


def _small_joystick_state(y_fraction: float = 1.0) -> dict:
    return _stick_state(ly=JOYSTICK_MAX * y_fraction)


def test_wheel_travel_accumulates_left_value(qt_app) -> None:
    """Each call to _process_wheel_travel should add to the accumulated travel."""
    cp = _make_cp()
    initial = cp._left_wheel_travel_mm
    cp._process_wheel_travel(_small_joystick_state(), "Wheel Travel Left", "left")
    cp._process_wheel_travel(_small_joystick_state(), "Wheel Travel Left", "left")
    assert cp._left_wheel_travel_mm > initial


def test_wheel_travel_accumulates_right_value_separately(qt_app) -> None:
    cp = _make_cp()
    cp._process_wheel_travel(_small_joystick_state(), "Wheel Travel Right", "left")
    assert cp._right_wheel_travel_mm > 0.0
    assert cp._left_wheel_travel_mm == 0.0  # left must not be affected


def test_wheel_travel_clamped_positive_at_max(qt_app) -> None:
    """Accumulated travel must not exceed wheel_travel_max."""
    cp = _make_cp()
    # Drive far beyond max with many calls
    for _ in range(10000):
        cp._process_wheel_travel(_small_joystick_state(), "Wheel Travel Left", "left")
    assert cp._left_wheel_travel_mm <= cp._wheel_travel_max


def test_wheel_travel_clamped_negative_at_minus_max(qt_app) -> None:
    cp = _make_cp()
    for _ in range(10000):
        cp._process_wheel_travel(_stick_state(ly=-JOYSTICK_MAX), "Wheel Travel Left", "left")
    assert cp._left_wheel_travel_mm >= -cp._wheel_travel_max


def test_wheel_travel_does_not_send_command(qt_app) -> None:
    """_process_wheel_travel must only accumulate — no wheel command until button pressed."""
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    for _ in range(10):
        cp._process_wheel_travel(_small_joystick_state(), "Wheel Travel Left", "left")
    assert wheel.position_commands == []


# ---------------------------------------------------------------------------
# send_wheel_travel_command
# ---------------------------------------------------------------------------


def test_send_wheel_travel_command_calls_position_command(qt_app) -> None:
    wheel = FakeWheel()
    cp = _make_cp(wheel=wheel)
    cp._left_wheel_travel_mm = 150.0
    cp._right_wheel_travel_mm = -75.0
    cp.send_wheel_travel_command()
    assert len(wheel.position_commands) == 1
    left_mm, right_mm, rpm, relative = wheel.position_commands[0]
    assert left_mm == 150
    assert right_mm == -75
    assert relative is True


def test_send_wheel_travel_command_uses_configured_rpm(qt_app) -> None:
    wheel = FakeWheel()
    cp = _make_cp()
    cp._wheel = wheel
    cp._left_wheel_travel_mm = 50.0
    cp.send_wheel_travel_command()
    _, _, rpm, _ = wheel.position_commands[0]
    assert rpm == cp._wheel_travel_rpm


# ---------------------------------------------------------------------------
# process_input dispatch (via overlay mode)
# ---------------------------------------------------------------------------


def test_process_input_dispatches_track_left_to_left_wheel(qt_app) -> None:
    """process_input with Track Control Left overlay must call left wheel speed."""
    wheel = FakeWheel()
    overlay = FakeOverlay(left="Track Control Left", right="None")
    cp = _make_cp(wheel=wheel, overlay=overlay)
    state = _stick_state(ly=JOYSTICK_MAX)
    cp.process_input(state)
    assert len(wheel.left_speed_commands) == 1
    assert wheel.right_speed_commands == []


def test_process_input_dispatches_track_right_to_right_wheel(qt_app) -> None:
    wheel = FakeWheel()
    overlay = FakeOverlay(left="None", right="Track Control Right")
    cp = _make_cp(wheel=wheel, overlay=overlay)
    state = _stick_state(ry=JOYSTICK_MAX)
    cp.process_input(state)
    assert len(wheel.right_speed_commands) == 1
    assert wheel.left_speed_commands == []


def test_process_input_unknown_mode_sends_no_command(qt_app) -> None:
    """Overlay returning an unrecognised mode must produce no crash and no command."""
    wheel = FakeWheel()
    overlay = FakeOverlay(left="Unknown Mode", right="Unknown Mode")
    cp = _make_cp(wheel=wheel, overlay=overlay)
    cp.process_input(_stick_state(ly=JOYSTICK_MAX, ry=JOYSTICK_MAX))
    assert wheel.left_speed_commands == []
    assert wheel.right_speed_commands == []


def test_display_properties_follow_selection_model(qt_app) -> None:
    """Compact display labels are derived from the canonical selection model names."""
    from paint_controller.models.joystick_selection import JoystickSelectionModel

    model = JoystickSelectionModel()
    model.set_joystick_controls("Track Control Left", "EF Yaw Angle")
    cp = _make_cp(overlay=model)

    cp.process_input(_stick_state())

    assert cp.left_control_mode == "Track Control Left"
    assert cp.left_control_mode_display == "Track Left"
    assert cp.right_control_mode == "EF Yaw Angle"
    assert cp.right_control_mode_display == "Yaw"


# ---------------------------------------------------------------------------
# Track mode lifecycle + cross-stick display (partner-hold seam)
# ---------------------------------------------------------------------------


class PartnerHoldWheel:
    """Mirrors WheelHal: each side command republishes the last partner RPM."""

    def __init__(self) -> None:
        self.pairs: list[tuple[int, int]] = []
        self._left = 0
        self._right = 0

    def command_left_wheel_speed(self, speed: float) -> None:
        self._left = int(speed)
        self.pairs.append((self._left, self._right))

    def command_right_wheel_speed(self, speed: float) -> None:
        self._right = int(speed)
        self.pairs.append((self._left, self._right))

    def command_position(self, left_mm: float, right_mm: float, rpm_limit: float, relative: bool) -> bool:
        return True

    def emergency_stop(self) -> None:
        self._left = 0
        self._right = 0
        self.pairs.append((0, 0))


def _clear_engine_rate_limits(cp: Any) -> None:
    """Allow the next process_input tick to pass mode min_interval gates."""
    cp._engine.last_command_times.clear()


def test_deselecting_track_right_zeros_right_while_left_track_continues(qt_app) -> None:
    """Leaving Track Control Right must publish right=0; partner hold must not keep it spinning.

    FakeWheel hides this bug because it never republishes partner RPM. PartnerHoldWheel
    mirrors production WheelHal so the teleop deselect path is exercised for real.
    """
    wheel = PartnerHoldWheel()
    overlay = FakeOverlay(left="Track Control Left", right="Track Control Right")
    cp = _make_cp(wheel=wheel, overlay=overlay)

    cp.process_input(_stick_state(ly=JOYSTICK_MAX, ry=JOYSTICK_MAX))
    assert wheel.pairs, "expected both tracks to publish"
    assert wheel.pairs[-1][0] != 0 and wheel.pairs[-1][1] != 0

    overlay._right = "None"
    _clear_engine_rate_limits(cp)
    cp.process_input(_stick_state(ly=JOYSTICK_MAX, ry=0))

    last_left, last_right = wheel.pairs[-1]
    assert last_right == 0, f"deselected right track must zero, got pair {wheel.pairs[-1]}"
    assert last_left != 0, f"active left track must keep commanding, got pair {wheel.pairs[-1]}"


def test_deselecting_track_left_zeros_left_while_right_track_continues(qt_app) -> None:
    """Symmetric lifecycle: removing Track Control Left must zero the left wheel."""
    wheel = PartnerHoldWheel()
    overlay = FakeOverlay(left="Track Control Left", right="Track Control Right")
    cp = _make_cp(wheel=wheel, overlay=overlay)

    cp.process_input(_stick_state(ly=JOYSTICK_MAX, ry=JOYSTICK_MAX))
    overlay._left = "None"
    _clear_engine_rate_limits(cp)
    cp.process_input(_stick_state(ly=0, ry=JOYSTICK_MAX))

    last_left, last_right = wheel.pairs[-1]
    assert last_left == 0, f"deselected left track must zero, got pair {wheel.pairs[-1]}"
    assert last_right != 0, f"active right track must keep commanding, got pair {wheel.pairs[-1]}"


def test_track_left_on_right_stick_drives_left_wheel_and_right_panel(qt_app) -> None:
    """Mode selects the wheel; stick selects input and display side."""
    wheel = FakeWheel()
    overlay = FakeOverlay(left="None", right="Track Control Left")
    cp = _make_cp(wheel=wheel, overlay=overlay)

    cp.process_input(_stick_state(ly=0, ry=JOYSTICK_MAX))

    assert len(wheel.left_speed_commands) == 1
    assert wheel.left_speed_commands[0] != 0
    assert wheel.right_speed_commands == []
    assert cp.right_control_mode == "Track Control Left"
    assert cp.right_control_value != ""
    assert cp.left_control_mode == "None"
    assert cp.left_control_value == ""


def test_track_left_on_right_stick_does_not_clobber_left_panel_display(qt_app) -> None:
    """Track Control Left on the right stick must not overwrite left stick display values."""
    from paint_controller.models.joystick_selection import JoystickSelectionModel

    wheel = FakeWheel()
    model = JoystickSelectionModel()
    model.set_joystick_controls("EF arm", "Track Control Left")
    cp = _make_cp(wheel=wheel, overlay=model)

    cp.process_input(_stick_state(ly=JOYSTICK_MAX, ry=JOYSTICK_MAX))

    assert wheel.left_speed_commands  # track mode still drives left wheel
    assert cp.left_control_mode == "EF arm"
    assert cp.right_control_mode == "Track Control Left"
    assert "L:" in cp.right_control_value or cp.right_control_value != ""

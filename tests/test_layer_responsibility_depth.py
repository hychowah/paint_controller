"""TD-055 structural + pure-policy tests for layer responsibility depth.

These drive shipped modules: ports, demo_sequence, action_legality,
teleop_control_map, TeensyController surface, and workflow hardware adapters.
"""

from __future__ import annotations

import importlib
import inspect

from paint_controller.handlers.demo_sequence import run_demo_action
from paint_controller.handlers.policy.action_legality import (
    evaluate_action_legality,
    enforcement_enabled_from_env_and_settings,
)
from paint_controller.handlers.policy.teleop_control_map import (
    ControlConfig,
    TeleopScaleConstants,
    build_default_control_configs,
    scale_joystick_axis,
)
from paint_controller.services.workflow.hardware import (
    HardwareControllers,
    TeensyControllerAdapter,
    WinchControllerAdapter,
)
from paint_controller.utils.constants import HeartbeatStatus


# --- Pure policy (no QObject) -------------------------------------------------


def test_evaluate_action_legality_blocks_maintenance_in_error_without_qobject() -> None:
    evaluation = evaluate_action_legality(
        "wheel.reset_position",
        heartbeat_state=HeartbeatStatus.ERROR.value,
        enforcement_enabled=True,
        metadata={
            "title": "Reset Wheel Position",
            "legalStateClass": "maintenance-preset",
        },
    )
    assert evaluation["allowed"] is False
    assert "ERROR" in evaluation["reason"]


def test_evaluate_action_legality_allows_when_enforcement_off() -> None:
    evaluation = evaluate_action_legality(
        "wheel.reset_position",
        heartbeat_state=HeartbeatStatus.ERROR.value,
        enforcement_enabled=False,
    )
    assert evaluation["allowed"] is True
    assert evaluation["reason"] == ""


def test_enforcement_enabled_from_env_overrides_settings() -> None:
    assert (
        enforcement_enabled_from_env_and_settings(
            lambda key, default=None: True,
            env={"PAINT_ACTION_LEGALITY_ENFORCED": "0"},
        )
        is False
    )
    assert (
        enforcement_enabled_from_env_and_settings(
            lambda key, default=None: False,
            env={"PAINT_ACTION_LEGALITY_ENFORCED": "1"},
        )
        is True
    )


def test_build_default_control_configs_includes_winch_and_track() -> None:
    constants = TeleopScaleConstants(
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
    controls = build_default_control_configs(constants)
    assert "Winch Speed" in controls
    assert "Track Control Left" in controls
    assert controls["Winch Speed"].bidirectional is True
    assert controls["Winch Speed"].max_value == 500.0


def test_scale_joystick_axis_clamps_bidirectional() -> None:
    config = ControlConfig(scale=1.0, min_interval=0.1, min_value=-10.0, max_value=10.0, bidirectional=True)
    assert scale_joystick_axis(50.0, config, apply_offset=False) == 10.0
    assert scale_joystick_axis(-50.0, config, apply_offset=False) == -10.0


# --- Demo sequence (application op, not device) ------------------------------


class _DemoTeensy:
    def __init__(self) -> None:
        self.pitch: list[tuple[float, float]] = []
        self.force: list[tuple[float, float]] = []

    def setSprayGunPitchAngle(self, angle: float, speed: float) -> None:
        self.pitch.append((angle, speed))

    def set_ef_force(self, fx: float, fy: float) -> None:
        self.force.append((fx, fy))

    def extendArm(self, dist: int) -> None:
        pass


class _DemoWinch:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, int]] = []

    def move_absolute_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int = 30) -> None:
        self.calls.append((length_mm, speed_mm_s, acceleration_rpm_s))

    def move_increment_with_accel(self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int = 30) -> None:
        pass

    def get_cable_length(self) -> float:
        return 0.0


def test_run_demo_action_sequences_teensy_and_winch() -> None:
    teensy = _DemoTeensy()
    winch = _DemoWinch()
    run_demo_action(
        teensy,
        winch,
        pitch_angle=1.0,
        pitch_speed=2.0,
        cable_length=300,
        cable_speed=40,
        force_y=0.5,
    )
    assert teensy.pitch == [(1.0, 2.0)]
    assert winch.calls == [(300, 40, 30)]
    assert teensy.force == [(0.0, 0.5)]


# --- Device surface purity ---------------------------------------------------


def test_teensy_controller_ctor_rejects_foreign_concerns() -> None:
    """Teensy is a device adapter: no show_popup_fn / winch_controller / demoAction."""
    teensy_mod = importlib.import_module("paint_controller.controllers.teensy")
    ctor = inspect.signature(teensy_mod.TeensyController.__init__)
    params = set(ctor.parameters)
    assert "show_popup_fn" not in params
    assert "winch_controller" not in params
    assert not hasattr(teensy_mod.TeensyController, "demoAction")


def test_workflow_hardware_has_no_parallel_abc_interfaces() -> None:
    hardware = importlib.import_module("paint_controller.services.workflow.hardware")
    assert not hasattr(hardware, "ITeensyController")
    assert not hasattr(hardware, "IWinchController")
    assert hasattr(hardware, "TeensyControllerAdapter")
    assert hasattr(hardware, "WinchControllerAdapter")


def test_workflow_adapters_use_shared_port_methods() -> None:
    class Body:
        def __init__(self) -> None:
            self.pitch = []
            self.arm = []
            self.force = []

        def setSprayGunPitchAngle(self, angle: float, speed: float) -> None:
            self.pitch.append((angle, speed))

        def extendArm(self, dist: int) -> None:
            self.arm.append(dist)

        def set_ef_force(self, fx: float, fy: float) -> None:
            self.force.append((fx, fy))

    class Valve:
        def __init__(self) -> None:
            self.turns = []

        def setValveTurn(self, value: float) -> None:
            self.turns.append(value)

    class Winch:
        def __init__(self) -> None:
            self.moves = []

        def move_absolute_with_accel(self, a, b, c=30) -> None:
            self.moves.append(("abs", a, b, c))

        def move_increment_with_accel(self, a, b, c=30) -> None:
            self.moves.append(("inc", a, b, c))

        def get_cable_length(self) -> float:
            return 12.5

    body = Body()
    valve = Valve()
    winch = Winch()
    bundle = HardwareControllers.from_controllers(body, winch, valve)
    assert isinstance(bundle.teensy, TeensyControllerAdapter)
    assert isinstance(bundle.winch, WinchControllerAdapter)
    bundle.teensy.set_spray_gun_gimbal_angle(5.0, 1.0)
    bundle.teensy.set_valve_turn(0.25)
    bundle.winch.move_absolute(100, 50, 20)
    assert body.pitch == [(5.0, 1.0)]
    assert valve.turns == [0.25]
    assert winch.moves == [("abs", 100, 50, 20)]
    assert bundle.winch.get_cable_length() == 12.5


def test_ports_package_exports_winch_wheel_valve_clusters() -> None:
    ports = importlib.import_module("paint_controller.ports")
    for name in (
        "SupportsWinchMotion",
        "SupportsWinchTeleop",
        "SupportsWinchWorkflow",
        "SupportsWheelTeleop",
        "SupportsWheelCommands",
        "SupportsValveCommand",
        "SupportsTeensyTeleop",
        "SupportsTeensyWorkflowBody",
    ):
        assert hasattr(ports, name), name


def test_control_processor_types_against_ports_not_concrete_controllers() -> None:
    source = inspect.getsource(
        importlib.import_module("paint_controller.handlers.control_processor").ControlProcessor.__init__
    )
    assert "SupportsWheelTeleop" in source
    assert "SupportsWinchTeleop" in source
    assert "SupportsValveCommand" in source
    assert "SupportsTeensyTeleop" in source
    assert "WheelController" not in source
    assert "WinchController" not in source
    assert "ESP32ValveController" not in source

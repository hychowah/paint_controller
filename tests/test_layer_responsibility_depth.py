"""TD-055 structural + pure-policy tests for layer responsibility depth.

These drive shipped modules: ports, demo_sequence, action_legality,
teleop_control_map, TeensyController surface, and workflow hardware adapters.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path

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
    pure = importlib.import_module("paint_controller.controllers.teensy")
    shell = importlib.import_module("paint_controller.controllers.teensy_shell")
    for cls in (pure.TeensyHal, shell.TeensyController):
        ctor = inspect.signature(cls.__init__)
        params = set(ctor.parameters)
        assert "show_popup_fn" not in params
        assert "winch_controller" not in params
        assert not hasattr(cls, "demoAction")


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
    bundle.teensy.setSprayGunPitchAngle(5.0, 1.0)
    bundle.teensy.setValveTurn(0.25)
    bundle.winch.move_absolute_with_accel(100, 50, 20)
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


def test_scale_joystick_axis_used_by_production_teleop() -> None:
    """TD-055.6: pure scaler must have production callers (not test-only dual truth)."""
    engine_src = Path(
        importlib.import_module("paint_controller.handlers.continuous_teleop_engine").__file__
    ).read_text(encoding="utf-8")
    winch_src = Path(
        importlib.import_module("paint_controller.handlers.winch_teleop").__file__
    ).read_text(encoding="utf-8")
    assert "scale_joystick_axis" in engine_src
    assert "scale_joystick_axis" in winch_src


def test_continuous_teleop_engine_ticks_without_qobject() -> None:
    """TD-055.8: engine is non-Qt and drives devices on tick."""
    from paint_controller.handlers.continuous_teleop_engine import ContinuousTeleopEngine
    from PySide6.QtCore import QObject

    class W:
        def __init__(self) -> None:
            self.left = []
            self.right = []

        def command_left_wheel_speed(self, s: float) -> None:
            self.left.append(s)

        def command_right_wheel_speed(self, s: float) -> None:
            self.right.append(s)

        def command_position(self, **kw) -> bool:
            return True

        def emergency_stop(self) -> None:
            pass

    class Winch:
        def get_available(self) -> bool:
            return True

        def get_motor_brake(self) -> bool:
            return False

        def command_speed_mmps(self, v: float) -> None:
            pass

    class Teensy:
        def get_status_value(self, key: str):
            return 0.0

        def setLeftPropJoint(self, *a):
            pass

        def setRightPropJoint(self, *a):
            pass

        def set_ef_force(self, *a):
            pass

        def setYawAngle(self, *a):
            pass

        def setArmRailSpeed(self, *a):
            pass

        def setSprayTrigger(self, *a):
            pass

        def setTopRailSpeed(self, *a):
            pass

        def setLeftPropPWM(self, *a):
            pass

        def setRightPropPWM(self, *a):
            pass

        def setSprayPitchSpeed(self, *a):
            pass

    class Valve:
        def setValveTurn(self, v: float) -> None:
            pass

    wheel = W()
    engine = ContinuousTeleopEngine(
        wheel, Winch(), Teensy(), Valve(), is_winch_locked=lambda: False
    )
    assert not isinstance(engine, QObject)
    engine.tick(
        {
            "left_stick": {"x": 0, "y": 10000},
            "right_stick": {"x": 0, "y": 0},
            "triggers": {"left": 0, "right": 0},
        },
        "Track Control Left",
        "None",
    )
    assert len(wheel.left) == 1


def test_migrated_actions_have_no_string_method_dispatch() -> None:
    """TD-055.7: primary action façades must not use method_name string getattr."""
    for mod_name in (
        "paint_controller.models.teensy_actions",
        "paint_controller.models.tuning_actions",
        "paint_controller.models.recording_actions",
        "paint_controller.models.system_actions",
        "paint_controller.models.wheel_actions",
        "paint_controller.models.winch_actions",
    ):
        src = Path(importlib.import_module(mod_name).__file__).read_text(encoding="utf-8")
        assert "method_name" not in src, mod_name
        assert "getattr(controller" not in src and "getattr(self._teensy, method_name" not in src, mod_name


def test_wheel_port_declares_command_position() -> None:
    from paint_controller.ports.wheel import SupportsWheelTeleop

    assert "command_position" in SupportsWheelTeleop.__dict__ or "command_position" in getattr(
        SupportsWheelTeleop, "__annotations__", {}
    ) or any(
        getattr(m, "__name__", "") == "command_position"
        for m in SupportsWheelTeleop.__dict__.values()
        if callable(m)
    ) or "command_position" in inspect.getsource(SupportsWheelTeleop)


def test_factory_uses_subsystem_builders() -> None:
    src = Path(
        importlib.import_module("paint_controller.core.controller_factory").__file__
    ).read_text(encoding="utf-8")
    assert "_build_device_adapters" in src
    assert "_build_control_plane" in src
    assert "_build_presentation_actions" in src
    assert "_build_workflow_and_services" in src


def test_manual_winch_uses_single_port_verb() -> None:
    src = Path(
        importlib.import_module("paint_controller.handlers.manual_commands").__file__
    ).read_text(encoding="utf-8")
    assert "move_increment_with_accel" in src
    assert "moveIncrementWithAccel" not in src

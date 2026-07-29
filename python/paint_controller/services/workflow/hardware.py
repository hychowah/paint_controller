#!/usr/bin/env python3
"""Workflow hardware adapters over the shared ports vocabulary (TD-055).

Adapters pull complexity downward: availability checks and error translation
live here. Capability shapes come from ``paint_controller.ports`` — not a
parallel ABC dialect.
"""

from __future__ import annotations

from paint_controller.ports.teensy import SupportsTeensyWorkflowBody
from paint_controller.ports.valve import SupportsValveCommand
from paint_controller.ports.winch import SupportsWinchWorkflow


class ControllerError(Exception):
    """Base exception for controller errors."""

    pass


class ControllerNotAvailable(ControllerError):  # noqa: N818 — public workflow exception name
    """Raised when controller is not available."""

    pass


class TeensyControllerAdapter:
    """Workflow-facing Teensy+valve adapter implementing shared port methods."""

    def __init__(
        self,
        teensy_controller: SupportsTeensyWorkflowBody | None,
        valve_controller: SupportsValveCommand | None = None,
    ):
        self._teensy_controller = teensy_controller
        self._valve_controller = valve_controller

    def set_valve_turn(self, turn_value: float) -> None:
        if not self._valve_controller:
            raise ControllerNotAvailable("ESP32 valve controller not available")
        self._valve_controller.setValveTurn(float(turn_value))

    def set_spray_gun_gimbal_angle(self, angle: float, speed: float) -> None:
        if not self._teensy_controller:
            raise ControllerNotAvailable("Teensy controller not available")
        self._teensy_controller.setSprayGunPitchAngle(float(angle), float(speed))

    def extend_arm(self, distance: int) -> None:
        if not self._teensy_controller:
            raise ControllerNotAvailable("Teensy controller not available")
        self._teensy_controller.extendArm(int(distance))

    def set_ef_force(self, fx: float, fy: float) -> None:
        if not self._teensy_controller:
            raise ControllerNotAvailable("Teensy controller not available")
        self._teensy_controller.set_ef_force(float(fx), float(fy))


class WinchControllerAdapter:
    """Workflow-facing winch adapter over ``SupportsWinchWorkflow``."""

    def __init__(self, controller: SupportsWinchWorkflow | None):
        self._controller = controller

    def move_increment(self, length: int, speed: int, acceleration: int = 30) -> None:
        if not self._controller:
            raise ControllerNotAvailable("Winch controller not available")
        self._controller.move_increment_with_accel(int(length), int(speed), int(acceleration))

    def move_absolute(self, length: int, speed: int, acceleration: int = 30) -> None:
        if not self._controller:
            raise ControllerNotAvailable("Winch controller not available")
        self._controller.move_absolute_with_accel(int(length), int(speed), int(acceleration))

    def get_cable_length(self) -> float:
        if not self._controller:
            raise ControllerNotAvailable("Winch controller not available")
        return self._controller.get_cable_length()


class HardwareControllers:
    """Container for workflow hardware adapter instances."""

    def __init__(
        self,
        teensy_controller: TeensyControllerAdapter | None = None,
        winch_controller: WinchControllerAdapter | None = None,
    ):
        self.teensy = teensy_controller
        self.winch = winch_controller

    @classmethod
    def from_robot_controller(cls, robot_controller):
        teensy = None
        winch = None

        if hasattr(robot_controller, "teensy_controller") and robot_controller.teensy_controller:
            valve_controller = getattr(robot_controller, "esp32_valve_controller", None)
            teensy = TeensyControllerAdapter(robot_controller.teensy_controller, valve_controller)

        if hasattr(robot_controller, "winch_controller") and robot_controller.winch_controller:
            winch = WinchControllerAdapter(robot_controller.winch_controller)

        return cls(teensy_controller=teensy, winch_controller=winch)

    @classmethod
    def from_controllers(cls, teensy_ctrl, winch_ctrl, esp32_valve_ctrl=None):
        teensy = TeensyControllerAdapter(teensy_ctrl, esp32_valve_ctrl) if teensy_ctrl else None
        winch = WinchControllerAdapter(winch_ctrl) if winch_ctrl else None
        return cls(teensy_controller=teensy, winch_controller=winch)

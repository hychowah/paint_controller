"""Winch capability Protocols shared by teleop, safety, workflow, and actions (TD-055).

One vocabulary for winch motion — workflow adapters and handlers type against
these surfaces instead of a parallel ABC HAL.
"""

from __future__ import annotations

from typing import Protocol

from paint_controller.ports.halt import SupportsWinchHalt


class SupportsWinchTeleop(Protocol):
    """Continuous stick teleop surface used by ControlProcessor / winch_teleop."""

    def get_available(self) -> bool: ...

    def get_motor_brake(self) -> bool: ...

    def command_speed_mmps(self, value: float) -> object: ...


class SupportsWinchWorkflow(Protocol):
    """Workflow / sequenced motion surface (absolute & incremental with accel)."""

    def move_increment_with_accel(
        self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int = 30
    ) -> object: ...

    def move_absolute_with_accel(
        self, length_mm: int, speed_mm_s: int, acceleration_rpm_s: int = 30
    ) -> object: ...

    def get_cable_length(self) -> float: ...


class SupportsWinchMotion(SupportsWinchHalt, SupportsWinchWorkflow, SupportsWinchTeleop, Protocol):
    """Discrete page/actions surface plus halt, teleop, and workflow motion.

    Controllers implement this full surface; callers depend only on the cluster
    they need (teleop vs workflow vs halt).
    """

    def move_increment(self, length_mm: int, speed_mm_s: int) -> object: ...

    def move_absolute(self, length_mm: int, speed_mm_s: int) -> object: ...

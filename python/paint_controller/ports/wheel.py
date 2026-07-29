"""Wheel capability Protocols shared by teleop, safety, and actions (TD-055)."""

from __future__ import annotations

from typing import Protocol

from paint_controller.ports.halt import SupportsWheelHalt


class SupportsWheelTeleop(SupportsWheelHalt, Protocol):
    """Continuous track teleop surface used by ControlProcessor."""

    def command_left_wheel_speed(self, speed: float) -> object: ...

    def command_right_wheel_speed(self, speed: float) -> object: ...


class SupportsWheelCommands(SupportsWheelTeleop, Protocol):
    """Discrete wheel actions surface (enable / reset) plus teleop and halt."""

    def setEnabled(self, enabled: bool) -> object: ...

    def resetWheelPosition(self) -> object: ...

    @property
    def enabled(self) -> bool: ...

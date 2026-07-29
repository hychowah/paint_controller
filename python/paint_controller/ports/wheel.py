"""Wheel capability Protocols shared by teleop, safety, and actions (TD-055)."""

from __future__ import annotations

from typing import Protocol

from paint_controller.ports.halt import SupportsWheelHalt


class SupportsWheelTeleop(SupportsWheelHalt, Protocol):
    """Continuous teleop surface: track speeds + travel position fire."""

    def command_left_wheel_speed(self, speed: float) -> object: ...

    def command_right_wheel_speed(self, speed: float) -> object: ...

    def command_position(
        self,
        left_mm: int,
        right_mm: int,
        rpm_limit: int,
        relative: bool = True,
    ) -> object: ...


class SupportsWheelCommands(SupportsWheelTeleop, Protocol):
    """Discrete wheel actions surface (enable / reset) plus teleop and halt."""

    def setEnabled(self, enabled: bool) -> object: ...

    def resetWheelPosition(self) -> object: ...

    @property
    def enabled(self) -> bool: ...

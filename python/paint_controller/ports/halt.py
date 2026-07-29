"""Per-device safe-stop Protocols for SafetyCoordinator (TD-049)."""

from __future__ import annotations

from typing import Protocol


class SupportsWinchHalt(Protocol):
    def command_speed_rpm(self, value: float) -> object: ...


class SupportsWheelHalt(Protocol):
    def emergency_stop(self) -> object: ...


class SupportsValveHalt(Protocol):
    def setValveTurn(self, value: float) -> object: ...

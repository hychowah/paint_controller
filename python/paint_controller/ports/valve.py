"""Valve capability Protocol shared by teleop, safety, and workflow (TD-055)."""

from __future__ import annotations

from typing import Protocol

from paint_controller.ports.halt import SupportsValveHalt


class SupportsValveCommand(SupportsValveHalt, Protocol):
    """Set valve turn position (halt uses the same method with zero)."""

    def setValveTurn(self, value: float) -> object: ...

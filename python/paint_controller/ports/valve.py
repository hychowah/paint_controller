"""Valve capability Protocol shared by teleop, safety, and workflow (TD-055).

TD-055.6: one name for the surface — command and halt are the same method
(``setValveTurn``; halt uses zero). ``SupportsValveCommand`` is an alias of
``SupportsValveHalt`` (no inheritance ladder for the same method).
"""

from __future__ import annotations

from paint_controller.ports.halt import SupportsValveHalt

# Single vocabulary: teleop + safety both use setValveTurn.
SupportsValveCommand = SupportsValveHalt

__all__ = ["SupportsValveCommand", "SupportsValveHalt"]

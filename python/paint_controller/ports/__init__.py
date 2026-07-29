"""Shared hardware capability Protocols (TD-049 / TD-055).

Lightweight package only — no Qt/ROS imports. Controllers stay leaves;
handlers, actions, and workflow adapters type against these structural Protocols.

Honesty (TD-055): this is the **single** hardware vocabulary for capability
clusters used by ≥2 consumers. Do not add a second parallel HAL under services/.
"""

from paint_controller.ports.halt import (
    SupportsValveHalt,
    SupportsWheelHalt,
    SupportsWinchHalt,
)
from paint_controller.ports.teensy import (
    SupportsTeensyHalt,
    SupportsTeensyStatusRead,
    SupportsTeensyTeleop,
    SupportsTeensyWorkflowBody,
)
from paint_controller.ports.valve import SupportsValveCommand
from paint_controller.ports.wheel import SupportsWheelCommands, SupportsWheelTeleop
from paint_controller.ports.winch import (
    SupportsWinchMotion,
    SupportsWinchTeleop,
    SupportsWinchWorkflow,
)

__all__ = [
    "SupportsTeensyHalt",
    "SupportsTeensyStatusRead",
    "SupportsTeensyTeleop",
    "SupportsTeensyWorkflowBody",
    "SupportsValveCommand",
    "SupportsValveHalt",
    "SupportsWheelCommands",
    "SupportsWheelHalt",
    "SupportsWheelTeleop",
    "SupportsWinchHalt",
    "SupportsWinchMotion",
    "SupportsWinchTeleop",
    "SupportsWinchWorkflow",
]

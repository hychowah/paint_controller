"""Shared hardware port Protocols (TD-049).

Lightweight package only — no Qt/ROS imports. Controllers stay leaves;
handlers and workflow adapters type against these structural Protocols.
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

__all__ = [
    "SupportsTeensyHalt",
    "SupportsTeensyStatusRead",
    "SupportsTeensyTeleop",
    "SupportsTeensyWorkflowBody",
    "SupportsValveHalt",
    "SupportsWheelHalt",
    "SupportsWinchHalt",
]

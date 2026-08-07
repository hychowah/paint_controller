"""Centralized constants and enums for the paint controller application.

All magic strings used across the codebase are defined here as enums
to prevent silent failures from typos and enable IDE autocompletion.
"""

from enum import Enum, IntEnum


class ControlMode(str, Enum):
    """Robot control modes — base (track) vs end-effector."""

    BASE = "base"
    END_EFFECTOR = "ef"


class JoystickControl(str, Enum):
    """Joystick control options available in the overlay menu.

    Values must match exact strings used in QML and control_processor configs.
    """

    NONE = "None"
    WINCH_SPEED = "Winch Speed"
    TRACK_LEFT = "Track Control Left"
    TRACK_RIGHT = "Track Control Right"
    WHEEL_TRAVEL_LEFT = "Wheel Travel Left"
    WHEEL_TRAVEL_RIGHT = "Wheel Travel Right"
    EF_ARM = "EF arm"
    EF_TOP_RAIL = "EF top rail"
    EF_PROP_PWM = "EF prop pwm"
    EF_PROP_JOINT = "EF prop joint"
    EF_SPRAY_TRIGGER = "EF spray trigger"
    EF_SPRAY_PITCH = "EF spray pitch"
    EF_YAW_ANGLE = "EF Yaw Angle"
    EF_FORCE = "EF Force"
    VALVE_TURN = "Valve Turn"
    ARM_RAIL_SPEED = "Arm Rail Speed"


class HeartbeatStatus(IntEnum):
    """Controller heartbeat status values shared across UI and ROS."""

    IDLE = 0x00
    ONTASK = 0x01
    WARNING = 0x02
    ERROR = 0x03
    CLEAR_ERROR = 0x04


# Qt-free SOT for hold-to-exit duration so tests/integrity checks can read it
# without importing PySide6 via handlers/exit_hold.py.
DEFAULT_EXIT_HOLD_DURATION_S = 1.0

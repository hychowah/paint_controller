"""Canonical action keys for discrete operator commands.

This module is the single source of truth for action-key strings shared by
``models/*_actions.py``, ``capability_catalog.py``, QML ``actionKey`` bindings,
and ``handlers/policy/action_legality.py`` overrides.

Ungated actions (e.g., Teensy feature toggles, home rails, recording toggles)
intentionally do not have entries here; only gated admin/machine-affecting
actions do.
"""

from __future__ import annotations

from enum import Enum


class ActionKey(str, Enum):
    """Typed action keys for gated discrete commands."""

    # Wheel
    WHEEL_ENABLE = "wheel.enable"
    WHEEL_RESET_POSITION = "wheel.reset_position"

    # Winch
    WINCH_MOVE_INCREMENT = "winch.move_increment"
    WINCH_MOVE_ABSOLUTE = "winch.move_absolute"
    WINCH_RETRACT_FULL = "winch.retract_full"
    WINCH_EXTEND_ONE_METER = "winch.extend_one_meter"
    WINCH_EMERGENCY_STOP = "winch.emergency_stop"
    WINCH_LOAD_DETECTION = "winch.load_detection"

    # Status / enable toggles
    STATUS_WINCH_ENABLE = "status.winch_enable"
    STATUS_TEENSY_ENABLE = "status.teensy_enable"
    STATUS_TEENSY_RELAY = "status.teensy_relay"

    # Tuning
    TUNING_SHORT_YAW_PID = "tuning.short_yaw_pid"
    TUNING_LONG_YAW_PID = "tuning.long_yaw_pid"

    # Base top view camera
    CAMERA_BASE_TOP_VIEW_LIVE_ADJUSTMENTS = "camera.base_top_view.live_adjustments"
    CAMERA_BASE_TOP_VIEW_SAVE = "camera.base_top_view.save"
    CAMERA_BASE_TOP_VIEW_RESET = "camera.base_top_view.reset"

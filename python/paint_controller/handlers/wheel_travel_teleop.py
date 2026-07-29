"""Wheel travel continuous teleop (accumulate stick, fire on button).

Used by ``ControlProcessor`` only. Stick path does not publish ROS; ``send`` does.
Does not use ``AdminActionGate``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from paint_controller.ports.wheel import SupportsWheelTeleop

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WheelTravelTickResult:
    """Accumulated travel after one stick tick (caller owns HUD)."""

    left_mm: float
    right_mm: float
    display_value: float


def travel_scale(rate_mm_per_s: float, update_interval_s: float, joystick_max: float) -> float:
    """mm per update at full joystick deflection."""
    return (rate_mm_per_s * update_interval_s) / joystick_max


def accumulate_wheel_travel(
    input_state: dict[str, Any],
    mode: str,
    stick: str,
    *,
    left_mm: float,
    right_mm: float,
    scale: float,
    travel_max: float,
) -> WheelTravelTickResult:
    """Accumulate left/right travel mm from stick Y."""
    delta = input_state[f"{stick}_stick"]["y"] * scale

    if mode == "Wheel Travel Left":
        left_mm += delta
        left_mm = max(-travel_max, min(travel_max, left_mm))
        display = left_mm
    else:  # "Wheel Travel Right"
        right_mm += delta
        right_mm = max(-travel_max, min(travel_max, right_mm))
        display = right_mm

    return WheelTravelTickResult(left_mm, right_mm, display)


def send_wheel_travel_command(
    wheel: SupportsWheelTeleop,
    *,
    left_mm: float,
    right_mm: float,
    rpm: int,
) -> bool:
    """Publish accumulated relative position command. Returns success."""
    try:
        success = wheel.command_position(
            left_mm=int(left_mm),
            right_mm=int(right_mm),
            rpm_limit=rpm,
            relative=True,
        )
        if success:
            logger.info(
                "Wheel travel command sent: left=%.0fmm, right=%.0fmm, rpm=%s",
                left_mm,
                right_mm,
                rpm,
            )
        else:
            logger.warning("Failed to send wheel travel command")
        return bool(success)
    except Exception as e:
        logger.error("Error sending wheel travel command: %s", e)
        return False

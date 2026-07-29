"""Winch continuous teleop helpers (high-state stick path).

Used by ``ControlProcessor`` only. Does not use ``AdminActionGate``.
"""

from __future__ import annotations

import logging
from typing import Any

from collections.abc import Callable
from dataclasses import dataclass

from paint_controller.handlers.policy.teleop_control_map import scale_joystick_axis
from paint_controller.ports.winch import SupportsWinchTeleop
from paint_controller.utils.constants import HeartbeatStatus
from paint_controller.utils.input import DeadzoneTracker

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WinchTickResult:
    """Result of one winch stick tick (no HUD mutation)."""

    has_been_active: bool
    display_value: float
    commanded: bool


def is_winch_control_locked(
    *,
    get_base_status: Callable[[], int],
    get_ef_status: Callable[[], int],
) -> bool:
    """True when base or EF heartbeat reports ONTASK (winch stick must not command)."""
    return (
        get_base_status() == HeartbeatStatus.ONTASK.value
        or get_ef_status() == HeartbeatStatus.ONTASK.value
    )


def process_winch_speed(
    input_state: dict[str, Any],
    mode: str,
    stick: str,
    *,
    config: Any,
    deadzone: DeadzoneTracker,
    deadzone_threshold: float,
    has_been_active: bool,
    winch: SupportsWinchTeleop,
    is_locked: Callable[[], bool],
) -> WinchTickResult:
    """Map stick Y to winch speed; return tick result (caller owns HUD)."""
    raw = float(input_state[f"{stick}_stick"]["y"])
    value = scale_joystick_axis(raw, config, apply_offset=True)

    normalized_value = abs(value) / config.max_value if config.max_value > 0 else 0
    should_send = deadzone.update(normalized_value, deadzone_threshold)

    if not deadzone.in_deadzone:
        has_been_active = True

    commanded = False
    if should_send and has_been_active:
        try:
            if not winch.get_available():
                logger.warning("Winch not available")
                return WinchTickResult(has_been_active, value, False)

            if winch.get_motor_brake():
                logger.warning("Winch motor brake is on")
                return WinchTickResult(has_been_active, value, False)

            if is_locked():
                logger.warning("Winch control locked: Base or EF is in ONTASK state")
                return WinchTickResult(has_been_active, value, False)

            winch.command_speed_mmps(value)
            commanded = True
        except Exception as e:
            logger.error("Error commanding winch speed: %s", e)

    return WinchTickResult(has_been_active, value, commanded)


def reset_winch_activation(deadzone: DeadzoneTracker) -> None:
    """Clear deadzone history when leaving winch stick mode."""
    deadzone.reset()

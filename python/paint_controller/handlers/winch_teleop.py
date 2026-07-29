"""Winch continuous teleop helpers (high-state stick path).

Used by ``ControlProcessor`` only. Does not use ``AdminActionGate``.
"""

from __future__ import annotations

import logging
from typing import Any

from paint_controller.handlers.heartbeat import HeartbeatStatus
from paint_controller.utils.input import DeadzoneTracker

logger = logging.getLogger(__name__)


def is_winch_control_locked(heartbeat_handler: Any) -> bool:
    """True when base or EF heartbeat reports ONTASK (winch stick must not command)."""
    base_status = heartbeat_handler.get_base_status()
    ef_status = heartbeat_handler.get_ef_status()
    return base_status == HeartbeatStatus.ONTASK.value or ef_status == HeartbeatStatus.ONTASK.value


def process_winch_speed(
    input_state: dict[str, Any],
    mode: str,
    stick: str,
    *,
    config: Any,
    current_values: dict[str, Any],
    deadzone: DeadzoneTracker,
    deadzone_threshold: float,
    has_been_active: bool,
    winch: Any,
    heartbeat_handler: Any,
) -> bool:
    """Map stick Y to winch speed; return updated ``has_been_active`` flag."""
    value = input_state[f"{stick}_stick"]["y"] * config.scale + config.offset
    value = max(config.min_value, min(config.max_value, value))

    if stick == "left":
        current_values["left_mode"] = mode
        current_values["left_value"] = value
    else:
        current_values["right_mode"] = mode
        current_values["right_value"] = value

    normalized_value = abs(value) / config.max_value if config.max_value > 0 else 0
    should_send = deadzone.update(normalized_value, deadzone_threshold)

    if not deadzone.in_deadzone:
        has_been_active = True

    if should_send and has_been_active:
        try:
            if not winch.get_available():
                logger.warning("Winch not available")
                return has_been_active

            if winch.get_motor_brake():
                logger.warning("Winch motor brake is on")
                return has_been_active

            if is_winch_control_locked(heartbeat_handler):
                logger.warning("Winch control locked: Base or EF is in ONTASK state")
                return has_been_active

            winch.command_speed_mmps(value)
        except Exception as e:
            logger.error("Error commanding winch speed: %s", e)

    return has_been_active


def reset_winch_activation(deadzone: DeadzoneTracker) -> None:
    """Clear deadzone history when leaving winch stick mode."""
    deadzone.reset()

"""Runtime defaults for application bootstrap."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeDefaults:
    """Small bootstrap defaults that are not persisted in SettingsManager."""

    video_port: int = 5000
    update_rate: float = 60.0
    joystick_deadzone: float = 0.1

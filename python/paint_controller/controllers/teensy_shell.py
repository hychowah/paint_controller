#!/usr/bin/env python3
"""Qt I/O shell for pure :class:`~paint_controller.controllers.teensy.TeensyHal` (Level C P4)."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, QTimer, Signal
from rclpy.node import Node

from paint_controller.controllers.teensy import TeensyHal
from paint_controller.core.availability_watchdog import AvailabilityWatchdog
from paint_controller.core.device_notifier import SignalDeviceNotifier
from paint_controller.core.ros_telemetry import RosTelemetryBridge

logger = logging.getLogger(__name__)

_SHELL_ATTRS = frozenset(
    {
        "_hal",
        "_notifier",
        "_telemetry",
        "_watchdog",
        "_io_shell",
        "_thrust_ramp_timer",
        "_settings_manager",
    }
)


class TeensyController(QObject):
    """Presentation/I/O shell for Teensy HAL (Signals, bridge, thrust timer, settings)."""

    status_changed = Signal(dict)
    connection_changed = Signal(bool)
    spray_gun_leveling_changed = Signal(bool)
    spray_gun_led_changed = Signal(bool)
    auto_correction_enabled_changed = Signal(bool)
    stability_enabled_changed = Signal(bool)
    thrust_force_changed = Signal(float)
    thrust_force_enabled_changed = Signal(bool)
    roller_steering_enabled_changed = Signal(bool)
    swing_damping_enabled_changed = Signal(bool)

    def __init__(
        self,
        node: Node,
        settings_manager: Any | None = None,
        command_bus: Any | None = None,
        *,
        io_shell: QObject | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._io_shell = io_shell if io_shell is not None else self
        self._settings_manager = settings_manager
        self._notifier = SignalDeviceNotifier(self, parent=self)
        self._telemetry = RosTelemetryBridge(self._apply_status_snapshot, parent=self._io_shell)

        thrust_force = -1.0
        thrust_ramp_rate = 1.0
        if settings_manager is not None:
            thrust_force = settings_manager.get("thrust_force") or -1.0
            thrust_ramp_rate = settings_manager.get("thrust_ramp_rate", 1.0)

        self._hal = TeensyHal(
            node,
            notifier=self._notifier,
            post_status=self._telemetry.post,
            command_bus=command_bus,
            thrust_force=float(thrust_force),
            thrust_ramp_rate=float(thrust_ramp_rate),
        )

        # Settings fan-in on shell (pure HAL has no SettingsManager.connect).
        if settings_manager is not None:
            if hasattr(settings_manager, "thrust_force_changed"):
                settings_manager.thrust_force_changed.connect(self._hal.apply_thrust_force_setting)
            if hasattr(settings_manager, "thrust_ramp_rate_changed"):
                settings_manager.thrust_ramp_rate_changed.connect(self._hal.apply_thrust_ramp_rate_setting)

        self._watchdog = AvailabilityWatchdog(
            self._hal._check_availability,
            interval_ms=200,
            parent=self._io_shell,
        )
        # Thrust ramping timer (10Hz) stays on shell — timing unchanged.
        self._thrust_ramp_timer = QTimer(self)
        self._thrust_ramp_timer.timeout.connect(self._hal._update_thrust_ramp)
        self._thrust_ramp_timer.start(100)

    def _apply_status_snapshot(self, snap: object) -> None:
        self._hal._apply_status_snapshot(snap)

    @property
    def io_shell(self) -> QObject:
        return self._io_shell

    @property
    def hal(self) -> TeensyHal:
        return self._hal

    def cleanup(self) -> None:
        if self._watchdog is not None:
            self._watchdog.stop()
        if self._thrust_ramp_timer.isActive():
            self._thrust_ramp_timer.stop()
        self._hal.cleanup()

    def __getattr__(self, name: str) -> Any:
        if name in _SHELL_ATTRS:
            raise AttributeError(name)
        try:
            hal = object.__getattribute__(self, "_hal")
        except AttributeError as exc:
            raise AttributeError(name) from exc
        return getattr(hal, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in _SHELL_ATTRS or name.startswith("_Q"):
            return super().__setattr__(name, value)
        if "_hal" not in self.__dict__:
            return super().__setattr__(name, value)
        if name in self.__dict__ or name in type(self).__dict__:
            return super().__setattr__(name, value)
        if hasattr(self._hal, name) or name.startswith("_"):
            setattr(self._hal, name, value)
            return None
        return super().__setattr__(name, value)

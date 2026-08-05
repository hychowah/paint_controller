#!/usr/bin/env python3
"""Qt I/O shell for pure :class:`~paint_controller.controllers.winch.WinchHal` (Level C P3)."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, Signal
from rclpy.node import Node

from paint_controller.controllers.winch import WinchHal
from paint_controller.core.availability_watchdog import AvailabilityWatchdog
from paint_controller.core.device_notifier import SignalDeviceNotifier
from paint_controller.core.ros_telemetry import RosTelemetryBridge

logger = logging.getLogger(__name__)

_SHELL_ATTRS = frozenset({"_hal", "_notifier", "_telemetry", "_watchdog", "_io_shell", "_settings_manager"})


class WinchController(QObject):
    """Presentation/I/O shell for winch HAL (Status Signals + settings inject)."""

    cable_length_changed = Signal()
    cable_speed_changed = Signal()
    winch_torque_changed = Signal()
    motor_temperature_changed = Signal()
    motor_voltage_changed = Signal()
    motor_brake_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()
    load_detection_changed = Signal()
    unusual_load_detected_changed = Signal()

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

        max_speed = 400.0
        if settings_manager is not None:
            max_speed = settings_manager.get("winch_max_speed_mmps") or 400.0

        self._hal = WinchHal(
            node,
            notifier=self._notifier,
            post_status=self._telemetry.post,
            command_bus=command_bus,
            max_speed=float(max_speed),
        )
        # Settings fan-in on shell — pure HAL has no SettingsManager.connect.
        if settings_manager is not None and hasattr(settings_manager, "winch_max_speed_mmps_changed"):
            settings_manager.winch_max_speed_mmps_changed.connect(self._hal.set_max_speed)

        self._watchdog = AvailabilityWatchdog(
            self._hal._check_availability,
            interval_ms=200,
            parent=self._io_shell,
        )

    def _apply_status_snapshot(self, snap: object) -> None:
        self._hal._apply_status_snapshot(snap)

    @property
    def io_shell(self) -> QObject:
        return self._io_shell

    @property
    def hal(self) -> WinchHal:
        return self._hal

    def cleanup(self) -> None:
        if self._watchdog is not None:
            self._watchdog.stop()
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

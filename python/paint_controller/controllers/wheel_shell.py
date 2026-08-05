#!/usr/bin/env python3
"""Qt I/O shell for pure :class:`~paint_controller.controllers.wheel.WheelHal` (Level C P3)."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, Signal
from rclpy.node import Node

from paint_controller.controllers.wheel import WheelHal
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
    }
)


class WheelController(QObject):
    """Presentation/I/O shell for wheel HAL (Status + safety Signals)."""

    left_wheel_speed_changed = Signal()
    right_wheel_speed_changed = Signal()
    left_wheel_current_changed = Signal()
    right_wheel_current_changed = Signal()
    left_wheel_position_changed = Signal()
    right_wheel_position_changed = Signal()
    available_changed = Signal()
    enabled_changed = Signal()
    left_error_changed = Signal()
    right_error_changed = Signal()
    left_motor_available_changed = Signal()
    right_motor_available_changed = Signal()
    error_state_changed = Signal(bool, str)

    def __init__(
        self,
        node: Node,
        command_bus: Any | None = None,
        *,
        io_shell: QObject | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        # Shell is the lifetime parent for bridges/watchdog (P2 + P3).
        self._io_shell = io_shell if io_shell is not None else self
        self._notifier = SignalDeviceNotifier(self, parent=self)
        self._telemetry = RosTelemetryBridge(self._apply_status_snapshot, parent=self._io_shell)
        self._hal = WheelHal(
            node,
            notifier=self._notifier,
            post_status=self._telemetry.post,
            command_bus=command_bus,
        )
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
    def hal(self) -> WheelHal:
        return self._hal

    def cleanup(self) -> None:
        if self._watchdog is not None:
            self._watchdog.stop()
        self._hal.cleanup()

    def __getattr__(self, name: str) -> Any:
        # Forward public and test-facing attributes to pure HAL.
        if name in _SHELL_ATTRS:
            raise AttributeError(name)
        try:
            hal = object.__getattribute__(self, "_hal")
        except AttributeError as exc:
            raise AttributeError(name) from exc
        return getattr(hal, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in _SHELL_ATTRS or name.startswith("_Q") or name in {
            "staticMetaObject",
        }:
            return super().__setattr__(name, value)
        # During __init__ before _hal exists, set on self.
        if "_hal" not in self.__dict__:
            return super().__setattr__(name, value)
        if name in self.__dict__ or name in type(self).__dict__:
            return super().__setattr__(name, value)
        # Forward HAL field writes used by tests (e.g. _left_motor_available).
        if hasattr(self._hal, name) or name.startswith("_"):
            setattr(self._hal, name, value)
            return None
        return super().__setattr__(name, value)

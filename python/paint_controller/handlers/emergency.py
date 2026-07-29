#!/usr/bin/env python3

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol, TypedDict, cast

from PySide6.QtCore import QObject, Signal

from paint_controller.utils.constants import HeartbeatStatus

if TYPE_CHECKING:
    from paint_controller.controllers.esp32_valve import ESP32ValveController
    from paint_controller.controllers.teensy import TeensyController
    from paint_controller.controllers.wheel import WheelController
    from paint_controller.controllers.winch import WinchController
    from paint_controller.core.settings import SettingsManager
    from paint_controller.core.state_store import StateStore
    from paint_controller.handlers.safety_coordinator import SafetyCoordinator
    from paint_controller.handlers.steam_deck import SteamDeckHandler


class LoggerProtocol(Protocol):
    def error(self, message: str) -> object: ...


class EmergencyState(TypedDict):
    is_holding: bool
    hold_start_time: float
    overlay_visible: bool
    completed: bool
    duration_target: float
    last_steam_state: bool
    cooldown_start: float
    cooldown_duration: float


class EmergencyButtonHandler(QObject):
    """Handler for emergency button functionality"""

    # Signals
    overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()

    def __init__(
        self,
        steam_deck_handler: SteamDeckHandler,
        winch: WinchController,
        teensy: TeensyController,
        wheel: WheelController,
        show_popup_fn: Callable[..., None] | None = None,
        logger: LoggerProtocol | None = None,
        settings_manager: SettingsManager | None = None,
        state_store: StateStore | None = None,
        safety_coordinator: SafetyCoordinator | None = None,
        esp32_valve: ESP32ValveController | None = None,
    ) -> None:
        super().__init__()

        self.steam_deck_handler = steam_deck_handler
        self._winch = winch
        self._teensy = teensy
        self._wheel = wheel
        self._esp32_valve = esp32_valve
        self._show_popup_fn = show_popup_fn
        self._logger = logger
        self._settings_manager = settings_manager
        self._state_store = state_store
        self._safety_coordinator = safety_coordinator

        duration_target = 1.0
        if self._settings_manager is not None:
            try:
                duration_target = float(self._settings_manager.get("emergency_hold_duration_s", 1.0))
            except Exception:
                duration_target = 1.0

            signal = getattr(self._settings_manager, "emergency_hold_duration_s_changed", None)
            if signal is not None:
                signal.connect(self.set_duration_target)

        # Emergency state tracking
        self._state: EmergencyState = {
            "is_holding": False,
            "hold_start_time": 0.0,
            "overlay_visible": False,
            "completed": False,
            "duration_target": duration_target,
            "last_steam_state": False,
            "cooldown_start": 0.0,  # When emergency was last triggered
            "cooldown_duration": 1.0,  # Minimum time between emergency activations
        }

    def _set_heartbeat_state(self, state: int, *, force: bool = False) -> None:
        if self._safety_coordinator is not None:
            if force:
                self._safety_coordinator.clear_error_state()
            return

        if self._state_store is None:
            return

        current_state = self._state_store.controller_heartbeat_state
        if current_state == HeartbeatStatus.ERROR.value and state != HeartbeatStatus.ERROR.value and not force:
            return
        self._state_store.controller_heartbeat_state = state

    def check_emergency_button(self, button_state: dict[str, bool]) -> None:
        """Check and update emergency button state"""
        steam_pressed = button_state.get("steam", False)
        current_time = time.time()

        # Check if we're in cooldown period
        if self._state["completed"]:
            cooldown_elapsed = current_time - self._state["cooldown_start"]
            if cooldown_elapsed >= self._state["cooldown_duration"]:
                # Cooldown complete, reset the completed flag
                self._state["completed"] = False

        # Handle button press transitions
        if steam_pressed and not self._state["last_steam_state"]:
            # Just pressed - start new hold if not already active and not in cooldown
            if not self._state["is_holding"] and not self._state["completed"]:
                self._state["is_holding"] = True
                self._state["hold_start_time"] = current_time

        elif not steam_pressed and self._state["last_steam_state"]:
            # Just released - cancel if not completed
            if self._state["is_holding"] and not self._state["completed"]:
                self._cancel_emergency()

        # If we're holding and haven't completed
        if steam_pressed and self._state["is_holding"] and not self._state["completed"]:
            hold_duration = current_time - self._state["hold_start_time"]

            # Show overlay if not already visible
            if not self._state["overlay_visible"]:
                self._state["overlay_visible"] = True

            # Update overlay progress
            self.overlay_changed.emit(True, hold_duration, self._state["duration_target"])

            # Check if we've held long enough
            if hold_duration >= self._state["duration_target"]:
                self._state["completed"] = True
                self._state["cooldown_start"] = current_time  # Start cooldown
                self._trigger_emergency(hold_duration)

        # Update last state
        self._state["last_steam_state"] = steam_pressed

    def _trigger_emergency(self, duration: float) -> None:
        """Trigger the emergency action"""
        # Immediately hide the overlay and stop counting
        try:
            self._state["overlay_visible"] = False
            self._state["is_holding"] = False
            self.overlay_changed.emit(False, 0, 0)

            if self._safety_coordinator is not None:
                self._safety_coordinator.halt_all_effectors(
                    "Emergency activated by user",
                    heartbeat_state=HeartbeatStatus.ERROR,
                )
            else:
                self._winch.command_speed_rpm(0)
                self._teensy.setSprayTrigger(1000)
                self._wheel.emergency_stop()
                if self._esp32_valve is not None:
                    self._esp32_valve.setValveTurn(0.0)
                self._set_heartbeat_state(HeartbeatStatus.ERROR.value)

            # Show emergency popup
            if self._show_popup_fn:
                self._show_popup_fn("EMERGENCY", "Emergency stop activated!", "error", 1000)

            # Log the event
            if self._logger:
                self._logger.error(f"Emergency activated by user at {time.time()}")

            # Emit signal for other components
            self.emergency_triggered.emit()
        except Exception as e:
            if self._logger:
                self._logger.error(f"Error during emergency trigger: {e}")

    def _cancel_emergency(self) -> None:
        """Cancel the emergency sequence"""
        # Reset holding state
        self._state["is_holding"] = False

        # Hide overlay immediately
        if self._state["overlay_visible"]:
            self._state["overlay_visible"] = False
            self.overlay_changed.emit(False, 0, 0)

    def reset_state(self, force: bool = False) -> None:
        """Reset the emergency state to initial values"""
        # If not forcing, respect cooldown
        if not force and self._state["completed"]:
            current_time = time.time()
            cooldown_elapsed = current_time - self._state["cooldown_start"]
            if cooldown_elapsed < self._state["cooldown_duration"]:
                # Still in cooldown, don't reset completed
                self._state["is_holding"] = False
                self._state["overlay_visible"] = False
                return

        # Full reset
        self._state = {
            "is_holding": False,
            "hold_start_time": 0.0,
            "overlay_visible": False,
            "completed": False,
            "duration_target": self._state["duration_target"],  # Preserve duration
            "last_steam_state": False,
            "cooldown_start": 0.0,
            "cooldown_duration": self._state["cooldown_duration"],  # Preserve cooldown
        }
        self._set_heartbeat_state(HeartbeatStatus.IDLE.value, force=True)

    def set_duration_target(self, duration: float) -> None:
        """Set the required hold duration for emergency activation"""
        self._state["duration_target"] = max(0.2, min(2.0, float(duration)))

    def set_cooldown_duration(self, duration: float) -> None:
        """Set the cooldown period between emergency activations"""
        self._state["cooldown_duration"] = duration

    def get_state(self) -> dict[str, bool | float]:
        """Get current emergency state (for debugging/monitoring)"""
        state = cast(dict[str, bool | float], dict(self._state))
        if state["completed"]:
            current_time = time.time()
            cooldown_start = float(state["cooldown_start"])
            cooldown_duration = float(state["cooldown_duration"])
            cooldown_elapsed = current_time - cooldown_start
            state["cooldown_remaining"] = max(0.0, cooldown_duration - cooldown_elapsed)
        return state

    def force_reset(self) -> None:
        """Force reset the emergency state, bypassing cooldown"""
        self.reset_state(force=True)

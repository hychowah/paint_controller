"""Hold-to-confirm app exit on the Steam Deck Switch button."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypedDict

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from paint_controller.utils.constants import DEFAULT_EXIT_HOLD_DURATION_S


class ExitHoldState(TypedDict):
    is_holding: bool
    hold_start_time: float
    overlay_visible: bool
    completed: bool
    duration_target: float
    last_switch_state: bool


class ExitHoldHandler(QObject):
    """Require a sustained Switch hold before quitting the application.

    Mirrors the emergency hold pattern: rising edge starts, continuous progress
    while held, release cancels, threshold completion requests a graceful quit.
    """

    overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    exit_triggered = Signal()

    def __init__(
        self,
        *,
        duration_target_s: float = DEFAULT_EXIT_HOLD_DURATION_S,
        quit_fn: Callable[[], None] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._quit_fn = quit_fn
        self._state: ExitHoldState = {
            "is_holding": False,
            "hold_start_time": 0.0,
            "overlay_visible": False,
            "completed": False,
            "duration_target": float(duration_target_s),
            "last_switch_state": False,
        }

    def check_exit_button(self, button_state: dict[str, bool]) -> None:
        """Poll Switch button state and update hold progress / quit request."""
        switch_pressed = bool(button_state.get("switch", False))
        current_time = time.time()

        if self._state["completed"]:
            # Stay latched until button is released so a held Switch cannot re-fire.
            if not switch_pressed:
                self._state["completed"] = False
            self._state["last_switch_state"] = switch_pressed
            return

        if switch_pressed and not self._state["last_switch_state"]:
            if not self._state["is_holding"]:
                self._state["is_holding"] = True
                self._state["hold_start_time"] = current_time

        elif not switch_pressed and self._state["last_switch_state"]:
            if self._state["is_holding"]:
                self._cancel_hold()

        if switch_pressed and self._state["is_holding"] and not self._state["completed"]:
            hold_duration = current_time - self._state["hold_start_time"]

            if not self._state["overlay_visible"]:
                self._state["overlay_visible"] = True

            self.overlay_changed.emit(True, hold_duration, self._state["duration_target"])

            if hold_duration >= self._state["duration_target"]:
                self._state["completed"] = True
                self._trigger_exit()

        self._state["last_switch_state"] = switch_pressed

    def _trigger_exit(self) -> None:
        self._state["overlay_visible"] = False
        self._state["is_holding"] = False
        self.overlay_changed.emit(False, 0.0, 0.0)
        self.exit_triggered.emit()
        self._request_quit()

    def _cancel_hold(self) -> None:
        self._state["is_holding"] = False
        if self._state["overlay_visible"]:
            self._state["overlay_visible"] = False
            self.overlay_changed.emit(False, 0.0, 0.0)

    def _request_quit(self) -> None:
        if self._quit_fn is not None:
            self._quit_fn()
            return
        app = QApplication.instance()
        if app is not None:
            app.quit()

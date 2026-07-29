"""Backend session state shared across handlers (not a general UI SSoT)."""

# pyright: reportRedeclaration=false

from __future__ import annotations

import threading

from PySide6.QtCore import Property, QObject, Signal

from paint_controller.utils.constants import HeartbeatStatus


class StateStore(QObject):
    """Holds a small set of cross-handler session facts.

    Live surface: ``control_mode``, ``display_message``, ``controller_heartbeat_state``.
    Stick/control HUD labels live on ``ControlProcessor`` / selection models — not here.

    Thread-safe: all property access is guarded by ``_lock``.
    Signals are emitted **outside** the lock to avoid deadlocks
    (see KNOWLEDGE.md — Thread Lock + Signal Pattern).
    """

    control_mode_changed = Signal(str)
    display_message_changed = Signal(str)
    controller_heartbeat_state_changed = Signal(int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._lock = threading.Lock()
        self._control_mode = "base"
        self._display_message = ""
        self._controller_heartbeat_state = int(HeartbeatStatus.IDLE)

    # --- control_mode ---
    @Property(str, notify=control_mode_changed)
    def control_mode(self) -> str:
        with self._lock:
            return self._control_mode

    @control_mode.setter
    def control_mode(self, mode: str) -> None:
        with self._lock:
            if self._control_mode == mode:
                return
            self._control_mode = mode
        self.control_mode_changed.emit(mode)

    # --- display_message ---
    @Property(str, notify=display_message_changed)
    def display_message(self) -> str:
        with self._lock:
            return self._display_message

    @display_message.setter
    def display_message(self, message: str) -> None:
        with self._lock:
            if self._display_message == message:
                return
            self._display_message = message
        self.display_message_changed.emit(message)

    # --- controller_heartbeat_state ---
    @Property(int, notify=controller_heartbeat_state_changed)
    def controller_heartbeat_state(self) -> int:
        with self._lock:
            return self._controller_heartbeat_state

    @controller_heartbeat_state.setter
    def controller_heartbeat_state(self, value: int) -> None:
        with self._lock:
            if self._controller_heartbeat_state == value:
                return
            self._controller_heartbeat_state = value
        self.controller_heartbeat_state_changed.emit(value)

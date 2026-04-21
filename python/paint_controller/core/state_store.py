"""Shared mutable state that multiple components read/write."""

import threading
from PySide6.QtCore import QObject, Signal, Property

from paint_controller.utils.constants import HeartbeatStatus


class StateStore(QObject):
    """Holds application state shared across controllers and UI.

    Thread-safe: all property access is guarded by ``_lock``.
    Signals are emitted **outside** the lock to avoid deadlocks
    (see KNOWLEDGE.md — Thread Lock + Signal Pattern).
    """

    control_mode_changed = Signal(str)
    display_message_changed = Signal(str)
    left_joystick_control_changed = Signal(str)
    right_joystick_control_changed = Signal(str)
    left_control_info_changed = Signal(str, str)   # mode, value
    right_control_info_changed = Signal(str, str)   # mode, value
    controller_heartbeat_state_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._lock = threading.Lock()
        self._control_mode = "base"
        self._display_message = ""
        self._left_joystick_control = "None"
        self._right_joystick_control = "None"
        self._left_control_mode = "None"
        self._left_control_value = ""
        self._right_control_mode = "None"
        self._right_control_value = ""
        self._controller_heartbeat_state = int(HeartbeatStatus.IDLE)

    # --- control_mode ---
    @Property(str, notify=control_mode_changed)
    def control_mode(self):
        with self._lock:
            return self._control_mode

    @control_mode.setter
    def control_mode(self, mode):
        with self._lock:
            if self._control_mode == mode:
                return
            self._control_mode = mode
        self.control_mode_changed.emit(mode)

    # --- display_message ---
    @Property(str, notify=display_message_changed)
    def display_message(self):
        with self._lock:
            return self._display_message

    @display_message.setter
    def display_message(self, message):
        with self._lock:
            if self._display_message == message:
                return
            self._display_message = message
        self.display_message_changed.emit(message)

    # --- left_joystick_control ---
    @Property(str, notify=left_joystick_control_changed)
    def left_joystick_control(self):
        with self._lock:
            return self._left_joystick_control

    @left_joystick_control.setter
    def left_joystick_control(self, mode):
        with self._lock:
            if self._left_joystick_control == mode:
                return
            self._left_joystick_control = mode
        self.left_joystick_control_changed.emit(mode)

    # --- right_joystick_control ---
    @Property(str, notify=right_joystick_control_changed)
    def right_joystick_control(self):
        with self._lock:
            return self._right_joystick_control

    @right_joystick_control.setter
    def right_joystick_control(self, mode):
        with self._lock:
            if self._right_joystick_control == mode:
                return
            self._right_joystick_control = mode
        self.right_joystick_control_changed.emit(mode)

    # --- left_control_mode ---
    @Property(str, notify=left_control_info_changed)
    def left_control_mode(self):
        with self._lock:
            return self._left_control_mode

    @left_control_mode.setter
    def left_control_mode(self, mode):
        with self._lock:
            if self._left_control_mode == mode:
                return
            self._left_control_mode = mode
            value = self._left_control_value
        self.left_control_info_changed.emit(mode, value)

    # --- left_control_value ---
    @Property(str, notify=left_control_info_changed)
    def left_control_value(self):
        with self._lock:
            return self._left_control_value

    @left_control_value.setter
    def left_control_value(self, value):
        with self._lock:
            if self._left_control_value == value:
                return
            self._left_control_value = value
            mode = self._left_control_mode
        self.left_control_info_changed.emit(mode, value)

    # --- right_control_mode ---
    @Property(str, notify=right_control_info_changed)
    def right_control_mode(self):
        with self._lock:
            return self._right_control_mode

    @right_control_mode.setter
    def right_control_mode(self, mode):
        with self._lock:
            if self._right_control_mode == mode:
                return
            self._right_control_mode = mode
            value = self._right_control_value
        self.right_control_info_changed.emit(mode, value)

    # --- right_control_value ---
    @Property(str, notify=right_control_info_changed)
    def right_control_value(self):
        with self._lock:
            return self._right_control_value

    @right_control_value.setter
    def right_control_value(self, value):
        with self._lock:
            if self._right_control_value == value:
                return
            self._right_control_value = value
            mode = self._right_control_mode
        self.right_control_info_changed.emit(mode, value)

    # --- controller_heartbeat_state ---
    @Property(int, notify=controller_heartbeat_state_changed)
    def controller_heartbeat_state(self):
        with self._lock:
            return self._controller_heartbeat_state

    @controller_heartbeat_state.setter
    def controller_heartbeat_state(self, value):
        with self._lock:
            if self._controller_heartbeat_state == value:
                return
            self._controller_heartbeat_state = value
        self.controller_heartbeat_state_changed.emit(value)

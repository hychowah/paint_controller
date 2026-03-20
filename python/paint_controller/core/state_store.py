"""Shared mutable state that multiple components read/write."""

from PySide6.QtCore import QObject, Signal, Property


class StateStore(QObject):
    """Holds application state shared across controllers and UI."""

    control_mode_changed = Signal(str)
    display_message_changed = Signal(str)
    left_joystick_control_changed = Signal(str)
    right_joystick_control_changed = Signal(str)
    left_control_info_changed = Signal(str, str)   # mode, value
    right_control_info_changed = Signal(str, str)   # mode, value

    def __init__(self, parent=None):
        super().__init__(parent)
        self._control_mode = "base"
        self._display_message = ""
        self._left_joystick_control = "None"
        self._right_joystick_control = "None"
        self._left_control_mode = "None"
        self._left_control_value = ""
        self._right_control_mode = "None"
        self._right_control_value = ""

    # --- control_mode ---
    @Property(str, notify=control_mode_changed)
    def control_mode(self):
        return self._control_mode

    @control_mode.setter
    def control_mode(self, mode):
        if self._control_mode != mode:
            self._control_mode = mode
            self.control_mode_changed.emit(mode)

    # --- display_message ---
    @Property(str, notify=display_message_changed)
    def display_message(self):
        return self._display_message

    @display_message.setter
    def display_message(self, message):
        if self._display_message != message:
            self._display_message = message
            self.display_message_changed.emit(message)

    # --- left_joystick_control ---
    @Property(str, notify=left_joystick_control_changed)
    def left_joystick_control(self):
        return self._left_joystick_control

    @left_joystick_control.setter
    def left_joystick_control(self, mode):
        if self._left_joystick_control != mode:
            self._left_joystick_control = mode
            self.left_joystick_control_changed.emit(mode)

    # --- right_joystick_control ---
    @Property(str, notify=right_joystick_control_changed)
    def right_joystick_control(self):
        return self._right_joystick_control

    @right_joystick_control.setter
    def right_joystick_control(self, mode):
        if self._right_joystick_control != mode:
            self._right_joystick_control = mode
            self.right_joystick_control_changed.emit(mode)

    # --- left_control_mode ---
    @Property(str, notify=left_control_info_changed)
    def left_control_mode(self):
        return self._left_control_mode

    @left_control_mode.setter
    def left_control_mode(self, mode):
        if self._left_control_mode != mode:
            self._left_control_mode = mode
            self.left_control_info_changed.emit(mode, self._left_control_value)

    # --- left_control_value ---
    @Property(str, notify=left_control_info_changed)
    def left_control_value(self):
        return self._left_control_value

    @left_control_value.setter
    def left_control_value(self, value):
        if self._left_control_value != value:
            self._left_control_value = value
            self.left_control_info_changed.emit(self._left_control_mode, value)

    # --- right_control_mode ---
    @Property(str, notify=right_control_info_changed)
    def right_control_mode(self):
        return self._right_control_mode

    @right_control_mode.setter
    def right_control_mode(self, mode):
        if self._right_control_mode != mode:
            self._right_control_mode = mode
            self.right_control_info_changed.emit(mode, self._right_control_value)

    # --- right_control_value ---
    @Property(str, notify=right_control_info_changed)
    def right_control_value(self):
        return self._right_control_value

    @right_control_value.setter
    def right_control_value(self, value):
        if self._right_control_value != value:
            self._right_control_value = value
            self.right_control_info_changed.emit(self._right_control_mode, value)

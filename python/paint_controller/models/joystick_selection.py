from __future__ import annotations

from PySide6.QtCore import QObject, Property, Signal, Slot


class JoystickSelectionModel(QObject):
    """Own committed and temporary joystick control selections."""

    committed_left_index_changed = Signal(int)
    committed_right_index_changed = Signal(int)
    temporary_left_index_changed = Signal(int)
    temporary_right_index_changed = Signal(int)
    control_options_changed = Signal(list)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._control_options = [
            "None",
            "Winch Speed",
            "Track Control Left",
            "Track Control Right",
            "Wheel Travel Left",
            "Wheel Travel Right",
            "EF arm",
            "EF top rail",
            "EF prop pwm",
            "EF prop joint",
            "EF spray trigger",
            "EF spray pitch",
            "EF Yaw Angle",
            "EF Force",
        ]
        self._left_selected_index = 0
        self._right_selected_index = 0
        self._temp_left_index = 0
        self._temp_right_index = 0

    @Property(list, notify=control_options_changed)
    def control_options(self) -> list[str]:
        return self._control_options

    def display_left_index(self, show_overlay: bool) -> int:
        return self._temp_left_index if show_overlay else self._left_selected_index

    def display_right_index(self, show_overlay: bool) -> int:
        return self._temp_right_index if show_overlay else self._right_selected_index

    def initialize_temporary_selection(self) -> None:
        self._set_temporary_left_index(self._left_selected_index)
        self._set_temporary_right_index(self._right_selected_index)

    def commit_temporary_selection(self) -> None:
        self._set_committed_left_index(self._temp_left_index)
        self._set_committed_right_index(self._temp_right_index)

    def reset_temporary_selection(self, left_index: int = 0, right_index: int = 0) -> None:
        self._set_temporary_left_index(left_index)
        self._set_temporary_right_index(right_index)

    def _can_select_option(self, active_menu: str, index: int) -> bool:
        if index in (2, 3):
            return True

        if active_menu == "left":
            return index == 0 or index != self._temp_right_index
        return index == 0 or index != self._temp_left_index

    def move_selection_up(self, active_menu: str) -> bool:
        current_index = self._temp_left_index if active_menu == "left" else self._temp_right_index
        for index in range(current_index - 1, -1, -1):
            if self._can_select_option(active_menu, index):
                if active_menu == "left":
                    self._set_temporary_left_index(index)
                else:
                    self._set_temporary_right_index(index)
                return True
        return False

    def move_selection_down(self, active_menu: str) -> bool:
        current_index = self._temp_left_index if active_menu == "left" else self._temp_right_index
        for index in range(current_index + 1, len(self._control_options)):
            if self._can_select_option(active_menu, index):
                if active_menu == "left":
                    self._set_temporary_left_index(index)
                else:
                    self._set_temporary_right_index(index)
                return True
        return False

    def move_selection_to_first(self, active_menu: str) -> None:
        if active_menu == "left":
            self._set_temporary_left_index(0)
        else:
            self._set_temporary_right_index(0)

    def move_selection_to_last(self, active_menu: str) -> bool:
        for index in range(len(self._control_options) - 1, -1, -1):
            if self._can_select_option(active_menu, index):
                if active_menu == "left":
                    self._set_temporary_left_index(index)
                else:
                    self._set_temporary_right_index(index)
                return True
        return False

    @Slot(result=str)
    def get_left_selected_option(self) -> str:
        return self._control_options[self._left_selected_index]

    @Slot(result=str)
    def get_right_selected_option(self) -> str:
        return self._control_options[self._right_selected_index]

    @Slot(str, str)
    def set_joystick_controls(self, left_control: str, right_control: str) -> None:
        left_index = self._control_options.index(left_control) if left_control in self._control_options else 0
        right_index = self._control_options.index(right_control) if right_control in self._control_options else 0
        self._set_committed_left_index(left_index)
        self._set_committed_right_index(right_index)

    @Slot(result=list)
    def get_current_joystick_controls(self) -> list[str]:
        return [self.get_left_selected_option(), self.get_right_selected_option()]

    @Slot()
    def avoidAutoRunOverwrite(self) -> None:
        if self._left_selected_index in (1, 8, 9):
            self._set_committed_left_index(0)

        if self._right_selected_index in (1, 8, 9):
            self._set_committed_right_index(0)

        self.reset_temporary_selection()

    def _set_committed_left_index(self, index: int) -> None:
        if self._left_selected_index == index:
            return
        self._left_selected_index = index
        self.committed_left_index_changed.emit(index)

    def _set_committed_right_index(self, index: int) -> None:
        if self._right_selected_index == index:
            return
        self._right_selected_index = index
        self.committed_right_index_changed.emit(index)

    def _set_temporary_left_index(self, index: int) -> None:
        if self._temp_left_index == index:
            return
        self._temp_left_index = index
        self.temporary_left_index_changed.emit(index)

    def _set_temporary_right_index(self, index: int) -> None:
        if self._temp_right_index == index:
            return
        self._temp_right_index = index
        self.temporary_right_index_changed.emit(index)
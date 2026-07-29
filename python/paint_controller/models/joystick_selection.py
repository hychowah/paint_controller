from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot


class JoystickSelectionModel(QObject):
    """Own committed and temporary joystick control selections."""

    committed_left_index_changed = Signal(int)
    committed_right_index_changed = Signal(int)
    temporary_left_index_changed = Signal(int)
    temporary_right_index_changed = Signal(int)
    control_options_changed = Signal(list)

    # Compact display labels for the small ControlInfoPanel surfaces.
    # Full canonical names remain in control_options for the selection menu.
    _DISPLAY_NAMES: dict[str, str] = {
        "None": "None",
        "Winch Speed": "Winch",
        "Track Control Left": "Track Left",
        "Track Control Right": "Track Right",
        "Wheel Travel Left": "Wheel Left",
        "Wheel Travel Right": "Wheel Right",
        "EF arm": "EF Arm",
        "EF top rail": "Top Rail",
        "EF prop pwm": "Prop PWM",
        "EF prop joint": "Prop Joint",
        "EF spray trigger": "Spray Trigger",
        "EF spray pitch": "Spray Pitch",
        "EF Yaw Angle": "Yaw",
        "EF Force": "EF Force",
    }

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
        self._remembered_controls_by_mode: dict[str, tuple[str, str]] = {}

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

    def _can_select_option(self, active_menu: str, index: int, *, other_index: int | None = None) -> bool:
        if index in (2, 3):
            return True

        if other_index is None:
            other_index = self._temp_right_index if active_menu == "left" else self._temp_left_index
        return index == 0 or index != other_index

    def select_left_control(self, index: int) -> bool:
        """Commit a left control selection if it is allowed.

        Validation is performed against the committed right selection so that
        direct touch selection behaves correctly even when the overlay is not
        using temporary preview.
        """
        if not self._can_select_option("left", index, other_index=self._right_selected_index):
            return False
        self._set_committed_left_index(index)
        return True

    def select_right_control(self, index: int) -> bool:
        """Commit a right control selection if it is allowed.

        Validation is performed against the committed left selection so that
        direct touch selection behaves correctly even when the overlay is not
        using temporary preview.
        """
        if not self._can_select_option("right", index, other_index=self._left_selected_index):
            return False
        self._set_committed_right_index(index)
        return True

    def set_temporary_index(self, active_menu: str, index: int) -> bool:
        """Set the temporary selection index if it is allowed.

        This is used by touch selection so that hide_menu() can commit the
        temporary index through the same path as button navigation.
        """
        if not self._can_select_option(active_menu, index):
            return False
        if active_menu == "left":
            self._set_temporary_left_index(index)
        else:
            self._set_temporary_right_index(index)
        return True

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

    @Slot(str, result=str)
    def display_name_for_option(self, option: str) -> str:
        """Return a compact display label for a canonical control option."""
        return self._DISPLAY_NAMES.get(option, option)

    def remember_current_controls(self, mode: str) -> None:
        self._remembered_controls_by_mode[mode] = (
            self.get_left_selected_option(),
            self.get_right_selected_option(),
        )

    def get_remembered_controls(self, mode: str) -> tuple[str, str] | None:
        return self._remembered_controls_by_mode.get(mode)

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

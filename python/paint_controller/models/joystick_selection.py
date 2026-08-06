from __future__ import annotations

from PySide6.QtCore import Property, QObject, Signal, Slot

from paint_controller.handlers.policy import teleop_modes


class JoystickSelectionModel(QObject):
    """Own committed and temporary joystick control selections.

    Menu labels, display names, and selection policy sets come from the teleop
    catalog (``teleop_modes``) — not hard-coded indices or parallel lists.
    """

    committed_left_index_changed = Signal(int)
    committed_right_index_changed = Signal(int)
    temporary_left_index_changed = Signal(int)
    temporary_right_index_changed = Signal(int)
    control_options_changed = Signal(list)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._control_options = teleop_modes.menu_labels()
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

    def _label_at(self, index: int) -> str:
        if 0 <= index < len(self._control_options):
            return self._control_options[index]
        return ""

    def _is_valid_index(self, index: int) -> bool:
        return 0 <= index < len(self._control_options)

    def _is_exclusive_conflict(self, index: int, other_index: int) -> bool:
        """True when both sticks would own the same exclusive mode.

        Track modes may share a label on both sticks. ``None`` never conflicts.
        Other modes are exclusive: selecting them on one stick clears the other.
        """
        label = self._label_at(index)
        if index == 0 or label == "None":
            return False
        if label in teleop_modes.duplicate_allowed_labels():
            return False
        return index == other_index

    def _assign_side(self, side: str, index: int, *, temporary: bool) -> bool:
        """Assign one stick; if exclusive conflict, clear the other stick to None."""
        if not self._is_valid_index(index):
            return False

        if temporary:
            if side == "left":
                self._set_temporary_left_index(index)
                if self._is_exclusive_conflict(index, self._temp_right_index):
                    self._set_temporary_right_index(0)
            else:
                self._set_temporary_right_index(index)
                if self._is_exclusive_conflict(index, self._temp_left_index):
                    self._set_temporary_left_index(0)
        else:
            if side == "left":
                self._set_committed_left_index(index)
                if self._is_exclusive_conflict(index, self._right_selected_index):
                    self._set_committed_right_index(0)
            else:
                self._set_committed_right_index(index)
                if self._is_exclusive_conflict(index, self._left_selected_index):
                    self._set_committed_left_index(0)
        return True

    def select_left_control(self, index: int) -> bool:
        """Commit a left control selection (clears right if exclusive conflict)."""
        return self._assign_side("left", index, temporary=False)

    def select_right_control(self, index: int) -> bool:
        """Commit a right control selection (clears left if exclusive conflict)."""
        return self._assign_side("right", index, temporary=False)

    def set_temporary_index(self, active_menu: str, index: int) -> bool:
        """Set the temporary selection index for the active menu.

        Used by touch selection so hide_menu() can commit through the same
        path as button navigation. Exclusive conflicts clear the other temp stick.
        """
        if active_menu not in ("left", "right"):
            return False
        return self._assign_side(active_menu, index, temporary=True)

    def move_selection_up(self, active_menu: str) -> bool:
        current_index = self._temp_left_index if active_menu == "left" else self._temp_right_index
        if current_index <= 0:
            return False
        return self._assign_side(active_menu, current_index - 1, temporary=True)

    def move_selection_down(self, active_menu: str) -> bool:
        current_index = self._temp_left_index if active_menu == "left" else self._temp_right_index
        if current_index >= len(self._control_options) - 1:
            return False
        return self._assign_side(active_menu, current_index + 1, temporary=True)

    def move_selection_to_first(self, active_menu: str) -> None:
        self._assign_side(active_menu, 0, temporary=True)

    def move_selection_to_last(self, active_menu: str) -> bool:
        if not self._control_options:
            return False
        return self._assign_side(active_menu, len(self._control_options) - 1, temporary=True)

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
        return teleop_modes.display_name(option)

    def remember_current_controls(self, mode: str) -> None:
        self._remembered_controls_by_mode[mode] = (
            self.get_left_selected_option(),
            self.get_right_selected_option(),
        )

    def get_remembered_controls(self, mode: str) -> tuple[str, str] | None:
        return self._remembered_controls_by_mode.get(mode)

    def transition_controls(self, leaving_mode: str, entering_mode: str) -> None:
        """Remember sticks for the mode being left; restore or apply defaults for the mode entered.

        Owns the per-mode stick memory decision. Session ``control_mode`` and
        hardware side-effects (video, winch reset) stay with the orchestrator.
        """
        self.remember_current_controls(leaving_mode)
        remembered = self.get_remembered_controls(entering_mode)
        if remembered is None:
            remembered = teleop_modes.default_stick_pair(entering_mode)
        left_control, right_control = remembered
        self.set_joystick_controls(left_control, right_control)

    @Slot()
    def avoidAutoRunOverwrite(self) -> None:
        clear = teleop_modes.autorun_clear_labels()
        if self.get_left_selected_option() in clear:
            self._set_committed_left_index(0)

        if self.get_right_selected_option() in clear:
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

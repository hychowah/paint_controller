#!/usr/bin/env python3

from PySide6.QtCore import QTimer, QObject, Slot, Property, Signal
import logging

from paint_controller.models.joystick_selection import JoystickSelectionModel

logger = logging.getLogger(__name__)


class OverlayController(QObject):
    """Controller class for managing dual joystick menu state"""
    
    leftSelectedIndexChanged = Signal(int)
    rightSelectedIndexChanged = Signal(int)
    overlayChanged = Signal(bool)
    controlOptionsChanged = Signal(list)
    activeMenuChanged = Signal(str)
    
    def __init__(self, selection_model: JoystickSelectionModel, teensy=None):
        super().__init__()
        self._selection_model = selection_model
        self._teensy = teensy
        self._show_overlay = False
        self._active_menu = ""  # Start with no active menu

        self._selection_model.committed_left_index_changed.connect(self._on_committed_left_index_changed)
        self._selection_model.committed_right_index_changed.connect(self._on_committed_right_index_changed)
        self._selection_model.temporary_left_index_changed.connect(self._on_temporary_left_index_changed)
        self._selection_model.temporary_right_index_changed.connect(self._on_temporary_right_index_changed)
        
        # Initialize timer
        self._input_timer = QTimer()
        self._input_timer.setInterval(100)
        self._input_timer.timeout.connect(self._reset_input_lock)
        self._input_locked = False

    def _on_committed_left_index_changed(self, index: int) -> None:
        if not self._show_overlay:
            self.leftSelectedIndexChanged.emit(index)

    def _on_committed_right_index_changed(self, index: int) -> None:
        if not self._show_overlay:
            self.rightSelectedIndexChanged.emit(index)

    def _on_temporary_left_index_changed(self, index: int) -> None:
        if self._show_overlay:
            self.leftSelectedIndexChanged.emit(index)

    def _on_temporary_right_index_changed(self, index: int) -> None:
        if self._show_overlay:
            self.rightSelectedIndexChanged.emit(index)

    @Property(list, notify=controlOptionsChanged)
    def control_options(self):
        return self._selection_model.control_options
        
    @Property(int, notify=leftSelectedIndexChanged)
    def left_selected_index(self):
        return self._selection_model.display_left_index(self._show_overlay)
        
    @Property(int, notify=rightSelectedIndexChanged)
    def right_selected_index(self):
        return self._selection_model.display_right_index(self._show_overlay)
        
    @Property(bool, notify=overlayChanged)
    def show_overlay(self):
        return self._show_overlay
        
    @Property(str, notify=activeMenuChanged)
    def active_menu(self):
        return self._active_menu

    def _reset_input_lock(self):
        self._input_locked = False
        self._input_timer.stop()

    def _activate_menu(self, menu: str) -> None:
        if menu in ["left", "right", "system"]:
            self._active_menu = menu
            self.activeMenuChanged.emit(menu)

    def _toggle_menu(self, menu: str) -> None:
        self._activate_menu(menu)

        if self._show_overlay:
            self.hide_menu()
            return

        if menu in ["left", "right"]:
            self._selection_model.initialize_temporary_selection()

        self.show_menu()
    
    @Slot()
    def toggle_system_menu(self):
        """Toggle the system menu"""
        self._toggle_menu("system")
    
    @Slot()
    def toggle_left_menu(self):
        """Toggle the left joystick menu"""
        self._toggle_menu("left")

    @Slot()
    def toggle_right_menu(self):
        """Toggle the right joystick menu"""
        self._toggle_menu("right")

    @Slot(result=bool)
    def is_showing_menu(self):
        """Check if any menu is showing"""
        return self._show_overlay
    
    @Slot()
    def show_menu(self):
        """Show the menu overlay"""
        self._show_overlay = True
        self.overlayChanged.emit(True)
    
    @Slot()
    def hide_menu(self):
        """Hide the menu overlay and apply selections"""
        if self._show_overlay:
            # Apply temporary selections to actual selections if applicable
            if self._active_menu in ["left", "right"]:
                self._selection_model.commit_temporary_selection()
        if self.get_left_selected_option() == "EF Yaw Angle" or self.get_right_selected_option() == "EF Yaw Angle":
            # Reset the temporary indices after applying a yaw selection.
            self._selection_model.reset_temporary_selection()
        # Hide the overlay but keep the active_menu unchanged
        self._show_overlay = False
        self.overlayChanged.emit(False)
        if self._active_menu in ["left", "right"]:
            self.leftSelectedIndexChanged.emit(self.left_selected_index)
            self.rightSelectedIndexChanged.emit(self.right_selected_index)

    @Slot()
    def move_up(self):
        """Move selection up in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
        self._selection_model.move_selection_up(self._active_menu)
                
        self._input_locked = True
        self._input_timer.start()
            
    @Slot()
    def move_down(self):
        """Move selection down in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
        self._selection_model.move_selection_down(self._active_menu)
                
        self._input_locked = True
        self._input_timer.start()

    @Slot(result=str)
    def get_left_selected_option(self):
        return self._selection_model.get_left_selected_option()
    
    @Slot(result=str)
    def get_right_selected_option(self):
        return self._selection_model.get_right_selected_option()
    
    @Slot()
    def move_to_first(self):
        """Move selection to the first available item in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
        self._selection_model.move_selection_to_first(self._active_menu)
                
        self._input_locked = True
        self._input_timer.start()

    @Slot()
    def move_to_last(self):
        """Move selection to the last available item in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
        self._selection_model.move_selection_to_last(self._active_menu)
                
        self._input_locked = True
        self._input_timer.start()


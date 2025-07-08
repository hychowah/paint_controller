#!/usr/bin/env python3

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from UITeensyController import TeensyController
from UIControlProcessor import ControlProcessor


class OverlayController(QObject):
    """Controller class for managing dual joystick menu state"""
    
    leftSelectedIndexChanged = Signal(int)
    rightSelectedIndexChanged = Signal(int)
    overlayChanged = Signal(bool)
    controlOptionsChanged = Signal(list)
    activeMenuChanged = Signal(str)
    
    def __init__(self, robotController):
        super().__init__()
        self.robot = robotController

        self._control_options = [
            "None",
            "Winch Speed",
            "Left Wheel Speed",
            "Right Wheel Speed",
            "EF arm",
            "EF top rail",
            "EF prop pwm",
            "EF prop joint",
            "EF spray trigger",
            "EF spray gimbal",
            "EF Yaw Angle",
            "EF Force"
        ]

        # Current active indices
        self._left_selected_index = 0
        self._right_selected_index = 0
        
        # Temporary indices for selection in overlay
        self._temp_left_index = 0
        self._temp_right_index = 0
        
        self._max_index = len(self._control_options) - 1
        self._show_overlay = False
        self._active_menu = ""  # Start with no active menu
        
        # Initialize timer
        self._input_timer = QTimer()
        self._input_timer.setInterval(100)
        self._input_timer.timeout.connect(self._reset_input_lock)
        self._input_locked = False

    @Property(list, notify=controlOptionsChanged)
    def control_options(self):
        return self._control_options
        
    @Property(int, notify=leftSelectedIndexChanged)
    def left_selected_index(self):
        # Return temporary index when overlay is shown
        return self._temp_left_index if self._show_overlay else self._left_selected_index
        
    @Property(int, notify=rightSelectedIndexChanged)
    def right_selected_index(self):
        # Return temporary index when overlay is shown
        return self._temp_right_index if self._show_overlay else self._right_selected_index
        
    @Property(bool, notify=overlayChanged)
    def show_overlay(self):
        return self._show_overlay
        
    @Property(str, notify=activeMenuChanged)
    def active_menu(self):
        return self._active_menu

    def _reset_input_lock(self):
        self._input_locked = False
        self._input_timer.stop()
    
    @Slot(str)
    def set_active_menu(self, menu):
        """Set active menu and show overlay"""
        if menu in ["left", "right", "power"]:
            self._active_menu = menu
            self.activeMenuChanged.emit(menu)

    @Slot()
    def toggle_power_menu(self):
        """Toggle the power menu"""
        # Always set the active menu first
        self._active_menu = "power"
        self.activeMenuChanged.emit("power")
        
        # Then toggle visibility
        if self._show_overlay:
            self.hide_menu()
        else:
            self.show_menu()
    
    @Slot()
    def toggle_left_menu(self):
        """Toggle the left joystick menu"""
        self._active_menu = "left"
        self.activeMenuChanged.emit("left")
        
        if self._show_overlay:
            self.hide_menu()
        else:
            # Initialize temporary selection with current selection
            self._temp_left_index = self._left_selected_index
            self._temp_right_index = self._right_selected_index
            self.show_menu()

    @Slot()
    def toggle_right_menu(self):
        """Toggle the right joystick menu"""
        self._active_menu = "right"
        self.activeMenuChanged.emit("right")
        
        if self._show_overlay:
            self.hide_menu()
        else:
            # Initialize temporary selection with current selection
            self._temp_left_index = self._left_selected_index
            self._temp_right_index = self._right_selected_index
            self.show_menu()

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
                self._left_selected_index = self._temp_left_index
                self._right_selected_index = self._temp_right_index
                
                # Emit signals for the final selections
                self.leftSelectedIndexChanged.emit(self._left_selected_index)
                self.rightSelectedIndexChanged.emit(self._right_selected_index)
        # set target yaw angle to current imu yaw angle if yaw control is not selected
        if self.get_left_selected_option() == "EF Yaw Angle" or self.get_right_selected_option() == "EF Yaw Angle":
            self.robot.controlProcessor.controls["EF Yaw Angle"].offset = self.robot.teensy_controller.get_status().get('imu_yaw')
            print(f"Set target yaw angle to {self.robot.teensy_controller.get_status().get('imu_yaw')}")
            # Reset the temporary indices
            self._temp_left_index = 0
            self._temp_right_index = 0
        # Hide the overlay but keep the active_menu unchanged
        self._show_overlay = False
        self.overlayChanged.emit(False)

    # set left and right selected index to None
    @Slot()
    def avoidAutoRunOverwrite(self):
        """Reset the selected indices to None if the selected option related to winch and spray gun"""
        if self._left_selected_index == 1 or self._left_selected_index == 8 or self._left_selected_index == 9:
            self._left_selected_index = 0
            self.leftSelectedIndexChanged.emit(0)

        if self._right_selected_index == 1 or self._right_selected_index == 8 or self._right_selected_index == 9:
            self._right_selected_index = 0
            self.rightSelectedIndexChanged.emit(0)
        # Reset the temporary indices
        self._temp_left_index = 0
        self._temp_right_index = 0
        
    
    def _can_select_option(self, index):
        """Check if an option can be selected"""
        if self._active_menu == "left":
            return index == 0 or index != self._temp_right_index
        else:
            return index == 0 or index != self._temp_left_index
            
    @Slot()
    def move_up(self):
        """Move selection up in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
            
        current_index = self._temp_left_index if self._active_menu == "left" else self._temp_right_index
        
        for index in range(current_index - 1, -1, -1):
            if self._can_select_option(index):
                if self._active_menu == "left":
                    self._temp_left_index = index
                    self.leftSelectedIndexChanged.emit(index)
                else:
                    self._temp_right_index = index
                    self.rightSelectedIndexChanged.emit(index)
                break
                
        self._input_locked = True
        self._input_timer.start()
            
    @Slot()
    def move_down(self):
        """Move selection down in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
            
        current_index = self._temp_left_index if self._active_menu == "left" else self._temp_right_index
        
        for index in range(current_index + 1, len(self._control_options)):
            if self._can_select_option(index):
                if self._active_menu == "left":
                    self._temp_left_index = index
                    self.leftSelectedIndexChanged.emit(index)
                else:
                    self._temp_right_index = index
                    self.rightSelectedIndexChanged.emit(index)
                break
                
        self._input_locked = True
        self._input_timer.start()

    @Slot(result=str)
    def get_left_selected_option(self):
        return self._control_options[self._left_selected_index]
    
    @Slot(result=str)
    def get_right_selected_option(self):
        return self._control_options[self._right_selected_index]
    
    @Slot()
    def move_to_first(self):
        """Move selection to the first available item in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
            
        # Always try to select index 0 (None) first since it's always available
        if self._active_menu == "left":
            self._temp_left_index = 0
            self.leftSelectedIndexChanged.emit(0)
        else:
            self._temp_right_index = 0
            self.rightSelectedIndexChanged.emit(0)
                
        self._input_locked = True
        self._input_timer.start()

    @Slot()
    def move_to_last(self):
        """Move selection to the last available item in the active menu"""
        if not self._show_overlay or self._input_locked:
            return
            
        # Start from the last index and move up until we find a valid option
        for index in range(len(self._control_options) - 1, -1, -1):
            if self._can_select_option(index):
                if self._active_menu == "left":
                    self._temp_left_index = index
                    self.leftSelectedIndexChanged.emit(index)
                else:
                    self._temp_right_index = index
                    self.rightSelectedIndexChanged.emit(index)
                break
                
        self._input_locked = True
        self._input_timer.start()


    @Slot(str, str)
    def set_joystick_controls(self, left_control: str, right_control: str):
        """
        Configure left and right joystick controls
        
        Args:
            left_control: Control option for left joystick
            right_control: Control option for right joystick
        """
        # Find the indices for the specified control options
        left_index = self._control_options.index(left_control) if left_control in self._control_options else 0
        right_index = self._control_options.index(right_control) if right_control in self._control_options else 0
        
        # Update the selected indices
        self._left_selected_index = left_index
        self._right_selected_index = right_index
        
        # Emit signals to update the UI
        self.leftSelectedIndexChanged.emit(left_index)
        self.rightSelectedIndexChanged.emit(right_index)
        
        # If EF Yaw Angle is selected, initialize the target angle to current IMU yaw
        if left_control == "EF Yaw Angle" or right_control == "EF Yaw Angle":
            current_yaw = self.robot.teensy_controller.get_status().get('yaw_command', 0)
            self.robot.controlProcessor.controls["EF Yaw Angle"].offset = current_yaw
            print(f"Set target yaw angle to {current_yaw}")
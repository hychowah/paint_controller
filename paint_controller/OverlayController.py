#!/usr/bin/env python3

import sys
import os
import time
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable
import yaml
import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from std_msgs.msg import Float64, Bool, Float32, Int32
from sensor_msgs.msg import LaserScan
from cv_bridge import CvBridge
from towngas_interfaces.msg import WinchStatus, WheelStatus, SteamDeckInput, TeensyStatus, TeensyYaw

from PySide6.QtCore import QTimer, QObject, QUrl, Slot, Qt, Property, Signal, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType
from PySide6.QtWidgets import QApplication
from PySide6.QtQuick import QQuickImageProvider



class OverlayController(QObject):
    """Controller class for managing dual joystick menu state"""
    
    leftSelectedIndexChanged = Signal(int)
    rightSelectedIndexChanged = Signal(int)
    overlayChanged = Signal(bool)
    controlOptionsChanged = Signal(list)
    activeMenuChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)

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
            "EF spray gimbal"
        ]

        # Current active indices
        self._left_selected_index = 0
        self._right_selected_index = 0
        
        # Temporary indices for selection in overlay
        self._temp_left_index = 0
        self._temp_right_index = 0
        
        self._max_index = len(self._control_options) - 1
        self._show_overlay = False
        self._active_menu = "left"
        
        # Initialize timer
        self._input_timer = QTimer(self)
        self._input_timer.setInterval(300)
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
        if menu in ["left", "right"]:
            self._active_menu = menu
            self.activeMenuChanged.emit(menu)
    
    def toggle_left_menu(self):
        if self._active_menu != "left":
            return
        if self._show_overlay:
            self.hide_menu()
        else:
            # Initialize temporary selection with current selection
            self._temp_left_index = self._left_selected_index
            self._temp_right_index = self._right_selected_index
            self.show_menu()

    def toggle_right_menu(self):
        if self._active_menu != "right":
            return
        if self._show_overlay:
            self.hide_menu()
        else:
            # Initialize temporary selection with current selection
            self._temp_left_index = self._left_selected_index
            self._temp_right_index = self._right_selected_index
            self.show_menu()

    def is_showing_menu(self):
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
            # Apply temporary selections to actual selections
            self._left_selected_index = self._temp_left_index
            self._right_selected_index = self._temp_right_index
            
            # Emit signals for the final selections
            self.leftSelectedIndexChanged.emit(self._left_selected_index)
            self.rightSelectedIndexChanged.emit(self._right_selected_index)
            
        self._show_overlay = False
        self.overlayChanged.emit(False)
    
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

    @Slot()
    def get_left_selected_option(self):
        return self._control_options[self._left_selected_index]
    
    @Slot()
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
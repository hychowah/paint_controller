#!/usr/bin/env python3

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable
import math

from towngas_interfaces.msg import SteamDeckInput


class SteamDeckHandler:
    def __init__(self, deadzone: float, smoothing_factor: float = 0.1):
        self._deadzone = deadzone
        self._smoothing_factor = max(0.0, min(1.0, smoothing_factor))  # Clamp between 0 and 1
        self._input_state = {}
        self._prev_input_state = {}  # Added to track previous state
        self._callbacks = {}
        self._prev_stick_values = {
            'left_stick': {'x': 0.0, 'y': 0.0},
            'right_stick': {'x': 0.0, 'y': 0.0}
        }
        # Initialize button_pressed state
        self._button_pressed = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'a': False,
            'b': False,
            'x': False,
            'y': False,
            'l1': False,
            'r1': False,
            'l4': False,
            'r4': False,
            'menu': False,
            'quick_access': False
        }

    def process_input(self, msg: SteamDeckInput):
        new_state = {
            'left_stick': self._process_stick(msg.left_stick_x, msg.left_stick_y, 'left_stick'),
            'right_stick': self._process_stick(msg.right_stick_x, msg.right_stick_y, 'right_stick'),
            'triggers': {
                'left': msg.left_trigger,
                'right': msg.right_trigger
            },
            'buttons': {
                'up': msg.dpad_up,
                'down': msg.dpad_down,
                'left': msg.dpad_left,
                'right': msg.dpad_right,
                'a': msg.a,
                'b': msg.b,
                'x': msg.x,
                'y': msg.y,
                'l1': msg.l1,
                'r1': msg.r1,
                'l4': msg.l4,
                'r4': msg.r4,
                'menu': msg.menu,
                'quick_access': msg.quick_access
            },
            'imu': {
                'pitch': msg.imu_pitch,
                'roll': msg.imu_roll,
                'yaw': msg.imu_yaw
            }
        }
        self._input_state = new_state
        
        

    def _update_button_pressed_state(self):
        """Update the button_pressed state based on rising edge detection"""
        if not self._prev_input_state:
            return

        for button in self._button_pressed.keys():
            prev_state = self._prev_input_state.get('buttons', {}).get(button, False)
            current_state = self._input_state.get('buttons', {}).get(button, False)
            # Rising edge detection: True only when previous was False and current is True
            self._button_pressed[button] = not prev_state and current_state

    def get_button_pressed(self, button: str) -> bool:
        """
        Get the pressed state of a specific button (rising edge detection)
        Returns True if the button was just pressed (rising edge detected)
        """
        return self._button_pressed.get(button, False)

    def get_all_pressed_buttons(self) -> Dict[str, bool]:
        """
        Get all buttons that were just pressed in this frame
        Returns a dictionary of button names and their pressed states
        """
        return self._button_pressed.copy()

    def _process_stick(self, x: float, y: float, stick_id: str) -> Dict[str, float]:
        # Normalize inputs to -1.0 to 1.0 range
        x = x / 32768.0
        y = y / 32768.0
        
        # Calculate magnitude and direction
        magnitude = math.sqrt(x*x + y*y)
        if magnitude < self._deadzone:
            self._prev_stick_values[stick_id] = {'x': 0.0, 'y': 0.0}
            return {'x': 0.0, 'y': 0.0}
        
        # Calculate normalized direction
        if magnitude > 0:
            normalized_x = x / magnitude
            normalized_y = y / magnitude
        else:
            normalized_x = 0
            normalized_y = 0
        
        # Apply deadzone scaling
        scaled_magnitude = self._scale_deadzone(magnitude)
        
        # Apply the scaled magnitude back to the normalized direction
        processed_x = normalized_x * scaled_magnitude
        processed_y = normalized_y * scaled_magnitude
        
        # Apply smoothing
        smoothed_x = self._apply_smoothing(processed_x, self._prev_stick_values[stick_id]['x'])
        smoothed_y = self._apply_smoothing(processed_y, self._prev_stick_values[stick_id]['y'])
        
        # Store current values for next frame
        self._prev_stick_values[stick_id] = {'x': smoothed_x, 'y': smoothed_y}
        
        return {
            'x': smoothed_x * 32768,
            'y': smoothed_y * 32768
        }

    def _scale_deadzone(self, magnitude: float) -> float:
        """
        Scales the input magnitude accounting for deadzone.
        Returns a value between 0 and 1.
        """
        if magnitude < self._deadzone:
            return 0.0
        
        # Rescale the input from [deadzone, 1.0] to [0.0, 1.0]
        scaled = (magnitude - self._deadzone) / (1.0 - self._deadzone)
        return min(scaled, 1.0)  # Clamp to maximum of 1.0

    def _apply_smoothing(self, current: float, previous: float) -> float:
        """
        Applies exponential smoothing to the input values.
        smoothing_factor of 1.0 means no smoothing, 0.0 means maximum smoothing.
        """
        return current * self._smoothing_factor + previous * (1.0 - self._smoothing_factor)

    def _detect_changes(self, new_state: Dict) -> Dict[str, Any]:
        changes = {}
        for key in new_state:
            if key not in self._input_state or new_state[key] != self._input_state[key]:
                changes[key] = new_state[key]
        return changes
    
    def get_current_state(self) -> Dict:
        """Get current input state"""
        # Update button_pressed state
        self._update_button_pressed_state()
        # Store previous state before updating
        self._prev_input_state = self._input_state.copy() if self._input_state else {}
        return self._input_state

    def has_new_input(self) -> bool:
        """Check if there are new inputs to process"""
        return bool(self._detect_changes(self._input_state))
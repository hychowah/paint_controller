#!/usr/bin/env python3

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, List, Any, Callable
import math
import time

from rclpy.node import Node
from towngas_interfaces.msg import SteamDeckInput
from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer

class SteamDeckHandler(QObject):
    # Define Qt signals
    input_state_changed = Signal(dict)
    left_stick_changed = Signal()
    right_stick_changed = Signal()
    triggers_changed = Signal()
    buttons_changed = Signal()
    imu_changed = Signal()
    
    def __init__(self, deadzone: float = 0.1, smoothing_factor: float = 0.1, update_rate: float = 60.0, default_debounce_time: float = 0.15):
        super().__init__()
        self._node = None  # Will be set when attached to a node
        self._deadzone = deadzone
        self._smoothing_factor = max(0.0, min(1.0, smoothing_factor))  # Clamp between 0 and 1
        self._default_debounce_time = default_debounce_time  # Default time in seconds to debounce button presses
        
        # UI update throttling
        self._update_rate = update_rate  # Hz
        self._min_update_interval = 1.0 / update_rate  # seconds
        self._last_update_time = 0
        self._pending_updates = False
        
        # Initialize state variables
        self._input_state = {
            'left_stick': {'x': 0.0, 'y': 0.0},
            'right_stick': {'x': 0.0, 'y': 0.0},
            'triggers': {'left': 0.0, 'right': 0.0},
            'buttons': {
                'up': False, 'down': False, 'left': False, 'right': False,
                'a': False, 'b': False, 'x': False, 'y': False,
                'l1': False, 'r1': False, 'l4': False, 'r4': False,
                'menu': False, 'quick_access': False
            },
            'imu': {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}
        }
        self._prev_input_state = self._input_state.copy()
        
        # Initialize button_pressed state for edge detection
        self._button_pressed = {
            'up': False, 'down': False, 'left': False, 'right': False,
            'a': False, 'b': False, 'x': False, 'y': False,
            'l1': False, 'r1': False, 'l4': False, 'r4': False,
            'menu': False, 'quick_access': False
        }
        
        # Track the last time each button was pressed for debouncing
        self._last_press_time = {
            'up': 0, 'down': 0, 'left': 0, 'right': 0,
            'a': 0, 'b': 0, 'x': 0, 'y': 0,
            'l1': 0, 'r1': 0, 'l4': 0, 'r4': 0,
            'menu': 0, 'quick_access': 0
        }
        
        # Set per-button debounce times (defaults to the default debounce time)
        self._debounce_times = {
            'up': self._default_debounce_time, 
            'down': self._default_debounce_time, 
            'left': self._default_debounce_time, 
            'right': self._default_debounce_time,
            'a': self._default_debounce_time, 
            'b': self._default_debounce_time, 
            'x': self._default_debounce_time, 
            'y': self._default_debounce_time,
            'l1': self._default_debounce_time, 
            'r1': self._default_debounce_time, 
            'l4': self._default_debounce_time, 
            'r4': self._default_debounce_time,
            'menu': self._default_debounce_time, 
            'quick_access': self._default_debounce_time
        }
        
        self._prev_stick_values = {
            'left_stick': {'x': 0.0, 'y': 0.0},
            'right_stick': {'x': 0.0, 'y': 0.0}
        }
        
        # Connection status tracking
        self._available = False
        self._last_input_time = 0
        self._connection_timeout = 1.0  # Time in seconds before considering disconnected
        
        # Create availability check timer
        self._availability_timer = QTimer(self)
        self._availability_timer.timeout.connect(self._check_availability)
        self._availability_timer.start(200)  # Check every 200ms

    def attach_to_node(self, node: Node):
        """Attach this handler to a ROS node and set up the subscription"""
        self._node = node
        
        # Set up the subscription
        self._input_sub = self._node.create_subscription(
            SteamDeckInput,
            'steam_deck/input',
            self._input_callback,
            10
        )
        
        
        print("SteamDeckHandler: Subscribed to 'steam_deck/input' topic")
    
    def _check_availability(self):
        """Check if the Steam Deck controller is still connected"""
        current_time = time.time()
        
        # Calculate time since last input
        time_since_last_input = current_time - self._last_input_time
        
        # If it's been too long since the last update, consider disconnected
        if time_since_last_input > self._connection_timeout:
            if self._available:
                self._available = False
                print(f"Steam Deck considered disconnected: {time_since_last_input:.1f}s since last message")
        
    def _input_callback(self, msg: SteamDeckInput):
        """Process incoming SteamDeckInput messages from ROS"""
        try:
            # Store previous state for change detection
            
            # Update connection status
            self._last_input_time = time.time()
            current_time = time.time()
            time_since_last_update = current_time - self._last_update_time
            if time_since_last_update < self._min_update_interval:
                return

            self._prev_input_state = self._input_state.copy()
            
            # Process the input
            self.process_input(msg)
            self._pending_updates = True
            self._process_pending_updates()
            self._last_update_time = current_time
            
        except Exception as e:
            print(f"Error in Steam Deck input callback: {e}")
    
    def process_input(self, msg: SteamDeckInput):
        """Process the input message and update internal state"""
        # Store the new state
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
        
        # Update internal state
        self._input_state = new_state
        
        # Update button_pressed state for edge detection
        self._update_button_pressed_state()
    
    def _process_pending_updates(self):
        """
        Process any pending updates at the controlled update rate
        This is called by the timer at the specified update rate
        """
        
        self._emit_change_signals()
        self._pending_updates = False
            # print(f"SteamDeckHandler: UI update processed at {time_since_last_update}Hz")
    
    def _emit_change_signals(self):
        """Emit signals for all properties without comparison"""
        
        # Simply emit all signals - no comparison needed
        self.left_stick_changed.emit()
        self.right_stick_changed.emit()
        self.triggers_changed.emit()
        self.buttons_changed.emit()
        self.imu_changed.emit()
        
        # Create a dict with the current state for the main signal
        changes = {
            'left_stick': self._input_state.get('left_stick', {}).copy(),
            'right_stick': self._input_state.get('right_stick', {}).copy(),
            'triggers': self._input_state.get('triggers', {}).copy(),
            'buttons': self._input_state.get('buttons', {}).copy(),
            'imu': self._input_state.get('imu', {}).copy()
        }
        
        # Emit the overall state change signal
        self.input_state_changed.emit(changes)

    def _update_button_pressed_state(self):
        """
        Update the button_pressed state based on rising edge detection with per-button debouncing
        """
        current_time = time.time()
        
        for button in self._button_pressed.keys():
            prev_state = self._prev_input_state.get('buttons', {}).get(button, False)
            current_state = self._input_state.get('buttons', {}).get(button, False)
            
            # Rising edge detection: True only when previous was False and current is True
            is_rising_edge = not prev_state and current_state
            
            if is_rising_edge:
                # Check if enough time has passed since the last press (debouncing)
                time_since_last_press = current_time - self._last_press_time[button]
                button_debounce_time = self._debounce_times[button]
                
                if time_since_last_press >= button_debounce_time:
                    # Update the last press time and set button as pressed
                    self._last_press_time[button] = current_time
                    self._button_pressed[button] = True
                else:
                    # Not enough time passed, ignore this press (debounce)
                    self._button_pressed[button] = False
            else:
                # Not a rising edge, so not a new press
                self._button_pressed[button] = False

    def get_button_pressed(self, button: str) -> bool:
        """
        Get the pressed state of a specific button (rising edge detection with debouncing)
        Returns True if the button was just pressed (rising edge detected) and passed debounce check
        """
        return self._button_pressed.get(button, False)

    def get_all_pressed_buttons(self) -> Dict[str, bool]:
        """
        Get all buttons that were just pressed in this frame that passed debounce check
        Returns a dictionary of button names and their pressed states
        """
        return self._button_pressed.copy()
    
    def set_debounce_time(self, button: str, debounce_time: float):
        """
        Set the debounce time for a specific button in seconds
        """
        if button in self._debounce_times:
            self._debounce_times[button] = max(0.0, debounce_time)  # Ensure non-negative
        else:
            print(f"Warning: Button '{button}' not found when setting debounce time")
    
    def set_default_debounce_time(self, debounce_time: float):
        """
        Set the default debounce time in seconds for all buttons
        """
        self._default_debounce_time = max(0.0, debounce_time)  # Ensure non-negative
        
    def set_all_debounce_times(self, debounce_time: float):
        """
        Set the debounce time for all buttons at once
        """
        debounce_time = max(0.0, debounce_time)  # Ensure non-negative
        for button in self._debounce_times:
            self._debounce_times[button] = debounce_time
            
    def get_debounce_time(self, button: str) -> float:
        """
        Get the current debounce time for a specific button in seconds
        """
        if button in self._debounce_times:
            return self._debounce_times[button]
        else:
            print(f"Warning: Button '{button}' not found when getting debounce time")
            return self._default_debounce_time
            
    def get_default_debounce_time(self) -> float:
        """
        Get the default debounce time in seconds
        """
        return self._default_debounce_time
        
    def get_all_debounce_times(self) -> Dict[str, float]:
        """
        Get all button debounce times
        """
        return self._debounce_times.copy()

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
    
    def get_current_state(self) -> Dict:
        """Get current input state"""
        return self._input_state.copy()

    def has_new_input(self) -> bool:
        """Check if there are new inputs since last get_current_state call"""
        return self._input_state != self._prev_input_state
    
    # Property getters
    def get_left_stick(self) -> Dict[str, float]:
        return self._input_state['left_stick'].copy()
    
    def get_right_stick(self) -> Dict[str, float]:
        return self._input_state['right_stick'].copy()
    
    def get_triggers(self) -> Dict[str, float]:
        return self._input_state['triggers'].copy()
    
    def get_buttons(self) -> Dict[str, bool]:
        return self._input_state['buttons'].copy()
    
    def get_imu(self) -> Dict[str, float]:
        return self._input_state['imu'].copy()
    
    def get_available(self) -> bool:
        return self._available
    
    # Define Qt properties
    left_stick = Property(dict, get_left_stick, notify=left_stick_changed)
    right_stick = Property(dict, get_right_stick, notify=right_stick_changed)
    triggers = Property(dict, get_triggers, notify=triggers_changed)
    buttons = Property(dict, get_buttons, notify=buttons_changed)
    imu = Property(dict, get_imu, notify=imu_changed)
    available = Property(bool, get_available)
    
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()
        
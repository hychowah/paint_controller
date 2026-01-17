#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Dict, List, Callable, Any, Optional
import math
import time
import hid
import struct

from PySide6.QtCore import QObject, Signal, Property, Slot, QTimer, QThread, QMutex, QMutexLocker

class SteamDeckReaderThread(QThread):
    """Qt thread for reading from the Steam Deck HID device"""
    
    # Signal to emit when new data is read
    data_read = Signal(bytes)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_requested = False
        self._device = None
        self._mutex = QMutex()
    
    def set_device(self, device):
        """Set the HID device to read from"""
        self._device = device
    
    def run(self):
        """Main thread function to read from HID device with blocking read optimization"""
        self._stop_requested = False
        
        if not self._device:
            print("Error: No HID device set for reader thread")
            return
            
        while not self._stop_requested:
            try:
                with QMutexLocker(self._mutex):
                    if self._device and not self._stop_requested:
                        # Use blocking read with 50ms timeout instead of polling
                        # This reduces CPU usage and provides better responsiveness than sleep+poll
                        data = self._device.read(64, timeout_ms=50)
                        if data:
                            self.data_read.emit(bytes(data))
                
                # No additional sleep needed - blocking read provides throttling
            except Exception as e:
                # Only log error if we're not stopping
                if not self._stop_requested:
                    print(f"Error reading from Steam Deck: {e}")
                QThread.msleep(100)  # Sleep on error to avoid rapid retry loops
    
    def stop(self):
        """Request the thread to stop"""
        self._stop_requested = True
        
        # Clear device reference to stop reads immediately
        with QMutexLocker(self._mutex):
            self._device = None
        
        # Don't wait here - let the caller use wait() if needed
    
    def cleanup(self):
        """Full cleanup of the thread"""
        if self.isRunning():
            self.stop()
            if not self.wait(2000):  # Wait up to 2 seconds
                print("Warning: Reader thread did not stop in time")
                self.terminate()  # Force terminate as last resort
                self.wait(1000)  # Wait for termination


class SteamDeckHandler(QObject):
    # Define Qt signals
    input_state_changed = Signal(dict)
    left_stick_changed = Signal()
    right_stick_changed = Signal()
    triggers_changed = Signal()
    buttons_changed = Signal()
    imu_changed = Signal()
    connection_status_changed = Signal(bool)
    button_held = Signal(str, float)  # Signal for button hold events (button, duration)
    button_hold_progress = Signal(str, float, float)  # Signal for hold progress (button, current_duration, target_duration)
    
    def __init__(self, deadzone: float = 0.1, smoothing_factor: float = 0.1, default_debounce_time: float = 0.15):
        super().__init__()
        self._deadzone = deadzone
        self._smoothing_factor = max(0.0, min(1.0, smoothing_factor))  # Clamp between 0 and 1
        self._default_debounce_time = default_debounce_time  # Default time in seconds to debounce button presses
        
        # Create mutex for thread-safe access to state
        self._mutex = QMutex()
        
        # Initialize state variables
        self._input_state = {
            'left_stick': {'x': 0.0, 'y': 0.0},
            'right_stick': {'x': 0.0, 'y': 0.0},
            'triggers': {'left': 0.0, 'right': 0.0},
            'buttons': {
                'up': False, 'down': False, 'left': False, 'right': False,
                'a': False, 'b': False, 'x': False, 'y': False,
                'l1': False, 'r1': False, 'l4': False, 'r4': False,
                'l5': False, 'r5': False, 'l3': False,
                'menu': False, 'switch': False, 'steam': False, 'dot': False
            },
            'imu': {'pitch': 0.0, 'roll': 0.0, 'yaw': 0.0}
        }
        self._prev_input_state = self._input_state.copy()
        
        # Initialize button_pressed state for edge detection
        self._button_pressed = {
            'up': False, 'down': False, 'left': False, 'right': False,
            'a': False, 'b': False, 'x': False, 'y': False,
            'l1': False, 'r1': False, 'l4': False, 'r4': False,
            'l5': False, 'r5': False, 'l3': False,
            'menu': False, 'switch': False, 'steam': False, 'dot': False
        }
        
        # Unified button timing - track start time and last trigger time for each button
        self._button_state_timing = {
            'up': {'start_time': 0, 'last_trigger_time': 0}, 
            'down': {'start_time': 0, 'last_trigger_time': 0}, 
            'left': {'start_time': 0, 'last_trigger_time': 0}, 
            'right': {'start_time': 0, 'last_trigger_time': 0},
            'a': {'start_time': 0, 'last_trigger_time': 0}, 
            'b': {'start_time': 0, 'last_trigger_time': 0}, 
            'x': {'start_time': 0, 'last_trigger_time': 0}, 
            'y': {'start_time': 0, 'last_trigger_time': 0},
            'l1': {'start_time': 0, 'last_trigger_time': 0}, 
            'r1': {'start_time': 0, 'last_trigger_time': 0}, 
            'l4': {'start_time': 0, 'last_trigger_time': 0}, 
            'r4': {'start_time': 0, 'last_trigger_time': 0},
            'l5': {'start_time': 0, 'last_trigger_time': 0},
            'r5': {'start_time': 0, 'last_trigger_time': 0},
            'l3': {'start_time': 0, 'last_trigger_time': 0},
            'menu': {'start_time': 0, 'last_trigger_time': 0}, 
            'switch': {'start_time': 0, 'last_trigger_time': 0},
            'steam': {'start_time': 0, 'last_trigger_time': 0},
            'dot': {'start_time': 0, 'last_trigger_time': 0}
        }
        
        # Set per-button debounce times
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
            'l5': self._default_debounce_time,
            'r5': self._default_debounce_time,
            'l3': self._default_debounce_time,
            'menu': self._default_debounce_time, 
            'switch': self._default_debounce_time,
            'steam': self._default_debounce_time,
            'dot': self._default_debounce_time
        }
        
        # Button hold callbacks
        self._button_hold_callbacks = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'a': [], 'b': [], 'x': [], 'y': [],
            'l1': [], 'r1': [], 'l4': [], 'r4': [],
            'l5': [], 'r5': [], 'l3': [],
            'menu': [], 'switch': [], 'steam': [], 'dot': []
        }
        
        # Track which hold callbacks have been triggered in current hold session
        self._button_hold_triggered = {
            'up': {}, 'down': {}, 'left': {}, 'right': {},
            'a': {}, 'b': {}, 'x': {}, 'y': {},
            'l1': {}, 'r1': {}, 'l4': {}, 'r4': {},
            'l5': {}, 'r5': {}, 'l3': {},
            'menu': {}, 'switch': {}, 'steam': {}, 'dot': {}
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
        self._availability_timer.start(1000)  # Check every 1000ms (optimized from 200ms)
        
        # Button callback system - store callbacks for each button
        self._button_callbacks = {
            'up': [], 'down': [], 'left': [], 'right': [],
            'a': [], 'b': [], 'x': [], 'y': [],
            'l1': [], 'r1': [], 'l4': [], 'r4': [],
            'l5': [], 'r5': [], 'l3': [],
            'menu': [], 'switch': [], 'steam': [], 'dot': []
        }
        
        # Initialize HID device and reader thread
        self._device = None
        self._reader_thread = SteamDeckReaderThread(self)
        self._reader_thread.data_read.connect(self._process_input)
    
    def __del__(self):
        """Destructor to ensure cleanup on object deletion"""
        try:
            self.cleanup()
        except:
            # Silently fail in destructor to avoid issues during interpreter shutdown
            pass
        
    def start(self):
        """Initialize and start the Steam Deck HID connection"""
        # Prevent starting if already running
        if self._device is not None or self._reader_thread.isRunning():
            print("Warning: Steam Deck handler already started")
            return True
        
        VALVE_VID = 0x28DE
        STEAM_DECK_PID = 0x1205
        
        # Find Steam Deck device
        device_info = None
        for dev in hid.enumerate(VALVE_VID, STEAM_DECK_PID):
            if dev.get('interface_number') == 2:  # Interface 2 is the controller interface
                device_info = dev
                break
        
        if not device_info:
            print('Error: Steam Deck interface 2 not found!')
            return False
        
        try:
            # Initialize device
            self._device = hid.device()
            self._device.open_path(device_info['path'])
            self._device.set_nonblocking(1)
            
            # Start reader thread
            self._reader_thread.set_device(self._device)
            self._reader_thread.start()
            
            self._available = True
            self._last_input_time = time.time()
            self.connection_status_changed.emit(True)
            print("Steam Deck HID connection started successfully")
            return True
            
        except Exception as e:
            print(f"Error initializing Steam Deck: {e}")
            if self._device:
                self._device.close()
                self._device = None
            return False
    
    def stop(self):
        """Stop the HID connection and processing thread"""
        if self._reader_thread.isRunning():
            self._reader_thread.stop()
            
        with QMutexLocker(self._mutex):
            if self._device:
                try:
                    self._device.close()
                except Exception as e:
                    print(f"Error closing Steam Deck device: {e}")
                finally:
                    self._device = None
            
        self._available = False
        self.connection_status_changed.emit(False)
        print("Steam Deck HID connection stopped")
    
    def cleanup(self):
        """Comprehensive cleanup of all Steam Deck handler resources.
        
        This method ensures proper cleanup of:
        - QTimer (availability check timer)
        - Reader thread (with timeout and force termination if needed)
        - HID device connection
        - All registered callbacks
        - Internal state variables
        
        This method is idempotent and safe to call multiple times.
        """
        print("Cleaning up Steam Deck handler...")
        
        # Stop the availability timer
        if hasattr(self, '_availability_timer') and self._availability_timer:
            self._availability_timer.stop()
            self._availability_timer.deleteLater()
            self._availability_timer = None
        
        # Stop the reader thread and HID device
        self.stop()
        
        # Wait for reader thread to fully terminate
        if self._reader_thread and self._reader_thread.isRunning():
            if not self._reader_thread.wait(2000):  # Wait up to 2 seconds
                print("Warning: Steam Deck reader thread did not terminate in time")
        
        # Clear all callbacks
        with QMutexLocker(self._mutex):
            for button in self._button_callbacks:
                self._button_callbacks[button].clear()
            for button in self._button_hold_callbacks:
                self._button_hold_callbacks[button].clear()
        
        # Reset state
        self._available = False
        
        print("Steam Deck handler cleanup complete")
    
    def register_button_callback(self, button: str, callback: Callable[[], None]):
        """
        Register a callback function to be called when a specific button is pressed
        
        Args:
            button: The button name to assign the callback to
            callback: Function to call when the button is pressed
        
        Returns:
            True if successful, False if the button name is invalid
        """
        if button in self._button_callbacks:
            with QMutexLocker(self._mutex):
                self._button_callbacks[button].append(callback)
            return True
        else:
            print(f"Warning: Button '{button}' is not a valid button name")
            return False
    
    def unregister_button_callback(self, button: str, callback: Callable[[], None]):
        """
        Remove a previously registered callback for a button
        
        Args:
            button: The button name to remove the callback from
            callback: The callback function to remove
        
        Returns:
            True if removed successfully, False if button is invalid or callback wasn't registered
        """
        if button in self._button_callbacks:
            with QMutexLocker(self._mutex):
                if callback in self._button_callbacks[button]:
                    self._button_callbacks[button].remove(callback)
                    return True
                else:
                    print(f"Warning: Callback not found for button '{button}'")
                    return False
        else:
            print(f"Warning: Button '{button}' is not a valid button name")
            return False
    
    def register_button_hold_callback(self, button: str, hold_duration: float, callback: Callable[[float], None], 
                                    update_during_hold: bool = False, update_interval: float = 0.1):
        """
        Register a callback function to be called when a specific button is held for a certain duration
        
        Args:
            button: The button name to assign the hold callback to
            hold_duration: Duration in seconds required for the hold callback
            callback: Function to call when the button is held (receives current hold duration as argument)
            update_during_hold: If True, callback will be called repeatedly during hold (for progress updates)
            update_interval: Interval between updates if update_during_hold is True
        
        Returns:
            True if successful, False if the button name is invalid
        """
        if button in self._button_hold_callbacks:
            with QMutexLocker(self._mutex):
                callback_id = len(self._button_hold_callbacks[button])
                self._button_hold_callbacks[button].append({
                    'duration': hold_duration,
                    'callback': callback,
                    'update_during_hold': update_during_hold,
                    'update_interval': update_interval,
                    'last_update_time': 0,
                    'callback_id': callback_id
                })
                # Initialize hold triggered state for this callback
                self._button_hold_triggered[button][callback_id] = False
            return True
        else:
            print(f"Warning: Button '{button}' is not a valid button name")
            return False
    
    def unregister_button_hold_callback(self, button: str, callback: Callable[[float], None]):
        """
        Remove a previously registered hold callback for a button
        
        Args:
            button: The button name to remove the hold callback from
            callback: The callback function to remove
        
        Returns:
            True if removed successfully, False if button is invalid or callback wasn't registered
        """
        if button in self._button_hold_callbacks:
            with QMutexLocker(self._mutex):
                for i, hold_callback in enumerate(self._button_hold_callbacks[button]):
                    if hold_callback['callback'] == callback:
                        # Remove from triggered state
                        callback_id = hold_callback['callback_id']
                        if callback_id in self._button_hold_triggered[button]:
                            del self._button_hold_triggered[button][callback_id]
                        # Remove the callback
                        self._button_hold_callbacks[button].pop(i)
                        return True
                print(f"Warning: Hold callback not found for button '{button}'")
                return False
        else:
            print(f"Warning: Button '{button}' is not a valid button name")
            return False
    
    def _check_availability(self):
        """Check if the Steam Deck controller is still connected"""
        current_time = time.time()
        
        # Calculate time since last input
        time_since_last_input = current_time - self._last_input_time
        
        # If it's been too long since the last update, consider disconnected
        was_available = self._available
        if time_since_last_input > self._connection_timeout:
            if self._available:
                self._available = False
                print(f"Steam Deck considered disconnected: {time_since_last_input:.1f}s since last message")
                self.connection_status_changed.emit(False)
    
    @Slot(bytes)
    def _process_input(self, data):
        """Process the raw HID input data"""
        if len(data) < 64:
            return
            
        # Update the last input time
        self._last_input_time = time.time()
        
        # Set available status if it wasn't already
        if not self._available:
            self._available = True
            self.connection_status_changed.emit(True)
            print("Steam Deck reconnected")
            
        with QMutexLocker(self._mutex):
            # Store previous state for change detection
            self._prev_input_state = self._input_state.copy()
                
            # Process byte 8 (first button byte)
            button_byte1 = data[8]
            r2_click = bool(button_byte1 & (1 << 0))
            l2_click = bool(button_byte1 & (1 << 1))
            r1 = bool(button_byte1 & (1 << 2))
            l1 = bool(button_byte1 & (1 << 3))
            y = bool(button_byte1 & (1 << 4))
            b = bool(button_byte1 & (1 << 5))
            x = bool(button_byte1 & (1 << 6))
            a = bool(button_byte1 & (1 << 7))
            
            # Process byte 9 (second button byte)
            button_byte2 = data[9]
            dpad_up = bool(button_byte2 & (1 << 0))
            dpad_right = bool(button_byte2 & (1 << 1))
            dpad_left = bool(button_byte2 & (1 << 2))
            dpad_down = bool(button_byte2 & (1 << 3))
            switch = bool(button_byte2 & (1 << 4))
            steam = bool(button_byte2 & (1 << 5))
            menu = bool(button_byte2 & (1 << 6))
            l5 = bool(button_byte2 & (1 << 7))
            
            # Process byte 10 (third button byte)
            button_byte3 = data[10]
            r5 = bool(button_byte3 & (1 << 0))
            left_touchpad_touch = bool(button_byte3 & (1 << 3))
            right_touchpad_touch = bool(button_byte3 & (1 << 4))
            l3 = bool(button_byte3 & (1 << 6))

            # Process byte 13 (fourth button byte)
            button_byte4 = data[13]
            l4 = bool(button_byte4 & (1 << 1))
            r4 = bool(button_byte4 & (1 << 2))

            button_byte5 = data[14]
            dot_button = bool(button_byte5 & (1 << 2))
            
            # Process analog inputs
            imu_pitch = struct.unpack('<h', bytes([data[38], data[39]]))[0]
            imu_roll = struct.unpack('<h', bytes([data[40], data[41]]))[0]
            imu_yaw = struct.unpack('<h', bytes([data[42], data[43]]))[0]
            left_trigger = struct.unpack('<h', bytes([data[44], data[45]]))[0]
            right_trigger = struct.unpack('<h', bytes([data[46], data[47]]))[0]
            left_stick_x = struct.unpack('<h', bytes([data[48], data[49]]))[0]
            left_stick_y = struct.unpack('<h', bytes([data[50], data[51]]))[0]
            right_stick_x = struct.unpack('<h', bytes([data[52], data[53]]))[0]
            right_stick_y = struct.unpack('<h', bytes([data[54], data[55]]))[0]
            
            # Update the input state dictionary
            self._input_state = {
                'left_stick': self._process_stick(left_stick_x, left_stick_y, 'left_stick'),
                'right_stick': self._process_stick(right_stick_x, right_stick_y, 'right_stick'),
                'triggers': {
                    'left': left_trigger,
                    'right': right_trigger
                },
                'buttons': {
                    'up': dpad_up,
                    'down': dpad_down,
                    'left': dpad_left,
                    'right': dpad_right,
                    'a': a,
                    'b': b,
                    'x': x,
                    'y': y,
                    'l1': l1,
                    'r1': r1,
                    'l4': l4,
                    'r4': r4,
                    'l5': l5,
                    'r5': r5,
                    'l3': l3,
                    'menu': menu,
                    'switch': switch,
                    'steam': steam,
                    'dot': dot_button
                },
                'imu': {
                    'pitch': imu_pitch,
                    'roll': imu_roll,
                    'yaw': imu_yaw
                }
            }
            
            # Update button timing and states
            current_time = time.time()
            self._update_button_states_and_timing(current_time)
            
            # Store the callbacks we need to execute (to avoid holding the mutex during execution)
            callbacks_to_execute = []
            for button, pressed in self._button_pressed.items():
                if pressed:
                    # Add regular button press callbacks
                    callbacks_to_execute.extend([(button, callback) for callback in self._button_callbacks[button]])
            
            # Check hold callbacks
            hold_callbacks_to_execute = []
            progress_signals_to_emit = []
            
            for button, timing in self._button_state_timing.items():
                current_state = self._input_state.get('buttons', {}).get(button, False)
                prev_state = self._prev_input_state.get('buttons', {}).get(button, False)
                
                if current_state:
                    # Button is currently pressed
                    hold_duration = current_time - timing['start_time']
                    
                    # Check all hold callbacks for this button
                    for hold_callback in self._button_hold_callbacks[button]:
                        callback_id = hold_callback['callback_id']
                        trigger_duration = hold_callback['duration']
                        
                        if hold_duration >= trigger_duration:
                            # Check if this callback hasn't been triggered yet for this hold session
                            if not self._button_hold_triggered[button].get(callback_id, False):
                                hold_callbacks_to_execute.append((button, hold_callback, hold_duration))
                                self._button_hold_triggered[button][callback_id] = True
                                # Emit held signal
                                self.button_held.emit(button, hold_duration)
                            
                            # Check for progress updates
                            if hold_callback['update_during_hold']:
                                time_since_last_update = current_time - hold_callback['last_update_time']
                                if time_since_last_update >= hold_callback['update_interval']:
                                    hold_callbacks_to_execute.append((button, hold_callback, hold_duration))
                                    hold_callback['last_update_time'] = current_time
                        
                        # Emit progress signal for UI updates
                        if hold_callback['update_during_hold'] or not self._button_hold_triggered[button].get(callback_id, False):
                            progress_signals_to_emit.append((button, hold_duration, trigger_duration))
        
        # Execute callbacks outside the mutex lock
        for button, callback in callbacks_to_execute:
            try:
                callback()
            except Exception as e:
                print(f"Error in button callback for {button}: {e}")
        
        for button, hold_callback, duration in hold_callbacks_to_execute:
            try:
                hold_callback['callback'](duration)
            except Exception as e:
                print(f"Error in hold callback for {button}: {e}")
        
        # Emit progress signals
        for button, current_duration, target_duration in progress_signals_to_emit:
            self.button_hold_progress.emit(button, current_duration, target_duration)
                
        # Emit signals
        self._emit_change_signals()
    
    def _update_button_states_and_timing(self, current_time: float):
        """
        Update the button states and timing in a unified manner
        """
        for button in self._button_pressed.keys():
            prev_state = self._prev_input_state.get('buttons', {}).get(button, False)
            current_state = self._input_state.get('buttons', {}).get(button, False)
            timing = self._button_state_timing[button]
            
            if not prev_state and current_state:
                # Button just pressed (rising edge)
                # Check debounce
                time_since_last_trigger = current_time - timing['last_trigger_time']
                if time_since_last_trigger >= self._debounce_times[button]:
                    # Valid press - update all timings
                    timing['start_time'] = current_time
                    timing['last_trigger_time'] = current_time
                    self._button_pressed[button] = True
                    
                    # Reset hold triggered states for this button
                    for callback_id in self._button_hold_triggered[button]:
                        self._button_hold_triggered[button][callback_id] = False
                else:
                    # Debounce - ignore this press
                    self._button_pressed[button] = False
            elif prev_state and not current_state:
                # Button just released
                self._button_pressed[button] = False
                # Keep start_time as is for potential next press timing
            else:
                # No state change
                self._button_pressed[button] = False
    
    def _emit_change_signals(self):
        """Emit signals for all properties"""
        self.left_stick_changed.emit()
        self.right_stick_changed.emit()
        self.triggers_changed.emit()
        self.buttons_changed.emit()
        self.imu_changed.emit()
        
        # Create a dict with the current state for the main signal
        with QMutexLocker(self._mutex):
            changes = {
                'left_stick': self._input_state.get('left_stick', {}).copy(),
                'right_stick': self._input_state.get('right_stick', {}).copy(),
                'triggers': self._input_state.get('triggers', {}).copy(),
                'buttons': self._input_state.get('buttons', {}).copy(),
                'imu': self._input_state.get('imu', {}).copy()
            }
        
        # Emit the overall state change signal
        self.input_state_changed.emit(changes)

    def get_button_pressed(self, button: str) -> bool:
        """
        Get the pressed state of a specific button (rising edge detection with debouncing)
        Returns True if the button was just pressed (rising edge detected) and passed debounce check
        """
        with QMutexLocker(self._mutex):
            return self._button_pressed.get(button, False)

    def get_all_pressed_buttons(self) -> Dict[str, bool]:
        """
        Get all buttons that were just pressed in this frame that passed debounce check
        Returns a dictionary of button names and their pressed states
        """
        with QMutexLocker(self._mutex):
            return self._button_pressed.copy()
    
    def get_button_hold_duration(self, button: str) -> float:
        """
        Get how long a button has been held for
        Returns 0 if button is not currently being held
        """
        with QMutexLocker(self._mutex):
            current_state = self._input_state.get('buttons', {}).get(button, False)
            if current_state:
                current_time = time.time()
                return current_time - self._button_state_timing[button]['start_time']
            return 0.0
    
    def set_debounce_time(self, button: str, debounce_time: float):
        """
        Set the debounce time for a specific button in seconds
        """
        with QMutexLocker(self._mutex):
            if button in self._debounce_times:
                self._debounce_times[button] = max(0.0, debounce_time)  # Ensure non-negative
            else:
                print(f"Warning: Button '{button}' not found when setting debounce time")
    
    def set_default_debounce_time(self, debounce_time: float):
        """
        Set the default debounce time in seconds for all buttons
        """
        with QMutexLocker(self._mutex):
            self._default_debounce_time = max(0.0, debounce_time)  # Ensure non-negative
        
    def set_all_debounce_times(self, debounce_time: float):
        """
        Set the debounce time for all buttons at once
        """
        debounce_time = max(0.0, debounce_time)  # Ensure non-negative
        with QMutexLocker(self._mutex):
            for button in self._debounce_times:
                self._debounce_times[button] = debounce_time
            
    def get_debounce_time(self, button: str) -> float:
        """
        Get the current debounce time for a specific button in seconds
        """
        with QMutexLocker(self._mutex):
            if button in self._debounce_times:
                return self._debounce_times[button]
            else:
                print(f"Warning: Button '{button}' not found when getting debounce time")
                return self._default_debounce_time
            
    def get_default_debounce_time(self) -> float:
        """
        Get the default debounce time in seconds
        """
        with QMutexLocker(self._mutex):
            return self._default_debounce_time
        
    def get_all_debounce_times(self) -> Dict[str, float]:
        """
        Get all button debounce times
        """
        with QMutexLocker(self._mutex):
            return self._debounce_times.copy()

    def _process_stick(self, x: float, y: float, stick_id: str) -> Dict[str, float]:
        """Process analog stick inputs with deadzone and smoothing"""
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
        with QMutexLocker(self._mutex):
            return self._input_state.copy()

    def has_new_input(self) -> bool:
        """Check if there are new inputs since last get_current_state call"""
        with QMutexLocker(self._mutex):
            return self._input_state != self._prev_input_state
    
    # Property getters
    def get_left_stick(self) -> Dict[str, float]:
        with QMutexLocker(self._mutex):
            return self._input_state['left_stick'].copy()
    
    def get_right_stick(self) -> Dict[str, float]:
        with QMutexLocker(self._mutex):
            return self._input_state['right_stick'].copy()
    
    def get_triggers(self) -> Dict[str, float]:
        with QMutexLocker(self._mutex):
            return self._input_state['triggers'].copy()
    
    def get_buttons(self) -> Dict[str, bool]:
        with QMutexLocker(self._mutex):
            return self._input_state['buttons'].copy()
    
    def get_imu(self) -> Dict[str, float]:
        with QMutexLocker(self._mutex):
            return self._input_state['imu'].copy()
    
    def get_available(self) -> bool:
        return self._available
    
    # Define Qt properties
    left_stick = Property(dict, get_left_stick, notify=left_stick_changed)
    right_stick = Property(dict, get_right_stick, notify=right_stick_changed)
    triggers = Property(dict, get_triggers, notify=triggers_changed)
    buttons = Property(dict, get_buttons, notify=buttons_changed)
    imu = Property(dict, get_imu, notify=imu_changed)
    available = Property(bool, get_available, notify=connection_status_changed)
    
    def cleanup(self):
        """Clean up resources when shutting down"""
        self.stop()
        if hasattr(self, '_availability_timer') and self._availability_timer.isActive():
            self._availability_timer.stop()
#!/usr/bin/env python3

import time
from PySide6.QtCore import QObject, Signal, QTimer

class EmergencyButtonHandler(QObject):
    """Handler for emergency button functionality"""
    
    # Signals
    overlay_changed = Signal(bool, float, float)  # visible, current_duration, target_duration
    emergency_triggered = Signal()
    
    def __init__(self, steam_deck_handler, robot_controller):
        super().__init__()
        
        self.steam_deck_handler = steam_deck_handler
        self.robot_controller = robot_controller
        
        # Emergency state tracking
        self._state = {
            'is_holding': False,
            'hold_start_time': 0,
            'overlay_visible': False,
            'completed': False,
            'duration_target': 0.2,  # 1 second
            'last_steam_state': False,
            'cooldown_start': 0,    # When emergency was last triggered
            'cooldown_duration': 1.0  # Minimum time between emergency activations
        }
    
    def check_emergency_button(self, button_state):
        """Check and update emergency button state"""
        steam_pressed = button_state.get('steam', False)
        current_time = time.time()
        
        # Check if we're in cooldown period
        if self._state['completed']:
            cooldown_elapsed = current_time - self._state['cooldown_start']
            if cooldown_elapsed >= self._state['cooldown_duration']:
                # Cooldown complete, reset the completed flag
                self._state['completed'] = False
        
        # Handle button press transitions
        if steam_pressed and not self._state['last_steam_state']:
            # Just pressed - start new hold if not already active and not in cooldown
            if not self._state['is_holding'] and not self._state['completed']:
                self._state['is_holding'] = True
                self._state['hold_start_time'] = current_time
        
        elif not steam_pressed and self._state['last_steam_state']:
            # Just released - cancel if not completed
            if self._state['is_holding'] and not self._state['completed']:
                self._cancel_emergency()
        
        # If we're holding and haven't completed
        if steam_pressed and self._state['is_holding'] and not self._state['completed']:
            hold_duration = current_time - self._state['hold_start_time']
            
            # Show overlay if not already visible
            if not self._state['overlay_visible']:
                self._state['overlay_visible'] = True
            
            # Update overlay progress
            self.overlay_changed.emit(True, hold_duration, self._state['duration_target'])
            
            # Check if we've held long enough
            if hold_duration >= self._state['duration_target']:
                self._state['completed'] = True
                self._state['cooldown_start'] = current_time  # Start cooldown
                self._trigger_emergency(hold_duration)
        
        # Update last state
        self._state['last_steam_state'] = steam_pressed
    
    def _trigger_emergency(self, duration: float):
        """Trigger the emergency action"""
        # Immediately hide the overlay and stop counting
        try:
            self._state['overlay_visible'] = False
            self._state['is_holding'] = False
            self.overlay_changed.emit(False, 0, 0)
            
            self.robot_controller.winch_controller.command_speed(0)
            self.robot_controller.teensy_controller.setSprayTrigger(1000)
            
            # Show emergency popup
            self.robot_controller.show_popup("EMERGENCY", "Emergency stop activated!", "error", 1000)
            
            # Log the event
            self.robot_controller.get_logger().error(f'Emergency activated by user at {time.time()}')
            
            # Emit signal for other components
            self.emergency_triggered.emit()
        except Exception as e:
            self.robot_controller.get_logger().error(f'Error during emergency trigger: {e}')
    
    def _stop_all_motors(self):
        """Stop all motors during emergency"""
        try:
            # Stop wheels
            if hasattr(self.robot_controller.wheel_controller, 'emergency_stop'):
                self.robot_controller.wheel_controller.emergency_stop()
            elif hasattr(self.robot_controller.wheel_controller, 'set_wheel_speeds'):
                self.robot_controller.wheel_controller.set_wheel_speeds(0, 0)
            
            # Stop winch
            if hasattr(self.robot_controller.winch_controller, 'emergency_stop'):
                self.robot_controller.winch_controller.emergency_stop()
            elif hasattr(self.robot_controller.winch_controller, 'set_winch_speed'):
                self.robot_controller.winch_controller.set_winch_speed(0)
            
            # Stop any other motors here if needed
            # self._stop_additional_motors()
            
        except Exception as e:
            self.robot_controller.get_logger().error(f'Error during emergency stop: {e}')
    
    def _cancel_emergency(self):
        """Cancel the emergency sequence"""
        # Reset holding state
        self._state['is_holding'] = False
        
        # Hide overlay immediately
        if self._state['overlay_visible']:
            self._state['overlay_visible'] = False
            self.overlay_changed.emit(False, 0, 0)
    
    def reset_state(self, force=False):
        """Reset the emergency state to initial values"""
        # If not forcing, respect cooldown
        if not force and self._state['completed']:
            current_time = time.time()
            cooldown_elapsed = current_time - self._state['cooldown_start']
            if cooldown_elapsed < self._state['cooldown_duration']:
                # Still in cooldown, don't reset completed
                self._state['is_holding'] = False
                self._state['overlay_visible'] = False
                return
        
        # Full reset
        self._state = {
            'is_holding': False,
            'hold_start_time': 0,
            'overlay_visible': False,
            'completed': False,
            'duration_target': self._state['duration_target'],  # Preserve duration
            'last_steam_state': False,
            'cooldown_start': 0,
            'cooldown_duration': self._state['cooldown_duration']  # Preserve cooldown
        }
    
    def set_duration_target(self, duration):
        """Set the required hold duration for emergency activation"""
        self._state['duration_target'] = duration
    
    def set_cooldown_duration(self, duration):
        """Set the cooldown period between emergency activations"""
        self._state['cooldown_duration'] = duration
    
    def get_state(self):
        """Get current emergency state (for debugging/monitoring)"""
        state = self._state.copy()
        if state['completed']:
            current_time = time.time()
            cooldown_elapsed = current_time - state['cooldown_start']
            state['cooldown_remaining'] = max(0, state['cooldown_duration'] - cooldown_elapsed)
        return state
    
    def force_reset(self):
        """Force reset the emergency state, bypassing cooldown"""
        self.reset_state(force=True)
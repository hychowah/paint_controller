#!/usr/bin/env python3
"""
Wheel ViewModel

MVVM pattern implementation for vehicle wheel control.
Separates UI concerns from business logic.
"""

from PySide6.QtCore import QObject, Signal, Property, Slot


class WheelViewModel(QObject):
    """
    ViewModel for Wheel/Vehicle operations.
    
    Provides a clean interface between the UI (QML) and the wheel controller
    service, following the MVVM (Model-View-ViewModel) pattern.
    
    This ViewModel:
    - Exposes properties for QML binding
    - Provides slots for UI actions
    - Emits signals for UI updates
    - Delegates business logic to the wheel controller service
    
    Example:
        wheel_service = WheelController(node)
        view_model = WheelViewModel(wheel_service)
        
        # In QML:
        # Text { text: wheelViewModel.left_wheel_speed }
        # Button { onClicked: wheelViewModel.command_speed(100, 100) }
    """
    
    # Qt Signals for property changes
    left_wheel_speed_changed = Signal(float)
    right_wheel_speed_changed = Signal(float)
    left_wheel_current_changed = Signal(float)
    right_wheel_current_changed = Signal(float)
    left_wheel_position_changed = Signal(float)
    right_wheel_position_changed = Signal(float)
    available_changed = Signal(bool)
    enabled_changed = Signal(bool)
    left_error_changed = Signal(bool)
    right_error_changed = Signal(bool)
    left_motor_available_changed = Signal(bool)
    right_motor_available_changed = Signal(bool)
    error_state_changed = Signal(bool, str)
    
    def __init__(self, wheel_controller):
        """
        Initialize ViewModel.
        
        Args:
            wheel_controller: WheelController instance (the service/model)
        """
        super().__init__()
        self._controller = wheel_controller
        
        # Connect to controller signals to forward them to our signals
        self._controller.left_wheel_speed_changed.connect(self.left_wheel_speed_changed.emit)
        self._controller.right_wheel_speed_changed.connect(self.right_wheel_speed_changed.emit)
        self._controller.left_wheel_current_changed.connect(self.left_wheel_current_changed.emit)
        self._controller.right_wheel_current_changed.connect(self.right_wheel_current_changed.emit)
        self._controller.left_wheel_position_changed.connect(self.left_wheel_position_changed.emit)
        self._controller.right_wheel_position_changed.connect(self.right_wheel_position_changed.emit)
        self._controller.available_changed.connect(self.available_changed.emit)
        self._controller.enabled_changed.connect(self.enabled_changed.emit)
        self._controller.left_error_changed.connect(self.left_error_changed.emit)
        self._controller.right_error_changed.connect(self.right_error_changed.emit)
        self._controller.left_motor_available_changed.connect(self.left_motor_available_changed.emit)
        self._controller.right_motor_available_changed.connect(self.right_motor_available_changed.emit)
        self._controller.error_state_changed.connect(self.error_state_changed.emit)
    
    # Properties for QML binding
    
    @Property(float, notify=left_wheel_speed_changed)
    def left_wheel_speed(self) -> float:
        """Current left wheel speed in RPM"""
        return self._controller.left_wheel_speed
    
    @Property(float, notify=right_wheel_speed_changed)
    def right_wheel_speed(self) -> float:
        """Current right wheel speed in RPM"""
        return self._controller.right_wheel_speed
    
    @Property(float, notify=left_wheel_current_changed)
    def left_wheel_current(self) -> float:
        """Current left wheel motor current"""
        return self._controller.left_wheel_current
    
    @Property(float, notify=right_wheel_current_changed)
    def right_wheel_current(self) -> float:
        """Current right wheel motor current"""
        return self._controller.right_wheel_current
    
    @Property(float, notify=left_wheel_position_changed)
    def left_wheel_position(self) -> float:
        """Current left wheel position"""
        return self._controller.left_wheel_position
    
    @Property(float, notify=right_wheel_position_changed)
    def right_wheel_position(self) -> float:
        """Current right wheel position"""
        return self._controller.right_wheel_position
    
    @Property(bool, notify=available_changed)
    def available(self) -> bool:
        """Wheel controller availability status"""
        return self._controller.available
    
    @Property(bool, notify=enabled_changed)
    def enabled(self) -> bool:
        """Wheel controller enabled status"""
        return self._controller.enabled
    
    @Property(bool, notify=left_error_changed)
    def left_error(self) -> bool:
        """Left motor error status"""
        return self._controller.left_error
    
    @Property(bool, notify=right_error_changed)
    def right_error(self) -> bool:
        """Right motor error status"""
        return self._controller.right_error
    
    @Property(bool, notify=left_motor_available_changed)
    def left_motor_available(self) -> bool:
        """Left motor availability"""
        return self._controller.left_motor_available
    
    @Property(bool, notify=right_motor_available_changed)
    def right_motor_available(self) -> bool:
        """Right motor availability"""
        return self._controller.right_motor_available
    
    # Slots for UI actions
    
    @Slot(float, float)
    def command_speed(self, left_rpm: float, right_rpm: float):
        """
        Command wheel speeds.
        
        Args:
            left_rpm: Left wheel speed in RPM
            right_rpm: Right wheel speed in RPM
        """
        self._controller.command_speed(left_rpm, right_rpm)
    
    @Slot(float, float, float)
    def command_position(self, left_pos: float, right_pos: float, speed_rpm: float):
        """
        Command wheel positions.
        
        Args:
            left_pos: Left wheel target position
            right_pos: Right wheel target position
            speed_rpm: Speed in RPM
        """
        self._controller.command_position(left_pos, right_pos, speed_rpm)
    
    @Slot()
    def stop(self):
        """Stop both wheels immediately"""
        self._controller.command_speed(0, 0)
    
    @Slot()
    def emergency_stop(self):
        """Emergency stop - disable and stop motors"""
        self._controller.emergency_stop()
    
    @Slot()
    def disable(self):
        """Disable wheel motors"""
        self._controller.disable()
    
    @Slot()
    def set_zero(self):
        """Set current position as zero"""
        self._controller.set_zero()

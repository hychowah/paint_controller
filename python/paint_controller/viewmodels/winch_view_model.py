#!/usr/bin/env python3
"""
Winch ViewModel

Demonstrates MVVM pattern for the winch controller.
Separates UI concerns from business logic.
"""

from PySide6.QtCore import QObject, Signal, Property, Slot


class WinchViewModel(QObject):
    """
    ViewModel for Winch operations.
    
    Provides a clean interface between the UI (QML) and the winch controller
    service, following the MVVM (Model-View-ViewModel) pattern.
    
    This ViewModel:
    - Exposes properties for QML binding
    - Provides slots for UI actions
    - Emits signals for UI updates
    - Delegates business logic to the winch controller service
    
    Example:
        winch_service = WinchController(node)
        view_model = WinchViewModel(winch_service)
        
        # In QML:
        # Text { text: winchViewModel.cable_length }
        # Button { onClicked: winchViewModel.set_speed(100) }
    """
    
    # Qt Signals for property changes
    cable_length_changed = Signal(float)
    cable_speed_changed = Signal(float)
    winch_torque_changed = Signal(float)
    motor_temperature_changed = Signal(float)
    motor_voltage_changed = Signal(float)
    motor_brake_changed = Signal(bool)
    available_changed = Signal(bool)
    enabled_changed = Signal(bool)
    max_speed_changed = Signal(float)
    
    def __init__(self, winch_controller):
        """
        Initialize ViewModel.
        
        Args:
            winch_controller: WinchController instance (the service/model)
        """
        super().__init__()
        self._controller = winch_controller
        
        # Connect to controller signals to forward them to our signals
        # This allows the ViewModel to act as a clean interface layer
        self._controller.cable_length_changed.connect(self.cable_length_changed.emit)
        self._controller.cable_speed_changed.connect(self.cable_speed_changed.emit)
        self._controller.winch_torque_changed.connect(self.winch_torque_changed.emit)
        self._controller.motor_temperature_changed.connect(self.motor_temperature_changed.emit)
        self._controller.motor_voltage_changed.connect(self.motor_voltage_changed.emit)
        self._controller.motor_brake_changed.connect(self.motor_brake_changed.emit)
        self._controller.available_changed.connect(self.available_changed.emit)
        self._controller.enabled_changed.connect(self.enabled_changed.emit)
    
    # Properties for QML binding
    
    @Property(float, notify=cable_length_changed)
    def cable_length(self) -> float:
        """Current cable length in mm"""
        return self._controller.cable_length
    
    @Property(float, notify=cable_speed_changed)
    def cable_speed(self) -> float:
        """Current cable speed in mm/s"""
        return self._controller.cable_speed
    
    @Property(float, notify=winch_torque_changed)
    def winch_torque(self) -> float:
        """Current winch torque"""
        return self._controller.winch_torque
    
    @Property(float, notify=motor_temperature_changed)
    def motor_temperature(self) -> float:
        """Motor temperature in Celsius"""
        return self._controller.motor_temperature
    
    @Property(float, notify=motor_voltage_changed)
    def motor_voltage(self) -> float:
        """Motor voltage"""
        return self._controller.motor_voltage
    
    @Property(bool, notify=motor_brake_changed)
    def motor_brake(self) -> bool:
        """Motor brake engaged status"""
        return self._controller.motor_brake
    
    @Property(bool, notify=available_changed)
    def available(self) -> bool:
        """Winch availability status"""
        return self._controller.available
    
    @Property(bool, notify=enabled_changed)
    def enabled(self) -> bool:
        """Winch enabled status"""
        return self._controller.enabled
    
    @Property(float, notify=max_speed_changed)
    def max_speed(self) -> float:
        """Maximum speed in mm/s"""
        return self._controller.max_speed
    
    # Slots for UI actions
    
    @Slot(float)
    def set_speed_rpm(self, speed: float):
        """
        Set winch speed in RPM.
        
        Args:
            speed: Speed in RPM
        """
        self._controller.command_speed_rpm(speed)
    
    @Slot(float)
    def set_speed_mmps(self, speed: float):
        """
        Set winch speed in mm/s.
        
        Args:
            speed: Speed in mm/s
        """
        self._controller.command_speed_mmps(speed)
    
    @Slot(bool)
    def set_enabled(self, enabled: bool):
        """
        Enable or disable the winch.
        
        Args:
            enabled: True to enable, False to disable
        """
        self._controller.command_enable(enabled)
    
    @Slot(float, float)
    def move_increment(self, length_mm: float, speed_mmps: float):
        """
        Move winch by relative distance.
        
        Args:
            length_mm: Distance to move in mm (positive = extend, negative = retract)
            speed_mmps: Speed in mm/s
        """
        self._controller.move_increment(length_mm, speed_mmps)
    
    @Slot(float, float)
    def move_absolute(self, target_mm: float, speed_mmps: float):
        """
        Move winch to absolute position.
        
        Args:
            target_mm: Target position in mm
            speed_mmps: Speed in mm/s
        """
        self._controller.move_absolute(target_mm, speed_mmps)
    
    @Slot()
    def stop(self):
        """Stop winch movement immediately"""
        self._controller.command_speed_rpm(0)
    
    @Slot(bool)
    def set_load_detection(self, enabled: bool):
        """
        Enable or disable load detection.
        
        Args:
            enabled: True to enable, False to disable
        """
        self._controller.command_load_detection(enabled)

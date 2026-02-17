#!/usr/bin/env python3
"""
ESP32 Valve ViewModel

MVVM pattern implementation for ESP32-based valve controller.
Separates UI concerns from business logic.
"""

from PySide6.QtCore import QObject, Signal, Property, Slot


class ESP32ValveViewModel(QObject):
    """
    ViewModel for ESP32 Valve operations.
    
    Provides a clean interface between the UI (QML) and the ESP32 valve controller
    service, following the MVVM (Model-View-ViewModel) pattern.
    
    This ViewModel:
    - Exposes properties for QML binding
    - Provides slots for UI actions
    - Emits signals for UI updates
    - Delegates business logic to the ESP32 valve controller service
    
    Example:
        valve_service = ESP32ValveController(node)
        view_model = ESP32ValveViewModel(valve_service)
        
        # In QML:
        # Text { text: esp32ValveViewModel.valve_position }
        # Slider { onValueChanged: esp32ValveViewModel.setValveTurn(value) }
    """
    
    # Qt Signals for property changes
    valve_position_changed = Signal(float)
    valve_motor_current_changed = Signal(int)
    flow_rate_changed = Signal(float)
    total_volume_changed = Signal(float)
    valve_motor_connected_changed = Signal(bool)
    flow_meter_connected_changed = Signal(bool)
    available_changed = Signal(bool)
    
    def __init__(self, esp32_valve_controller):
        """
        Initialize ViewModel.
        
        Args:
            esp32_valve_controller: ESP32ValveController instance (the service/model)
        """
        super().__init__()
        self._controller = esp32_valve_controller
        
        # Connect to controller signals to forward them to our signals
        self._controller.valve_position_changed.connect(self.valve_position_changed.emit)
        self._controller.valve_motor_current_changed.connect(self.valve_motor_current_changed.emit)
        self._controller.flow_rate_changed.connect(self.flow_rate_changed.emit)
        self._controller.total_volume_changed.connect(self.total_volume_changed.emit)
        self._controller.valve_motor_connected_changed.connect(self.valve_motor_connected_changed.emit)
        self._controller.flow_meter_connected_changed.connect(self.flow_meter_connected_changed.emit)
        self._controller.available_changed.connect(self.available_changed.emit)
    
    # Properties for QML binding
    
    @Property(float, notify=valve_position_changed)
    def valve_position(self) -> float:
        """Current valve position (0-100%)"""
        return self._controller._valve_position
    
    @Property(int, notify=valve_motor_current_changed)
    def valve_motor_current(self) -> int:
        """Valve motor current in mA"""
        return self._controller._valve_motor_current
    
    @Property(float, notify=flow_rate_changed)
    def flow_rate(self) -> float:
        """Current flow rate"""
        return self._controller._valve_rate
    
    @Property(float, notify=total_volume_changed)
    def total_volume(self) -> float:
        """Total volume dispensed"""
        return self._controller._total_volume
    
    @Property(bool, notify=valve_motor_connected_changed)
    def valve_motor_connected(self) -> bool:
        """Valve motor connection status"""
        return self._controller._valve_motor_connected
    
    @Property(bool, notify=flow_meter_connected_changed)
    def flow_meter_connected(self) -> bool:
        """Flow meter connection status"""
        return self._controller._flow_meter_connected
    
    @Property(bool, notify=available_changed)
    def available(self) -> bool:
        """ESP32 valve controller availability"""
        return self._controller._available
    
    # Slots for UI actions
    
    @Slot(float)
    def setValveTurn(self, position_pct: float):
        """
        Set valve position.
        
        Args:
            position_pct: Target position in percent (0.0-100.0)
        """
        self._controller.setValveTurn(position_pct)
    
    @Slot()
    def closeValve(self):
        """Close valve completely (set to 0%)"""
        self._controller.setValveTurn(0.0)
    
    @Slot()
    def openValve(self):
        """Open valve completely (set to 100%)"""
        self._controller.setValveTurn(100.0)

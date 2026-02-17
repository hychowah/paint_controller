#!/usr/bin/env python3
"""
Teensy ViewModel

MVVM pattern implementation for Teensy controller (spray system, rails, propellers).
Separates UI concerns from business logic.
"""

from typing import Any
from PySide6.QtCore import QObject, Signal, Property, Slot


class TeensyViewModel(QObject):
    """
    ViewModel for Teensy operations.
    
    Provides a clean interface between the UI (QML) and the teensy controller
    service, following the MVVM (Model-View-ViewModel) pattern.
    
    This ViewModel:
    - Exposes properties for QML binding
    - Provides slots for UI actions
    - Emits signals for UI updates
    - Delegates business logic to the teensy controller service
    
    Example:
        teensy_service = TeensyController(robot_controller)
        view_model = TeensyViewModel(teensy_service)
        
        # In QML:
        # Text { text: teensyViewModel.available }
        # Button { onClicked: teensyViewModel.setSprayTrigger(1500) }
    """
    
    # Qt Signals for property changes
    status_changed = Signal(dict)
    connection_changed = Signal(bool)
    spray_gun_leveling_changed = Signal(bool)
    spray_gun_led_changed = Signal(bool)
    auto_correction_enabled_changed = Signal(bool)
    stability_enabled_changed = Signal(bool)
    thrust_force_changed = Signal(float)
    thrust_force_enabled_changed = Signal(bool)
    roller_steering_enabled_changed = Signal(bool)
    
    def __init__(self, teensy_controller):
        """
        Initialize ViewModel.
        
        Args:
            teensy_controller: TeensyController instance (the service/model)
        """
        super().__init__()
        self._controller = teensy_controller
        
        # Connect to controller signals to forward them to our signals
        self._controller.status_changed.connect(self.status_changed.emit)
        self._controller.connection_changed.connect(self.connection_changed.emit)
        self._controller.spray_gun_leveling_changed.connect(self.spray_gun_leveling_changed.emit)
        self._controller.spray_gun_led_changed.connect(self.spray_gun_led_changed.emit)
        self._controller.auto_correction_enabled_changed.connect(self.auto_correction_enabled_changed.emit)
        self._controller.stability_enabled_changed.connect(self.stability_enabled_changed.emit)
        self._controller.thrust_force_changed.connect(self.thrust_force_changed.emit)
        self._controller.thrust_force_enabled_changed.connect(self.thrust_force_enabled_changed.emit)
        self._controller.roller_steering_enabled_changed.connect(self.roller_steering_enabled_changed.emit)
    
    # Property: available
    @Property(bool, notify=connection_changed)
    def available(self) -> bool:
        """Teensy controller availability status"""
        return self._controller._available
    
    # Slots for UI actions - Enable/Disable
    
    @Slot(bool)
    def setEnabled(self, enabled: bool):
        """Enable/disable Teensy control"""
        self._controller.setEnabled(enabled)
    
    @Slot(bool)
    def setRelayEnabled(self, enabled: bool):
        """Enable/disable Teensy relay"""
        self._controller.setRelayEnabled(enabled)
    
    # Slots for Rails Control
    
    @Slot(float)
    def setTopRailSpeed(self, speed: float):
        """Set the top rail speed"""
        self._controller.setTopRailSpeed(speed)
    
    @Slot(bool)
    def homeTopRail(self, home: bool):
        """Home the top rail"""
        self._controller.homeTopRail(home)
    
    @Slot(float)
    def setArmRailSpeed(self, speed: float):
        """Set the arm rail speed"""
        self._controller.setArmRailSpeed(speed)
    
    @Slot(int)
    def extendArm(self, dist: int):
        """Extend arm to specified distance"""
        self._controller.extendArm(dist)
    
    @Slot(bool)
    def homeArm(self, home: bool):
        """Home the arm rail"""
        self._controller.homeArm(home)
    
    # Slots for Propeller Control
    
    @Slot(int)
    def setLeftPropPWM(self, pwm: int):
        """Set the left propeller PWM"""
        self._controller.setLeftPropPWM(pwm)
    
    @Slot(int)
    def setRightPropPWM(self, pwm: int):
        """Set the right propeller PWM"""
        self._controller.setRightPropPWM(pwm)
    
    @Slot(float)
    def setLeftPropAngle(self, angle: float):
        """Set the left propeller joint angle"""
        self._controller.setLeftPropAngle(angle)
    
    @Slot(float)
    def setRightPropAngle(self, angle: float):
        """Set the right propeller joint angle"""
        self._controller.setRightPropAngle(angle)
    
    # Slots for Spray Gun Control
    
    @Slot(int)
    def setSprayTrigger(self, pwm: int):
        """Set spray gun trigger PWM"""
        self._controller.setSprayTrigger(pwm)
    
    @Slot(bool)
    def setSprayGunLeveling(self, enabled: bool):
        """Enable/disable spray gun leveling"""
        self._controller.setSprayGunLeveling(enabled)
    
    @Slot(bool)
    def setSprayGunLED(self, on: bool):
        """Turn spray gun LED on/off"""
        self._controller.setSprayGunLED(on)
    
    @Slot(float, float)
    def setGimbalTarget(self, pitch: float, roll: float):
        """Set gimbal target angles"""
        self._controller.setGimbalTarget(pitch, roll)
    
    @Slot(float, float, float, float, float)
    def setGimbalPID(self, p_pitch: float, i_pitch: float, d_pitch: float, 
                     p_roll: float, d_roll: float):
        """Set gimbal PID values"""
        self._controller.setGimbalPID(p_pitch, i_pitch, d_pitch, p_roll, d_roll)
    
    # Slots for Stability & Auto-correction
    
    @Slot(bool)
    def setAutoCorrection(self, enabled: bool):
        """Enable/disable auto correction"""
        self._controller.setAutoCorrection(enabled)
    
    @Slot(bool)
    def setStabilityEnabled(self, enabled: bool):
        """Enable/disable stability control"""
        self._controller.setStabilityEnabled(enabled)
    
    # Slots for Yaw Control
    
    @Slot(bool)
    def setYawEnabled(self, enabled: bool):
        """Enable/disable yaw control"""
        self._controller.setYawEnabled(enabled)
    
    @Slot(bool)
    def resetYaw(self, reset: bool):
        """Reset yaw to current heading"""
        self._controller.resetYaw(reset)
    
    @Slot(bool)
    def setRollerSteeringEnabled(self, enabled: bool):
        """Enable/disable roller steering"""
        self._controller.setRollerSteeringEnabled(enabled)
    
    # Slots for Thrust Control
    
    @Slot(float)
    def setThrustForce(self, force: float):
        """Set thrust force value"""
        self._controller.setThrustForce(force)
    
    @Slot(float, float, float)
    def setYawPID(self, p: float, i: float, d: float):
        """Set yaw PID parameters"""
        self._controller.setYawPID(p, i, d)
    
    @Slot(float, float, float)
    def setStabilityPID(self, p: float, i: float, d: float):
        """Set stability PID parameters"""
        self._controller.setStabilityPID(p, i, d)
    
    @Slot(float, float)
    def setTargetYaw(self, yaw: float, command: float):
        """Set target yaw and command value"""
        self._controller.setTargetYaw(yaw, command)
    
    @Slot(float)
    def setYawCommand(self, command: float):
        """Set yaw command value"""
        self._controller.setYawCommand(command)
    
    @Slot(float)
    def setTargetYawAngle(self, yaw: float):
        """Set target yaw angle"""
        self._controller.setTargetYawAngle(yaw)
    
    @Slot(bool)
    def setThrustForceEnabled(self, enabled: bool):
        """Enable/disable thrust force"""
        self._controller.setThrustForceEnabled(enabled)
    
    @Slot(bool)
    def setValveRelay(self, on: bool):
        """Set valve relay state"""
        self._controller.setValveRelay(on)
    
    # Status access methods
    
    @Slot(str, result='QVariant')
    def get_status_value(self, key: str) -> Any:
        """Get a specific status value by key"""
        return self._controller.get_status_value(key)
    
    @Slot(str, result=str)
    def get_formatted_value(self, key: str) -> str:
        """Get a specific status value formatted as a string"""
        return self._controller.get_formatted_value(key)

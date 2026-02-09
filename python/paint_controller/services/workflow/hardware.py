#!/usr/bin/env python3
"""
Hardware abstraction layer for robot controllers.

Provides clean interface to hardware controllers with error handling and validation.
"""

from abc import ABC, abstractmethod
from typing import Optional


class ControllerError(Exception):
    """Base exception for controller errors."""
    pass


class ControllerNotAvailable(ControllerError):
    """Raised when controller is not available."""
    pass


class ITeensyController(ABC):
    """Abstract interface for Teensy controller."""

    @abstractmethod
    def set_valve_turn(self, turn_value: float) -> None:
        """Set valve turn position."""
        pass

    @abstractmethod
    def set_spray_gun_gimbal_angle(self, angle: float, speed: float) -> None:
        """Set spray gun gimbal angle and speed."""
        pass

    @abstractmethod
    def extend_arm(self, distance: int) -> None:
        """Extend arm to specified distance."""
        pass

    @abstractmethod
    def set_ef_force(self, fx: float, fy: float) -> None:
        """Set end effector force."""
        pass


class IWinchController(ABC):
    """Abstract interface for Winch controller."""

    @abstractmethod
    def move_increment(self, length: int, speed: int, acceleration: int = 30) -> None:
        """Move winch by incremental distance."""
        pass

    @abstractmethod
    def move_absolute(self, length: int, speed: int, acceleration: int = 30) -> None:
        """Move winch to absolute position."""
        pass

    @abstractmethod
    def get_cable_length(self) -> float:
        """Get current cable length in mm."""
        pass


class TeensyControllerAdapter(ITeensyController):
    """Adapter for actual Teensy controller implementation."""

    def __init__(self, teensy_controller, valve_controller=None):
        """
        Initialize adapter.
        
        Args:
            teensy_controller: Actual Teensy controller instance
            valve_controller: Valve controller instance (ESP32ValveController)
        """
        self._teensy_controller = teensy_controller
        self._valve_controller = valve_controller

    def set_valve_turn(self, turn_value: float) -> None:
        """Set valve turn position."""
        if not self._valve_controller:
            raise ControllerNotAvailable("ESP32 valve controller not available")
        self._valve_controller.setValveTurn(float(turn_value))

    def set_spray_gun_gimbal_angle(self, angle: float, speed: float) -> None:
        """Set spray gun gimbal angle and speed."""
        if not self._teensy_controller:
            raise ControllerNotAvailable("Teensy controller not available")
        self._teensy_controller.setSprayGunGimbalAngle(float(angle), float(speed))

    def extend_arm(self, distance: int) -> None:
        """Extend arm to specified distance."""
        if not self._teensy_controller:
            raise ControllerNotAvailable("Teensy controller not available")
        self._teensy_controller.extendArm(int(distance))

    def set_ef_force(self, fx: float, fy: float) -> None:
        """Set end effector force."""
        if not self._teensy_controller:
            raise ControllerNotAvailable("Teensy controller not available")
        self._teensy_controller.set_ef_force(float(fx), float(fy))


class WinchControllerAdapter(IWinchController):
    """Adapter for actual Winch controller implementation."""

    def __init__(self, controller):
        """
        Initialize adapter.
        
        Args:
            controller: Actual Winch controller instance
        """
        self._controller = controller

    def move_increment(self, length: int, speed: int, acceleration: int = 30) -> None:
        """Move winch by incremental distance."""
        if not self._controller:
            raise ControllerNotAvailable("Winch controller not available")
        self._controller.move_increment_with_accel(int(length), int(speed), int(acceleration))

    def move_absolute(self, length: int, speed: int, acceleration: int = 30) -> None:
        """Move winch to absolute position."""
        if not self._controller:
            raise ControllerNotAvailable("Winch controller not available")
        self._controller.move_absolute_with_accel(int(length), int(speed), int(acceleration))

    def get_cable_length(self) -> float:
        """Get current cable length in mm."""
        if not self._controller:
            raise ControllerNotAvailable("Winch controller not available")
        return self._controller.get_cable_length()


class HardwareControllers:
    """Container for hardware controller instances."""

    def __init__(
        self,
        teensy_controller: Optional[ITeensyController] = None,
        winch_controller: Optional[IWinchController] = None
    ):
        """
        Initialize hardware controllers.
        
        Args:
            teensy_controller: Teensy controller instance
            winch_controller: Winch controller instance
        """
        self.teensy = teensy_controller
        self.winch = winch_controller

    @classmethod
    def from_robot_controller(cls, robot_controller):
        """
        Create HardwareControllers from robot controller instance.
        
        Args:
            robot_controller: ROS2 robot controller with teensy_controller, esp32_valve_controller, and winch_controller
            
        Returns:
            HardwareControllers instance
        """
        teensy = None
        winch = None

        if hasattr(robot_controller, 'teensy_controller') and robot_controller.teensy_controller:
            valve_controller = getattr(robot_controller, 'esp32_valve_controller', None)
            teensy = TeensyControllerAdapter(robot_controller.teensy_controller, valve_controller)

        if hasattr(robot_controller, 'winch_controller') and robot_controller.winch_controller:
            winch = WinchControllerAdapter(robot_controller.winch_controller)

        return cls(teensy, winch)

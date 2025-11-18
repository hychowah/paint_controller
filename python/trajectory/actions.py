#!/usr/bin/env python3
"""
Action handler registry for trajectory execution.

Provides pluggable action handlers with clean interface and error handling.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable
from .hardware import HardwareControllers, ControllerNotAvailable


class ActionHandler(ABC):
    """Base class for action handlers."""

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> None:
        """
        Execute the action.
        
        Args:
            params: Action parameters from YAML
        """
        pass

    @abstractmethod
    def estimate_duration(self, params: Dict[str, Any]) -> float:
        """
        Estimate action duration in seconds.
        
        Args:
            params: Action parameters from YAML
            
        Returns:
            Estimated duration in seconds
        """
        pass


class WinchIncrementHandler(ActionHandler):
    """Handler for incremental winch movement."""

    def __init__(self, hardware: HardwareControllers, logger=None):
        self.hardware = hardware
        self.logger = logger

    def execute(self, params: Dict[str, Any]) -> None:
        length = params.get("length", 0)
        speed = params.get("speed", 1)
        
        if not self.hardware.winch:
            raise ControllerNotAvailable("Winch controller not available")
        
        self.hardware.winch.move_increment(int(length), int(speed))
        if self.logger:
            self.logger.debug(f"Winch moved increment: {length}mm at {speed}mm/s")

    def estimate_duration(self, params: Dict[str, Any]) -> float:
        length = abs(params.get("length", 0))
        speed = params.get("speed", 1)
        return (length / speed) if speed > 0 else 0.0


class WinchAbsoluteHandler(ActionHandler):
    """Handler for absolute winch positioning."""

    def __init__(self, hardware: HardwareControllers, logger=None):
        self.hardware = hardware
        self.logger = logger
        self._last_estimated_time = 0.0

    def execute(self, params: Dict[str, Any]) -> None:
        length = params.get("length", 0)
        speed = params.get("speed", 1)
        
        if not self.hardware.winch:
            raise ControllerNotAvailable("Winch controller not available")
        
        current_length = self.hardware.winch.get_cable_length()
        distance = abs(length - current_length)
        
        self.hardware.winch.move_absolute(int(length), int(speed))
        
        # Store estimated time for later use
        self._last_estimated_time = (distance / speed) if speed > 0 else 0.0
        
        if self.logger:
            self.logger.info(
                f"Winch moving to {length}mm at {speed}mm/s "
                f"(distance={distance:.0f}mm, est={self._last_estimated_time:.1f}s)"
            )

    def estimate_duration(self, params: Dict[str, Any]) -> float:
        """
        Estimate duration based on target position and speed.
        Note: This is an approximation since we don't know current position at schedule time.
        """
        length = params.get("length", 0)
        speed = params.get("speed", 1)
        # Assume worst case: full distance from zero
        return (abs(length) / speed) if speed > 0 else 0.0
    
    def get_last_estimated_time(self) -> float:
        """Get the actual estimated time from last execution."""
        return self._last_estimated_time


class ValveTurnHandler(ActionHandler):
    """Handler for valve turn control."""

    def __init__(self, hardware: HardwareControllers, logger=None):
        self.hardware = hardware
        self.logger = logger

    def execute(self, params: Dict[str, Any]) -> None:
        turn_value = params.get("turn_value", 0.0)
        
        if not self.hardware.teensy:
            raise ControllerNotAvailable("Teensy controller not available")
        
        self.hardware.teensy.set_valve_turn(float(turn_value))
        if self.logger:
            self.logger.debug(f"Valve turn set to {turn_value}")

    def estimate_duration(self, params: Dict[str, Any]) -> float:
        return 0.5  # Valve operations are fast


class SprayGimbalHandler(ActionHandler):
    """Handler for spray gun gimbal control."""

    def __init__(self, hardware: HardwareControllers, logger=None):
        self.hardware = hardware
        self.logger = logger

    def execute(self, params: Dict[str, Any]) -> None:
        angle = params.get("angle", 0)
        speed = params.get("speed", 10)
        
        if not self.hardware.teensy:
            raise ControllerNotAvailable("Teensy controller not available")
        
        self.hardware.teensy.set_spray_gun_gimbal_angle(float(angle), float(speed))
        if self.logger:
            self.logger.debug(f"Spray gimbal set to {angle}° at {speed}°/s")

    def estimate_duration(self, params: Dict[str, Any]) -> float:
        angle = abs(params.get("angle", 0))
        speed = params.get("speed", 10)
        return (angle / speed) if speed > 0 else 0.0


class ArmExtendHandler(ActionHandler):
    """Handler for arm extension."""

    def __init__(self, hardware: HardwareControllers, logger=None, ros_node=None):
        self.hardware = hardware
        self.logger = logger
        self.ros_node = ros_node

    def execute(self, params: Dict[str, Any]) -> None:
        distance = params.get("distance", 0)
        
        if not self.hardware.teensy:
            raise ControllerNotAvailable("Teensy controller not available")
        
        self.hardware.teensy.extend_arm(int(distance))
        
        # Show popup if ROS node available
        if self.ros_node and hasattr(self.ros_node, 'show_info_popup'):
            self.ros_node.show_info_popup(
                "Extending Arm",
                f"Extending arm to {distance} mm"
            )
        
        if self.logger:
            self.logger.debug(f"Arm extended to {distance}mm")

    def estimate_duration(self, params: Dict[str, Any]) -> float:
        return 2.0  # Arm extension takes about 2 seconds


class EFForceHandler(ActionHandler):
    """Handler for end effector force control."""

    def __init__(self, hardware: HardwareControllers, logger=None, ros_node=None):
        self.hardware = hardware
        self.logger = logger
        self.ros_node = ros_node

    def execute(self, params: Dict[str, Any]) -> None:
        fx = params.get("fx", 0.0)
        fy = params.get("fy", 0.0)
        
        if not self.hardware.teensy:
            raise ControllerNotAvailable("Teensy controller not available")
        
        self.hardware.teensy.set_ef_force(float(fx), float(fy))
        
        # Show info via ROS node if available
        if self.ros_node and hasattr(self.ros_node, 'get_logger'):
            self.ros_node.get_logger().info(f"Sent EF force: Fx={fx}, Fy={fy}")
        
        if self.logger:
            self.logger.debug(f"EF force set to Fx={fx}, Fy={fy}")

    def estimate_duration(self, params: Dict[str, Any]) -> float:
        return 1.5  # Force application takes about 1.5 seconds


class ActionRegistry:
    """Registry for action handlers."""

    def __init__(self, hardware: HardwareControllers, logger=None, ros_node=None):
        """
        Initialize action registry.
        
        Args:
            hardware: Hardware controllers instance
            logger: Optional logger
            ros_node: Optional ROS node for UI interactions
        """
        self._handlers: Dict[str, ActionHandler] = {}
        self._hardware = hardware
        self._logger = logger
        self._ros_node = ros_node
        
        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default action handlers."""
        self.register("winch_increment", WinchIncrementHandler(self._hardware, self._logger))
        self.register("winch_absolute", WinchAbsoluteHandler(self._hardware, self._logger))
        self.register("winch_move_absolute", WinchAbsoluteHandler(self._hardware, self._logger))
        self.register("valve_turn", ValveTurnHandler(self._hardware, self._logger))
        self.register("spray_gimbal", SprayGimbalHandler(self._hardware, self._logger))
        self.register("arm_extend", ArmExtendHandler(self._hardware, self._logger, self._ros_node))
        self.register("ef_force", EFForceHandler(self._hardware, self._logger, self._ros_node))
        
        # Legacy aliases
        self.register("teensy_gimbal", SprayGimbalHandler(self._hardware, self._logger))
        self.register("teensy_arm_extend", ArmExtendHandler(self._hardware, self._logger, self._ros_node))

    def register(self, action_type: str, handler: ActionHandler) -> None:
        """
        Register an action handler.
        
        Args:
            action_type: Action type identifier
            handler: Handler instance
        """
        self._handlers[action_type] = handler

    def get_handler(self, action_type: str) -> Optional[ActionHandler]:
        """
        Get handler for action type.
        
        Args:
            action_type: Action type identifier
            
        Returns:
            Handler instance or None if not found
        """
        return self._handlers.get(action_type)

    def has_handler(self, action_type: str) -> bool:
        """Check if handler exists for action type."""
        return action_type in self._handlers

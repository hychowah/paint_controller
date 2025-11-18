#!/usr/bin/env python3
"""
Trajectory executor module for paint controller.

Handles YAML trajectory loading and sequential action execution with time-based scheduling.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import yaml

from PySide6.QtCore import QThread, Signal


class ExecutionState(Enum):
    """Trajectory execution state."""
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    COMPLETED = 3
    ERROR = 4


class TrajectoryExecutionThread(QThread):
    """QThread for executing trajectory actions."""
    
    execution_finished = Signal()
    execution_error = Signal(str)
    
    def __init__(self, executor, actions):
        """Initialize execution thread."""
        super().__init__()
        self.executor = executor
        self.actions = actions
        self._stop_requested = False
    
    def run(self):
        """Run trajectory execution."""
        try:
            self.executor._execute_actions(self.actions)
            self.execution_finished.emit()
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            self.execution_error.emit(error_msg)
    
    def request_stop(self):
        """Request thread to stop."""
        self._stop_requested = True
    
    def is_stop_requested(self):
        """Check if stop was requested."""
        return self._stop_requested


@dataclass
class ScheduledAction:
    """Action scheduled for execution with timing information."""
    action_index: int
    action_config: Dict[str, Any]
    scheduled_time: float  # Absolute time when action should execute
    reference_action_index: Optional[int] = None  # Index of action this timing references
    reference_arrival_time: Optional[float] = None  # Estimated arrival time of reference action


class TrajectoryExecutor:
    """
    Executes trajectories from YAML files with time-based sequencing.
    
    Handles:
    - Sequential action execution
    - Time-based delays (wait_after, delay_before)
    - Winch feedback-based timing (for needle valve relative timing)
    - Publisher-based ROS2 topic communication
    """

    def __init__(self, ros_node, logger=None):
        """
        Initialize trajectory executor.

        Args:
            ros_node: ROS2 node instance (RobotController) with access to controllers
            logger: Optional logger instance (uses ros_node.get_logger() if None)
        """
        self.ros_node = ros_node
        self._robot_controller = ros_node  # Store robot controller reference
        self.logger = logger or ros_node.get_logger()

        self.current_trajectory: Optional[Dict[str, Any]] = None
        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1  # Track currently executing action
        self.execution_thread: Optional[TrajectoryExecutionThread] = None
        self._stop_requested = False

        # Callback map for action execution
        self.action_handlers: Dict[str, Callable] = {
            "winch_increment": self._handle_winch_increment,
            "winch_absolute": self._handle_winch_absolute,
            "valve_turn": self._handle_valve_turn,
            "spray_gimbal": self._handle_spray_gimbal,
            "arm_extend": self._handle_arm_extend,
            "ef_force": self._handle_ef_force,
            # Legacy type names for backward compatibility
            "teensy_relay": self._handle_winch_increment,  # Map to dummy handler
            "teensy_gimbal": self._handle_spray_gimbal,
            "teensy_arm_extend": self._handle_arm_extend,
            "teensy_propeller": self._handle_winch_increment,  # Map to dummy handler
            "teensy_spray_trigger": self._handle_winch_increment,  # Map to dummy handler
            "winch_move_absolute": self._handle_winch_absolute,
        }

        # Winch state tracking for arrival time estimation
        self.winch_current_position = 0.0
        self.winch_target_position = 0.0
        self.winch_speed = 0.0
        self.winch_move_start_time = None

    def load_trajectory(self, yaml_path: str) -> bool:
        """
        Load trajectory from YAML file.

        Args:
            yaml_path: Path to trajectory YAML file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(yaml_path, 'r') as f:
                self.current_trajectory = yaml.safe_load(f)
            self.logger.info(f"Loaded trajectory: {self.current_trajectory.get('name', 'unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load trajectory from {yaml_path}: {e}")
            return False

    def play(self) -> bool:
        """
        Start executing the current trajectory.

        Returns:
            True if execution started, False if already running or no trajectory loaded
        """
        if self.current_state == ExecutionState.RUNNING:
            self.logger.warn("Trajectory already running")
            return False

        if not self.current_trajectory:
            self.logger.error("No trajectory loaded")
            return False

        self.current_state = ExecutionState.RUNNING
        self._stop_requested = False

        # Start execution in QThread
        actions = self.current_trajectory.get("actions", [])
        self.execution_thread = TrajectoryExecutionThread(self, actions)
        self.execution_thread.execution_finished.connect(self._on_execution_finished)
        self.execution_thread.execution_error.connect(self._on_execution_error)
        self.execution_thread.start()

        return True

    def pause(self) -> bool:
        """Pause trajectory execution."""
        if self.current_state != ExecutionState.RUNNING:
            return False
        self.current_state = ExecutionState.PAUSED
        return True

    def resume(self) -> bool:
        """Resume paused trajectory execution."""
        if self.current_state != ExecutionState.PAUSED:
            return False
        self.current_state = ExecutionState.RUNNING
        return True

    def stop(self) -> bool:
        """Stop trajectory execution."""
        if self.current_state == ExecutionState.IDLE:
            return False
        self._stop_requested = True
        if self.execution_thread:
            self.execution_thread.request_stop()
            self.execution_thread.wait(5000)  # Wait max 5 seconds
        self.current_state = ExecutionState.IDLE
        return True

    def _on_execution_finished(self) -> None:
        """Handle execution completion."""
        self.current_state = ExecutionState.COMPLETED
        self.logger.info("Trajectory execution completed")

    def _on_execution_error(self, error_msg: str) -> None:
        """Handle execution error."""
        self.current_state = ExecutionState.ERROR
        self.logger.error(error_msg)

    def _execute(self) -> None:
        """Execute the trajectory (runs in QThread)."""
        try:
            if not self.current_trajectory:
                return

            actions = self.current_trajectory.get("actions", [])
            if not actions:
                self.logger.warn("Trajectory has no actions")
                self.current_state = ExecutionState.COMPLETED
                return

            self._execute_actions(actions)

            if not self._stop_requested:
                self.current_state = ExecutionState.COMPLETED
                self.logger.info("Trajectory execution completed")
            else:
                self.logger.info("Trajectory execution stopped")

        except Exception as e:
            self.logger.error(f"Fatal error during trajectory execution: {e}")
            self.current_state = ExecutionState.ERROR

    def _execute_actions(self, actions: List[Dict[str, Any]]) -> None:
        """Execute actions from trajectory."""
        # Build scheduled action queue
        scheduled_actions = self._build_schedule(actions)

        start_time = time.time()
        action_index = 0

        while action_index < len(scheduled_actions) and not self._stop_requested:
            # Handle pause
            while self.current_state == ExecutionState.PAUSED and not self._stop_requested:
                time.sleep(0.1)

            if self._stop_requested:
                break

            scheduled = scheduled_actions[action_index]
            current_time = time.time() - start_time

            # Wait until scheduled time
            wait_time = scheduled.scheduled_time - current_time
            if wait_time > 0:
                time.sleep(min(wait_time, 0.1))  # Sleep in 100ms chunks for responsiveness
                continue

            # Update current action index
            self.current_action_index = action_index

            # Execute action
            action_name = scheduled.action_config.get("name", f"action_{action_index}")
            action_type = scheduled.action_config.get("type")

            try:
                self.logger.info(f"Executing: {action_name} (type: {action_type})")
                handler = self.action_handlers.get(action_type)

                if handler:
                    handler(scheduled.action_config)
                else:
                    self.logger.warn(f"No handler for action type: {action_type}")

            except Exception as e:
                self.logger.error(f"Error executing action {action_name}: {e}")
                self.current_state = ExecutionState.ERROR
                raise

            action_index += 1

        # Reset action index when done
        self.current_action_index = -1

    def _build_schedule(self, actions: List[Dict[str, Any]]) -> List[ScheduledAction]:
        """
        Build execution schedule from actions list.

        Handles:
        - Sequential execution (default)
        - delay_before: positive = after previous, negative = before previous completion
        - wait_after: duration to assume action takes

        Args:
            actions: List of action configurations from YAML

        Returns:
            List of ScheduledAction with absolute execution times
        """
        scheduled = []
        current_time = 0.0

        for idx, action in enumerate(actions):
            action_name = action.get("name", f"action_{idx}")
            wait_after = action.get("wait_after", 1000)  # Default 1 second
            delay_before = action.get("delay_before", 0)

            # Calculate action execution time
            if delay_before > 0:
                # Positive delay: execute N ms after previous action completes
                scheduled_time = current_time + delay_before
            elif delay_before < 0:
                # Negative delay: execute N ms before previous action completes
                # This is relative to the previous action's arrival/completion
                if idx > 0:
                    prev_action = scheduled[-1]
                    # If previous is winch move, estimate arrival time
                    if prev_action.action_config.get("type") == "winch_move_absolute":
                        prev_params = prev_action.action_config.get("params", {})
                        distance = prev_params.get("distance", 0)
                        speed = prev_params.get("speed", 1)  # mm/s
                        arrival_time = (distance / speed) * 1000 if speed > 0 else 0
                        scheduled_time = prev_action.scheduled_time + arrival_time + delay_before
                    else:
                        # For non-winch actions, delay relative to their completion
                        scheduled_time = current_time + delay_before
                else:
                    # No previous action, use from start
                    scheduled_time = delay_before if delay_before < 0 else current_time
            else:
                # No delay specified, execute at current time
                scheduled_time = current_time

            # Ensure scheduled time is never before start
            scheduled_time = max(0, scheduled_time)

            scheduled.append(
                ScheduledAction(
                    action_index=idx,
                    action_config=action,
                    scheduled_time=scheduled_time,
                )
            )

            # Update current time for next action
            current_time = scheduled_time + (wait_after / 1000.0)  # Convert ms to seconds

        return scheduled

    # Action handlers - use controller methods instead of raw ROS2 publishing
    def _handle_winch_increment(self, action: Dict[str, Any]) -> None:
        """Handle winch incremental movement."""
        params = action.get("params", {})
        length = params.get("length", 0)
        speed = params.get("speed", 1)

        try:
            self._robot_controller.winch_controller.moveIncrement(int(length), int(speed))
            self.logger.debug(f"Winch moved increment of {length}mm at {speed}mm/s")
        except Exception as e:
            self.logger.error(f"Error moving winch increment: {e}")

    def _handle_winch_absolute(self, action: Dict[str, Any]) -> None:
        """Handle winch absolute position movement."""
        params = action.get("params", {})
        length = params.get("length", 0)
        speed = params.get("speed", 1)

        try:
            self._robot_controller.winch_controller.moveAbsolute(int(length), int(speed))
            self.logger.debug(f"Winch moving to {length}mm at {speed}mm/s")

            # Track winch state for arrival time estimation
            self.winch_target_position = length
            self.winch_speed = speed
            self.winch_move_start_time = time.time()
        except Exception as e:
            self.logger.error(f"Error moving winch absolute: {e}")

    def _handle_valve_turn(self, action: Dict[str, Any]) -> None:
        """Handle valve turn control."""
        params = action.get("params", {})
        turn_value = params.get("turn_value", 0.0)

        try:
            self._robot_controller.teensy_controller.setValveTurn(float(turn_value))
            self.logger.debug(f"Valve turn set to {turn_value}")
        except Exception as e:
            self.logger.error(f"Error setting valve turn: {e}")

    def _handle_spray_gimbal(self, action: Dict[str, Any]) -> None:
        """Handle spray gun gimbal angle control."""
        params = action.get("params", {})
        angle = params.get("angle", 0)
        speed = params.get("speed", 10)

        try:
            self._robot_controller.teensy_controller.setSprayGunGimbalAngle(float(angle), float(speed))
            self.logger.debug(f"Spray gimbal set to angle={angle}° speed={speed}°/s")
        except Exception as e:
            self.logger.error(f"Error setting spray gimbal angle: {e}")

    def _handle_arm_extend(self, action: Dict[str, Any]) -> None:
        """Handle arm extension control."""
        params = action.get("params", {})
        distance = params.get("distance", 0)

        try:
            self._robot_controller.teensy_controller.extendArm(int(distance))
            self.logger.debug(f"Arm extended to {distance}mm")
        except Exception as e:
            self.logger.error(f"Error extending arm: {e}")

    def _handle_ef_force(self, action: Dict[str, Any]) -> None:
        """Handle end effector force control."""
        params = action.get("params", {})
        fx = params.get("fx", 0.0)
        fy = params.get("fy", 0.0)

        try:
            self._robot_controller.teensy_controller.set_ef_force(float(fx), float(fy))
            self.logger.debug(f"EF force set to Fx={fx}, Fy={fy}")
        except Exception as e:
            self.logger.error(f"Error setting EF force: {e}")

    def cleanup(self) -> None:
        """Clean up executor resources."""
        self.stop()

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

# ROS2 message imports (from research)
from std_msgs.msg import Float32, UInt16


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
            ros_node: ROS2 node instance for creating publishers
            logger: Optional logger instance (uses ros_node.get_logger() if None)
        """
        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        self.current_trajectory: Optional[Dict[str, Any]] = None
        self.current_state = ExecutionState.IDLE
        self.execution_thread: Optional[TrajectoryExecutionThread] = None
        self._stop_requested = False

        # Publisher cache: topic -> publisher
        self.publishers: Dict[str, Any] = {}

        # Action type to topic mapping
        self.action_type_map = {
            "teensy_relay": ("teensy/relay/cmd", "std_msgs/UInt16"),
            "teensy_gimbal": ("teensy/spray_gun/gimbal/angle/cmd", "std_msgs/Float32MultiArray"),
            "teensy_arm_extend": ("teensy/arm/extend/cmd", "std_msgs/Float32"),
            "teensy_propeller": ("teensy/prop/left/pwm/cmd", "std_msgs/UInt16"),  # Simplified
            "teensy_spray_trigger": ("teensy/spray_gun/trigger/cmd", "std_msgs/UInt16"),
            "winch_move_absolute": ("winch/move/absolute/cmd", "paint_interfaces/WinchMovement"),
        }

        # Callback map for action execution
        self.action_handlers: Dict[str, Callable] = {
            "teensy_relay": self._handle_teensy_relay,
            "teensy_gimbal": self._handle_teensy_gimbal,
            "teensy_arm_extend": self._handle_teensy_arm_extend,
            "teensy_propeller": self._handle_teensy_propeller,
            "teensy_spray_trigger": self._handle_teensy_spray_trigger,
            "winch_move_absolute": self._handle_winch_move_absolute,
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

    # Action handlers
    def _handle_teensy_relay(self, action: Dict[str, Any]) -> None:
        """Handle teensy relay control."""
        params = action.get("params", {})
        relay_id = params.get("relay_id", 1)
        enabled = params.get("enabled", True)

        # Create publisher if needed
        topic = "teensy/relay/cmd"
        if topic not in self.publishers:
            self.publishers[topic] = self.ros_node.create_publisher(UInt16, topic, 10)

        # Publish command (simplified: 1 for on, 0 for off)
        msg = UInt16()
        msg.data = 1 if enabled else 0
        self.publishers[topic].publish(msg)

    def _handle_teensy_gimbal(self, action: Dict[str, Any]) -> None:
        """Handle gimbal angle control."""
        params = action.get("params", {})
        angle = params.get("angle", 0)
        speed = params.get("speed", 10)

        # Create publisher if needed
        topic = "teensy/spray_gun/gimbal/angle/cmd"
        if topic not in self.publishers:
            from std_msgs.msg import Float32MultiArray

            self.publishers[topic] = self.ros_node.create_publisher(
                Float32MultiArray, topic, 10
            )

        # Publish [angle, speed]
        msg = Float32MultiArray()
        msg.data = [float(angle), float(speed)]
        self.publishers[topic].publish(msg)

    def _handle_teensy_arm_extend(self, action: Dict[str, Any]) -> None:
        """Handle arm extension control."""
        params = action.get("params", {})
        distance = params.get("distance", 0)

        topic = "teensy/arm/extend/cmd"
        if topic not in self.publishers:
            self.publishers[topic] = self.ros_node.create_publisher(Float32, topic, 10)

        msg = Float32()
        msg.data = float(distance)
        self.publishers[topic].publish(msg)

    def _handle_teensy_propeller(self, action: Dict[str, Any]) -> None:
        """Handle propeller control."""
        params = action.get("params", {})
        left_pwm = params.get("left_pwm", 0)
        right_pwm = params.get("right_pwm", 0)

        # Publish left propeller
        left_topic = "teensy/prop/left/pwm/cmd"
        if left_topic not in self.publishers:
            self.publishers[left_topic] = self.ros_node.create_publisher(UInt16, left_topic, 10)

        left_msg = UInt16()
        left_msg.data = int(left_pwm)
        self.publishers[left_topic].publish(left_msg)

        # Publish right propeller
        right_topic = "teensy/prop/right/pwm/cmd"
        if right_topic not in self.publishers:
            self.publishers[right_topic] = self.ros_node.create_publisher(
                UInt16, right_topic, 10
            )

        right_msg = UInt16()
        right_msg.data = int(right_pwm)
        self.publishers[right_topic].publish(right_msg)

    def _handle_teensy_spray_trigger(self, action: Dict[str, Any]) -> None:
        """Handle spray trigger (needle valve) control."""
        params = action.get("params", {})
        trigger_value = params.get("trigger_value", 0)

        topic = "teensy/spray_gun/trigger/cmd"
        if topic not in self.publishers:
            self.publishers[topic] = self.ros_node.create_publisher(UInt16, topic, 10)

        msg = UInt16()
        msg.data = int(trigger_value)
        self.publishers[topic].publish(msg)

    def _handle_winch_move_absolute(self, action: Dict[str, Any]) -> None:
        """Handle winch absolute position movement."""
        params = action.get("params", {})
        distance = params.get("distance", 0)
        speed = params.get("speed", 1)

        topic = "winch/move/absolute/cmd"
        if topic not in self.publishers:
            # Assuming paint_interfaces/WinchMovement exists
            # For now, publish as generic message with two Float32 values
            from std_msgs.msg import Float32MultiArray

            self.publishers[topic] = self.ros_node.create_publisher(
                Float32MultiArray, topic, 10
            )

        msg = Float32MultiArray()
        msg.data = [float(distance), float(speed)]
        self.publishers[topic].publish(msg)

        # Track winch state for arrival time estimation
        self.winch_target_position = distance
        self.winch_speed = speed
        self.winch_move_start_time = time.time()

    def cleanup(self) -> None:
        """Clean up executor resources."""
        self.stop()
        for publisher in self.publishers.values():
            try:
                self.ros_node.destroy_publisher(publisher)
            except Exception as e:
                self.logger.warn(f"Error destroying publisher: {e}")
        self.publishers.clear()

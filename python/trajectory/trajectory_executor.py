#!/usr/bin/env python3
"""
Refactored trajectory executor with clean architecture.

Key improvements:
- Separated scheduling logic
- Hardware abstraction layer
- Pluggable action handlers
- Cleaner state management
- Minimal logging
"""

import time
import yaml
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime

from PySide6.QtCore import QThread, Signal

from .scheduler import ActionScheduler, ScheduledAction
from .hardware import HardwareControllers
from .actions import ActionRegistry


class ExecutionState(Enum):
    """Trajectory execution state."""
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    COMPLETED = 3
    ERROR = 4


class TrajectoryExecutionThread(QThread):
    """Thread for executing trajectory actions."""
    
    execution_finished = Signal()
    execution_error = Signal(str)
    
    def __init__(self, executor, scheduled_actions: List[ScheduledAction]):
        super().__init__()
        self.executor = executor
        self.scheduled_actions = scheduled_actions
        self._stop_requested = False
    
    def run(self):
        """Run trajectory execution."""
        try:
            self.executor._execute_scheduled_actions(self.scheduled_actions)
            if not self._stop_requested:
                self.execution_finished.emit()
        except Exception as e:
            self.execution_error.emit(str(e))
    
    def request_stop(self):
        """Request thread to stop."""
        self._stop_requested = True
    
    def is_stop_requested(self) -> bool:
        """Check if stop was requested."""
        return self._stop_requested


class TrajectoryExecutor:
    """
    Executes trajectories with improved architecture.
    
    Features:
    - Clean separation of concerns (scheduling, execution, hardware)
    - Pluggable action handlers
    - Support for parallel and sequential actions
    - Proper error handling and state management
    """

    def __init__(self, ros_node, logger=None):
        """
        Initialize trajectory executor.

        Args:
            ros_node: ROS2 node instance with access to controllers
            logger: Optional logger instance
        """
        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        # Initialize subsystems
        self.hardware = HardwareControllers.from_robot_controller(ros_node)
        self.action_registry = ActionRegistry(self.hardware, self.logger, ros_node)
        self.scheduler = ActionScheduler(self.logger, self.hardware)

        # State management
        self.current_trajectory: Optional[Dict[str, Any]] = None
        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1
        self.execution_thread: Optional[TrajectoryExecutionThread] = None
        self._stop_requested = False

    def load_trajectory(self, yaml_path: str) -> bool:
        """
        Load trajectory from YAML file.

        Args:
            yaml_path: Path to trajectory YAML file

        Returns:
            True if loaded successfully
        """
        try:
            with open(yaml_path, 'r') as f:
                self.current_trajectory = yaml.safe_load(f)
            
            name = self.current_trajectory.get('name', 'unknown')
            self.logger.info(f"Loaded trajectory: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load trajectory: {e}")
            return False

    def play(self) -> bool:
        """
        Start executing the current trajectory.

        Returns:
            True if execution started successfully
        """
        if self.current_state == ExecutionState.RUNNING:
            self.logger.warn("Trajectory already running")
            return False

        if not self.current_trajectory:
            self.logger.error("No trajectory loaded")
            return False

        actions = self.current_trajectory.get("actions", [])
        if not actions:
            self.logger.warn("Trajectory has no actions")
            return False

        try:
            # Build schedule
            scheduled_actions = self.scheduler.build_schedule(actions)
            
            # Start execution thread
            self.current_state = ExecutionState.RUNNING
            self._stop_requested = False
            
            self.execution_thread = TrajectoryExecutionThread(self, scheduled_actions)
            self.execution_thread.execution_finished.connect(self._on_execution_finished)
            self.execution_thread.execution_error.connect(self._on_execution_error)
            self.execution_thread.start()
            
            self.logger.info(f"Started trajectory with {len(scheduled_actions)} actions")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start trajectory: {e}")
            self.current_state = ExecutionState.ERROR
            return False

    def pause(self) -> bool:
        """Pause trajectory execution."""
        if self.current_state != ExecutionState.RUNNING:
            return False
        self.current_state = ExecutionState.PAUSED
        self.logger.info("Trajectory paused")
        return True

    def resume(self) -> bool:
        """Resume paused trajectory execution."""
        if self.current_state != ExecutionState.PAUSED:
            return False
        self.current_state = ExecutionState.RUNNING
        self.logger.info("Trajectory resumed")
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
        self.current_action_index = -1
        self.logger.info("Trajectory stopped")
        return True

    def _on_execution_finished(self) -> None:
        """Handle execution completion."""
        self.current_state = ExecutionState.COMPLETED
        self.current_action_index = -1
        self.logger.info("Trajectory completed successfully")
        # Note: State change will be detected by runner's state monitoring

    def _on_execution_error(self, error_msg: str) -> None:
        """Handle execution error."""
        self.current_state = ExecutionState.ERROR
        self.current_action_index = -1
        self.logger.error(f"Trajectory execution error: {error_msg}")

    def _execute_scheduled_actions(self, scheduled_actions: List[ScheduledAction]) -> None:
        """
        Execute scheduled actions in time order.
        
        Args:
            scheduled_actions: List of scheduled actions sorted by time
        """
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
                time.sleep(min(wait_time, 0.1))
                continue

            # Execute action
            self.current_action_index = action_index
            self._execute_action(scheduled)

            # Determine wait time until next action or completion
            wait_until = self._calculate_wait_until(
                scheduled, 
                action_index, 
                scheduled_actions,
                start_time
            )
            
            # Wait
            self._wait_with_pause(wait_until, start_time)

            action_index += 1

        # Reset state
        self.current_action_index = -1

    def _execute_action(self, scheduled: ScheduledAction) -> None:
        """
        Execute a single scheduled action.
        
        Args:
            scheduled: Scheduled action to execute
        """
        action_name = scheduled.action_config.get("name", f"action_{scheduled.action_index}")
        action_type = scheduled.action_config.get("type")
        params = scheduled.action_config.get("params", {})

        try:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.logger.info(f"[{timestamp}] Executing: {action_name}")

            handler = self.action_registry.get_handler(action_type)
            if not handler:
                self.logger.warn(f"No handler for action type: {action_type}")
                return

            handler.execute(params)

        except Exception as e:
            self.logger.error(f"Error executing {action_name}: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.current_state = ExecutionState.ERROR
            raise

    def _calculate_wait_until(
        self,
        current_scheduled: ScheduledAction,
        current_index: int,
        scheduled_actions: List[ScheduledAction],
        start_time: float
    ) -> float:
        """
        Calculate absolute time to wait until (either next action or current completion).
        
        Returns:
            Absolute time to wait until (relative to start_time)
        """
        # Default: wait for current action to complete
        wait_until = current_scheduled.scheduled_time + current_scheduled.estimated_duration

        # Check if next action should execute sooner
        if current_index + 1 < len(scheduled_actions):
            next_action = scheduled_actions[current_index + 1]
            if next_action.scheduled_time < wait_until:
                wait_until = next_action.scheduled_time

        return wait_until

    def _wait_with_pause(self, wait_until: float, start_time: float) -> None:
        """
        Wait until specified time, handling pause state.
        
        Args:
            wait_until: Absolute time to wait until (relative to start_time)
            start_time: Execution start time
        """
        while time.time() - start_time < wait_until and not self._stop_requested:
            # Handle pause
            while self.current_state == ExecutionState.PAUSED and not self._stop_requested:
                time.sleep(0.1)
            
            if self._stop_requested:
                break
                
            time.sleep(0.05)  # Small sleep for responsiveness

    def cleanup(self) -> None:
        """Clean up executor resources."""
        self.stop()

    # Legacy compatibility methods
    def set_controllers(self, teensy_controller, winch_controller) -> None:
        """
        Set controller references (legacy compatibility).
        
        Args:
            teensy_controller: Teensy controller instance
            winch_controller: Winch controller instance
        """
        # Update hardware controllers
        from .hardware import TeensyControllerAdapter, WinchControllerAdapter
        
        if teensy_controller:
            self.hardware.teensy = TeensyControllerAdapter(teensy_controller)
        if winch_controller:
            self.hardware.winch = WinchControllerAdapter(winch_controller)

#!/usr/bin/env python3
"""
Refactored workflow executor with clean architecture.

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
    """WorkFlow execution state."""
    IDLE = 0
    RUNNING = 1
    PAUSED = 2
    COMPLETED = 3
    ERROR = 4


class WorkFlowExecutionThread(QThread):
    """Thread for executing workflow actions."""
    
    execution_finished = Signal()
    execution_error = Signal(str)
    
    def __init__(self, executor, scheduled_actions: List[ScheduledAction]):
        super().__init__()
        self.executor = executor
        self.scheduled_actions = scheduled_actions
        self._stop_requested = False
    
    def run(self):
        """Run workflow execution."""
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


class WorkFlowExecutor:
    """
    Executes workflows with improved architecture.
    
    Features:
    - Clean separation of concerns (scheduling, execution, hardware)
    - Pluggable action handlers
    - Support for parallel and sequential actions
    - Proper error handling and state management
    """

    def __init__(self, ros_node, logger=None):
        """
        Initialize workflow executor.

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
        self.current_workflow: Optional[Dict[str, Any]] = None
        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1
        self.execution_thread: Optional[WorkFlowExecutionThread] = None
        self._stop_requested = False
        
        # Position trigger tracking
        self._pending_position_triggers: List[ScheduledAction] = []  # Not yet activated
        self._active_position_triggers: Dict[str, tuple] = {}  # ref_id -> (action, last_position)
        self._fired_position_triggers: set = set()  # action_ids that have fired
        
        # Winch completion tracking
        self._active_winch_action: Optional[ScheduledAction] = None  # Currently executing winch action
        self._winch_position_tolerance: float = 50.0  # mm tolerance for position-based completion

    def load_workflow(self, yaml_path: str) -> bool:
        """
        Load workflow from YAML file.

        Args:
            yaml_path: Path to workflow YAML file

        Returns:
            True if loaded successfully
        """
        try:
            with open(yaml_path, 'r') as f:
                self.current_workflow = yaml.safe_load(f)
            
            name = self.current_workflow.get('name', 'unknown')
            self.logger.info(f"Loaded workflow: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow: {e}")
            return False

    def play(self) -> bool:
        """
        Start executing the current workflow.

        Returns:
            True if execution started successfully
        """
        if self.current_state == ExecutionState.RUNNING:
            self.logger.warn("WorkFlow already running")
            return False

        if not self.current_workflow:
            self.logger.error("No workflow loaded")
            return False

        actions = self.current_workflow.get("actions", [])
        if not actions:
            self.logger.warn("WorkFlow has no actions")
            return False

        try:
            # Build schedule
            all_scheduled = self.scheduler.build_schedule(actions)
            
            # Separate position-triggered actions from time-scheduled actions
            scheduled_actions = []
            self._pending_position_triggers = []
            self._active_position_triggers = {}
            self._fired_position_triggers = set()
            
            for action in all_scheduled:
                if action.is_position_triggered:
                    self._pending_position_triggers.append(action)
                    self.logger.debug(
                        f"Position trigger '{action.action_id}' will fire at {action.position_trigger_mm}mm "
                        f"during '{action.position_reference_action}'"
                    )
                else:
                    scheduled_actions.append(action)
            
            # Start execution thread
            self.current_state = ExecutionState.RUNNING
            self._stop_requested = False
            
            self.execution_thread = WorkFlowExecutionThread(self, scheduled_actions)
            self.execution_thread.execution_finished.connect(self._on_execution_finished)
            self.execution_thread.execution_error.connect(self._on_execution_error)
            self.execution_thread.start()
            
            total_actions = len(scheduled_actions) + len(self._pending_position_triggers)
            self.logger.info(f"Started workflow with {total_actions} actions ({len(self._pending_position_triggers)} position-triggered)")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start workflow: {e}")
            self.current_state = ExecutionState.ERROR
            return False

    def pause(self) -> bool:
        """Pause workflow execution."""
        if self.current_state != ExecutionState.RUNNING:
            return False
        self.current_state = ExecutionState.PAUSED
        self.logger.info("WorkFlow paused")
        return True

    def resume(self) -> bool:
        """Resume paused workflow execution."""
        if self.current_state != ExecutionState.PAUSED:
            return False
        self.current_state = ExecutionState.RUNNING
        self.logger.info("WorkFlow resumed")
        return True

    def stop(self) -> bool:
        """Stop workflow execution."""
        if self.current_state == ExecutionState.IDLE:
            return False
        
        self._stop_requested = True
        if self.execution_thread:
            self.execution_thread.request_stop()
            self.execution_thread.wait(5000)  # Wait max 5 seconds
        
        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1
        self.logger.info("WorkFlow stopped")
        return True

    def _on_execution_finished(self) -> None:
        """Handle execution completion."""
        self.current_state = ExecutionState.COMPLETED
        self.current_action_index = -1
        self.logger.info("WorkFlow completed successfully")
        # Note: State change will be detected by runner's state monitoring

    def _on_execution_error(self, error_msg: str) -> None:
        """Handle execution error."""
        self.current_state = ExecutionState.ERROR
        self.current_action_index = -1
        self.logger.error(f"WorkFlow execution error: {error_msg}")

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
            
            # Wait (pass current action ID for position trigger completion handling)
            self._wait_with_pause(wait_until, start_time, scheduled.action_id)

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

            # Activate any position triggers that reference this action
            self._activate_position_triggers_for(scheduled.action_id)
            
            # Track winch actions for position-based completion
            if scheduled.is_winch_action and scheduled.winch_target_mm is not None:
                self._active_winch_action = scheduled
                self.logger.debug(
                    f"Tracking winch action '{scheduled.action_id}' for position-based completion "
                    f"(target: {scheduled.winch_target_mm}mm)"
                )

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

    def _activate_position_triggers_for(self, reference_action_id: str) -> None:
        """
        Activate position triggers that reference the given action.
        
        Called when a reference action starts executing to begin position monitoring.
        
        Args:
            reference_action_id: ID of the action that just started
        """
        triggers_to_activate = []
        
        for trigger in self._pending_position_triggers:
            if trigger.position_reference_action == reference_action_id:
                triggers_to_activate.append(trigger)
        
        if not triggers_to_activate:
            return
        
        # Get current winch position to use as starting point
        try:
            current_position = self.hardware.winch.get_cable_length()
        except Exception as e:
            self.logger.error(f"Failed to get winch position for position triggers: {e}")
            current_position = 0.0
        
        for trigger in triggers_to_activate:
            self._pending_position_triggers.remove(trigger)
            self._active_position_triggers[trigger.action_id] = (trigger, current_position)
            self.logger.info(
                f"Position trigger '{trigger.action_id}' activated at {current_position:.0f}mm, "
                f"will fire when crossing {trigger.position_trigger_mm:.0f}mm"
            )

    def _check_position_triggers(self) -> None:
        """
        Check all active position triggers and fire any that have crossed their threshold.
        
        Called periodically (every 100ms) during execution wait loops.
        Uses crossing detection to handle both ascending and descending motion.
        """
        if not self._active_position_triggers:
            return
        
        try:
            current_position = self.hardware.winch.get_cable_length()
        except Exception as e:
            self.logger.warn(f"Failed to get winch position: {e}")
            return
        
        triggers_to_fire = []
        
        for action_id, (trigger, last_position) in list(self._active_position_triggers.items()):
            target = trigger.position_trigger_mm
            
            # Crossing detection: fire if position crossed the threshold in either direction
            crossed_ascending = last_position < target <= current_position
            crossed_descending = last_position > target >= current_position
            
            if crossed_ascending or crossed_descending:
                direction = "ascending" if crossed_ascending else "descending"
                self.logger.info(
                    f"Position trigger '{action_id}' fired at {current_position:.0f}mm "
                    f"(target={target:.0f}mm, {direction})"
                )
                triggers_to_fire.append(trigger)
            else:
                # Update last position for next check
                self._active_position_triggers[action_id] = (trigger, current_position)
        
        # Execute triggered actions
        for trigger in triggers_to_fire:
            self._execute_action(trigger)
            self._fired_position_triggers.add(trigger.action_id)
            del self._active_position_triggers[trigger.action_id]

    def _handle_reference_action_complete(self, reference_action_id: str) -> None:
        """
        Handle completion of a reference action - fire any unfired position triggers with warning.
        
        Args:
            reference_action_id: ID of the action that just completed
        """
        triggers_to_fire = []
        
        for action_id, (trigger, last_position) in list(self._active_position_triggers.items()):
            if trigger.position_reference_action == reference_action_id:
                triggers_to_fire.append((trigger, last_position))
        
        for trigger, last_position in triggers_to_fire:
            self.logger.warn(
                f"Position trigger '{trigger.action_id}' did not reach target "
                f"{trigger.position_trigger_mm:.0f}mm (last position: {last_position:.0f}mm). "
                f"Firing now with warning."
            )
            
            # Show warning popup
            if self.ros_node and hasattr(self.ros_node, 'show_popup'):
                self.ros_node.show_popup(
                    "Position Trigger Missed",
                    f"'{trigger.action_id}' fired late - didn't reach {trigger.position_trigger_mm:.0f}mm",
                    "error",
                    3000
                )
            
            # Execute the action anyway
            self._execute_action(trigger)
            self._fired_position_triggers.add(trigger.action_id)
            del self._active_position_triggers[trigger.action_id]

    def _check_winch_completion(self) -> bool:
        """
        Check if the active winch action has reached its target position.
        
        Returns:
            True if winch has reached target (within tolerance), False otherwise
        """
        if not self._active_winch_action:
            return True  # No active winch action, consider complete
        
        target = self._active_winch_action.winch_target_mm
        if target is None:
            return True
        
        try:
            current_position = self.hardware.winch.get_cable_length()
            distance_to_target = abs(current_position - target)
            
            if distance_to_target <= self._winch_position_tolerance:
                self.logger.info(
                    f"Winch action '{self._active_winch_action.action_id}' reached target "
                    f"{target:.0f}mm (current: {current_position:.0f}mm)"
                )
                self._active_winch_action = None
                return True
            
            return False
            
        except Exception as e:
            self.logger.warn(f"Failed to check winch position: {e}")
            return False

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

    def _wait_with_pause(
        self, 
        wait_until: float, 
        start_time: float,
        current_action_id: Optional[str] = None
    ) -> None:
        """
        Wait until specified time, handling pause state, position triggers, and winch completion.
        
        Args:
            wait_until: Absolute time to wait until (relative to start_time)
            start_time: Execution start time
            current_action_id: ID of the action currently being waited on (for position trigger completion)
        """
        last_position_check = 0.0
        position_check_interval = 0.1  # 10Hz polling
        
        # Check if there are active position triggers for this action
        def has_active_triggers_for_action() -> bool:
            if not current_action_id:
                return False
            for action_id, (trigger, _) in self._active_position_triggers.items():
                if trigger.position_reference_action == current_action_id:
                    return True
            return False
        
        # Wait until:
        # 1. Winch has reached target (if this is a winch action), AND
        # 2. All position triggers for this action have fired
        while not self._stop_requested:
            current_time_elapsed = time.time() - start_time
            has_active_triggers = has_active_triggers_for_action()
            winch_complete = self._check_winch_completion()
            
            # For winch actions: wait for position-based completion
            # For non-winch actions: use time-based wait
            if self._active_winch_action is None:
                # No active winch action - use time-based completion
                action_complete = current_time_elapsed >= wait_until
            else:
                # Active winch action - use position-based completion
                action_complete = winch_complete
            
            # Exit if: action complete AND no active position triggers for this action
            if action_complete and not has_active_triggers:
                break
            
            # Handle pause
            while self.current_state == ExecutionState.PAUSED and not self._stop_requested:
                time.sleep(0.1)
            
            if self._stop_requested:
                break
            
            # Check position triggers at 10Hz
            current_time = time.time()
            if current_time - last_position_check >= position_check_interval:
                self._check_position_triggers()
                last_position_check = current_time
                
            time.sleep(0.05)  # Small sleep for responsiveness
        
        # Clear active winch action when done
        self._active_winch_action = None
        
        # When we finish waiting for an action, check if any position triggers referenced it
        if current_action_id:
            self._handle_reference_action_complete(current_action_id)

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

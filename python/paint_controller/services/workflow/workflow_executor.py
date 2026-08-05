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

import os
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Any

import yaml
from PySide6.QtCore import QThread, Signal

from .actions import ActionRegistry
from .completion import CompletionTracker
from .document_compile import load_workflow_mapping
from .hardware import HardwareControllers
from .scheduler import ActionScheduler, ScheduledAction


def _require_winch_length(hardware: HardwareControllers) -> float:
    """Read winch cable length or raise if the adapter is missing."""
    winch = hardware.winch
    if winch is None:
        raise RuntimeError("Winch controller not available")
    return float(winch.get_cable_length())


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

    def __init__(self, executor, scheduled_actions: list[ScheduledAction], all_scheduled: list[ScheduledAction]):
        super().__init__()
        self.executor = executor
        self.scheduled_actions = scheduled_actions
        self.all_scheduled = all_scheduled  # Store all actions for loop rebuilding
        self._stop_event = threading.Event()

    # Property wrapper so all existing self._stop_requested reads/writes work unchanged
    @property
    def _stop_requested(self) -> bool:
        return self._stop_event.is_set()

    @_stop_requested.setter
    def _stop_requested(self, value: bool) -> None:
        if value:
            self._stop_event.set()
        else:
            self._stop_event.clear()

    def run(self):
        """Run workflow execution."""
        try:
            self.executor._execute_scheduled_actions(self.scheduled_actions)
            if not self._stop_event.is_set():
                self.execution_finished.emit()
        except Exception as e:
            self.execution_error.emit(str(e))

    def request_stop(self):
        """Request thread to stop."""
        self._stop_event.set()

    def is_stop_requested(self) -> bool:
        """Check if stop was requested."""
        return self._stop_event.is_set()


class WorkFlowExecutor:
    """
    Executes workflows with improved architecture.

    Features:
    - Clean separation of concerns (scheduling, execution, hardware)
    - Pluggable action handlers
    - Support for parallel and sequential actions
    - Proper error handling and state management
    """

    def __init__(self, ros_node, hardware: HardwareControllers, logger=None):
        """
        Initialize workflow executor.

        Args:
            ros_node: ROS2 node instance (for logger and popup access)
            hardware: Pre-built HardwareControllers with wired controller adapters
            logger: Optional logger instance
        """
        # Threading primitives must be created first (properties depend on them)
        self._state_lock = threading.Lock()
        self._stop_event = threading.Event()

        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        # Initialize subsystems
        self.hardware = hardware
        self.action_registry = ActionRegistry(self.hardware, self.logger, ros_node)
        self.scheduler = ActionScheduler(self.logger, self.hardware)

        # State management (backing stores for thread-safe properties)
        self.current_workflow: dict[str, Any] | None = None
        self._current_state = ExecutionState.IDLE
        self._current_action_index_val = -1
        self.execution_thread: WorkFlowExecutionThread | None = None
        self._loop_enabled = False
        self._loop_iteration = 0

        # Position trigger tracking
        self._pending_position_triggers: list[ScheduledAction] = []  # Not yet activated
        self._active_position_triggers: dict[str, tuple] = {}  # ref_id -> (action, last_position)
        self._fired_position_triggers: set = set()  # action_ids that have fired

        # Wait-done completion (policy-driven; winch is a feedback reader consumer)
        self._completion = CompletionTracker(
            self.hardware,
            default_winch_tolerance=50.0,
            logger=self.logger,
        )
        self._winch_position_tolerance: float = 50.0  # used by must-complete winch checks

        # Must-complete action tracking (industry pattern: implicit dependencies)
        self._must_complete_actions: dict[
            str, ScheduledAction
        ] = {}  # action_id -> action (currently running and must finish)

    # --- Thread-safe property wrappers ---

    @property
    def current_state(self) -> ExecutionState:
        with self._state_lock:
            return self._current_state

    @current_state.setter
    def current_state(self, value: ExecutionState) -> None:
        with self._state_lock:
            self._current_state = value

    @property
    def current_action_index(self) -> int:
        with self._state_lock:
            return self._current_action_index_val

    @current_action_index.setter
    def current_action_index(self, value: int) -> None:
        with self._state_lock:
            self._current_action_index_val = value

    @property
    def _stop_requested(self) -> bool:
        return self._stop_event.is_set()

    @_stop_requested.setter
    def _stop_requested(self, value: bool) -> None:
        if value:
            self._stop_event.set()
        else:
            self._stop_event.clear()

    def load_workflow(self, yaml_path: str) -> bool:
        """
        Load workflow from YAML file.

        Args:
            yaml_path: Path to workflow YAML file

        Returns:
            True if loaded successfully
        """
        try:
            with open(yaml_path) as f:
                raw = yaml.safe_load(f)

            default_name = os.path.splitext(os.path.basename(yaml_path))[0]
            workflow = load_workflow_mapping(raw, default_name=default_name)
            self.current_workflow = workflow
            name = workflow.get("name", "unknown")
            self._loop_enabled = bool(workflow.get("loop", False))
            self._loop_iteration = 0

            loop_status = " (looping enabled)" if self._loop_enabled else ""
            step_count = len(workflow.get("steps") or [])
            action_count = len(workflow.get("actions") or [])
            self.logger.info(
                f"Loaded workflow: {name}{loop_status} ({step_count} steps → {action_count} actions)"
            )
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
            self._must_complete_actions = {}

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
            self._loop_iteration = 1

            self.execution_thread = WorkFlowExecutionThread(self, scheduled_actions, all_scheduled)
            self.execution_thread.execution_finished.connect(self._on_execution_finished)
            self.execution_thread.execution_error.connect(self._on_execution_error)
            self.execution_thread.start()

            total_actions = len(scheduled_actions) + len(self._pending_position_triggers)
            self.logger.info(
                f"Started workflow with {total_actions} actions ({len(self._pending_position_triggers)} position-triggered)"
            )
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

    def request_stop_nonblocking(self) -> bool:
        """Request stop without joining the execution thread (halt-safe).

        Always succeeds for halt idempotency: idle is a no-op success.
        """
        if self.current_state == ExecutionState.IDLE:
            return True

        self._stop_requested = True
        if self.execution_thread is not None:
            self.execution_thread.request_stop()

        # Flip state immediately so UI is not left PAUSED/RUNNING under latch.
        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1
        self._loop_iteration = 0
        self.logger.info("WorkFlow stop requested (non-blocking)")
        return True

    def stop(self) -> bool:
        """Stop workflow execution and wait for the worker (operator stop)."""
        if self.current_state == ExecutionState.IDLE:
            return False

        self._stop_requested = True
        if self.execution_thread:
            self.execution_thread.request_stop()
            self.execution_thread.wait(5000)  # Wait max 5 seconds

        self.current_state = ExecutionState.IDLE
        self.current_action_index = -1
        self._loop_iteration = 0
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

    def _execute_scheduled_actions(self, scheduled_actions: list[ScheduledAction]) -> None:
        """
        Execute scheduled actions in time order.

        Args:
            scheduled_actions: List of scheduled actions sorted by time
        """
        start_time = time.time()
        action_index = 0

        while True:  # Outer loop for workflow restarts
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

                # Publish the original workflow-order index, not the sorted schedule index.
                self.current_action_index = scheduled.action_index
                self._execute_action(scheduled)

                # Track must-complete actions
                if scheduled.must_complete_before_workflow_end:
                    self._must_complete_actions[scheduled.action_id] = scheduled
                    self.logger.debug(
                        f"Tracking must-complete action '{scheduled.action_id}' "
                        f"(will wait for completion before workflow ends)"
                    )

                # Determine wait time until next action or completion
                wait_until = self._calculate_wait_until(scheduled, action_index, scheduled_actions, start_time)

                # Wait via completion policy (timed / feedback / hybrid)
                self._wait_with_pause(wait_until, start_time, scheduled)

                action_index += 1

            # Wait for must-complete actions before finishing workflow
            # (Industry pattern: implicit dependency completion)
            self._wait_for_must_complete_actions(start_time)

            # Check if we should loop
            if self._loop_enabled and not self._stop_requested:
                with self._state_lock:
                    self._loop_iteration += 1
                self.logger.info(f"Starting loop iteration {self.get_loop_iteration()}")

                # Reset state for next iteration and rebuild position trigger lists
                self._active_position_triggers = {}
                self._fired_position_triggers = set()
                self._completion.clear()
                self._must_complete_actions = {}

                # Rebuild position trigger list from all_scheduled_actions
                # Access via current thread
                self._pending_position_triggers = []
                execution_thread = self.execution_thread
                if execution_thread is not None and hasattr(execution_thread, "all_scheduled"):
                    for action in execution_thread.all_scheduled:
                        if action.is_position_triggered:
                            self._pending_position_triggers.append(action)

                self.logger.debug(
                    f"Loop {self._loop_iteration}: Reset {len(self._pending_position_triggers)} position triggers"
                )

                # Restart from beginning
                action_index = 0
                start_time = time.time()
                continue

            break  # Exit loop if not looping or stop requested

        # Reset state (only reached when exiting)
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

            if not isinstance(action_type, str) or not action_type:
                self.logger.warn(f"Missing action type for: {action_name}")
                return

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
            current_position = _require_winch_length(self.hardware)
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
            current_position = _require_winch_length(self.hardware)
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
            self.current_action_index = trigger.action_index
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
            if self.ros_node and hasattr(self.ros_node, "show_popup"):
                self.ros_node.show_popup(
                    "Position Trigger Missed",
                    f"'{trigger.action_id}' fired late - didn't reach {trigger.position_trigger_mm:.0f}mm",
                    "error",
                    3000,
                )

            # Execute the action anyway
            self.current_action_index = trigger.action_index
            self._execute_action(trigger)
            self._fired_position_triggers.add(trigger.action_id)
            del self._active_position_triggers[trigger.action_id]

    def _calculate_wait_until(
        self,
        current_scheduled: ScheduledAction,
        current_index: int,
        scheduled_actions: list[ScheduledAction],
        start_time: float,
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
        scheduled: ScheduledAction | str | None = None,
    ) -> None:
        """
        Wait until completion policy is satisfied, handling pause and position triggers.

        Args:
            wait_until: Schedule end time (elapsed seconds from start_time)
            start_time: Execution start time
            scheduled: Scheduled action being waited on (or legacy action_id str)
        """
        if isinstance(scheduled, str) or scheduled is None:
            current_action_id = scheduled
            scheduled_obj = None
        else:
            current_action_id = scheduled.action_id
            scheduled_obj = scheduled

        if scheduled_obj is not None:
            self._completion.begin_from_scheduled(scheduled_obj, wait_until=wait_until)
        else:
            self._completion.clear()

        last_position_check = 0.0
        position_check_interval = 0.1  # 10Hz polling

        def has_active_triggers_for_action() -> bool:
            if not current_action_id:
                return False
            for _action_id, (trigger, _) in self._active_position_triggers.items():
                if trigger.position_reference_action == current_action_id:
                    return True
            return False

        while not self._stop_requested:
            current_time_elapsed = time.time() - start_time
            has_active_triggers = has_active_triggers_for_action()
            action_complete = self._completion.is_complete(current_time_elapsed)

            if action_complete and not has_active_triggers:
                break

            while self.current_state == ExecutionState.PAUSED and not self._stop_requested:
                time.sleep(0.1)

            if self._stop_requested:
                break

            current_time = time.time()
            if current_time - last_position_check >= position_check_interval:
                self._check_position_triggers()
                last_position_check = current_time

            time.sleep(0.05)

        self._completion.clear()

        if current_action_id and current_action_id in self._must_complete_actions:
            del self._must_complete_actions[current_action_id]
            self.logger.debug(f"Must-complete action '{current_action_id}' finished")

        if current_action_id:
            self._handle_reference_action_complete(current_action_id)

    def _wait_for_must_complete_actions(self, start_time: float) -> None:
        """
        Wait for all must-complete actions to finish before ending workflow.

        Industry pattern: Actions referenced by position triggers must complete
        before the workflow is considered done. This prevents premature completion
        when position triggers fire early.

        Args:
            start_time: Execution start time for logging
        """
        if not self._must_complete_actions:
            return

        action_names = [a.action_config.get("name", a.action_id) for a in self._must_complete_actions.values()]
        self.logger.info(
            f"Waiting for {len(self._must_complete_actions)} must-complete actions: {', '.join(action_names)}"
        )

        last_check = 0.0
        check_interval = 0.1

        while self._must_complete_actions and not self._stop_requested:
            # Handle pause
            while self.current_state == ExecutionState.PAUSED and not self._stop_requested:
                time.sleep(0.1)

            if self._stop_requested:
                break

            current_time = time.time()
            if current_time - last_check >= check_interval:
                # Check feedback completion for must-complete actions (policy-driven)
                actions_to_remove = []
                for action_id, action in self._must_complete_actions.items():
                    target = action.completion_target
                    if target is None:
                        target = action.winch_target_mm
                    reader = action.completion_reader
                    if reader is None and action.is_winch_action:
                        reader = "winch_cable_length"
                    if target is None or not reader:
                        continue
                    try:
                        reader_fn = self._completion._readers.get(reader)
                        if reader_fn is None:
                            continue
                        current_position = float(reader_fn())
                        tolerance = float(getattr(action, "completion_tolerance", self._winch_position_tolerance))
                        if abs(current_position - target) <= tolerance:
                            self.logger.info(
                                f"Must-complete action '{action_id}' reached target "
                                f"({current_position:.0f}, target={target:.0f})"
                            )
                            actions_to_remove.append(action_id)
                    except Exception as e:
                        self.logger.warn(f"Failed to check completion for '{action_id}': {e}")

                for action_id in actions_to_remove:
                    del self._must_complete_actions[action_id]

                last_check = current_time

            time.sleep(0.05)

        if self._must_complete_actions and not self._stop_requested:
            remaining = [a.action_config.get("name", a.action_id) for a in self._must_complete_actions.values()]
            self.logger.warn(
                f"Workflow ending with {len(remaining)} incomplete must-complete actions: {', '.join(remaining)}"
            )
        elif not self._stop_requested:
            self.logger.info("All must-complete actions finished")

    def is_loop_enabled(self) -> bool:
        """Check if current workflow has looping enabled."""
        return self._loop_enabled

    def get_loop_iteration(self) -> int:
        """Get current loop iteration number (1-indexed, 0 if not looping)."""
        with self._state_lock:
            return self._loop_iteration

    def cleanup(self) -> None:
        """Clean up executor resources."""
        self.stop()

#!/usr/bin/env python3
"""QML-facing runtime boundary for workflow execution and status."""

import time
from typing import Any, List

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer

from .workflow_executor import WorkFlowExecutor, ExecutionState
from .hardware import HardwareControllers
from .workflow_catalog import WorkflowCatalog


class WorkFlowRunner(QObject):
    """
    QML-accessible workflow runtime interface.

    Signals:
        workflow_list_changed: Emitted when available workflows change
        execution_state_changed: Emitted when execution state changes
        current_workflow_changed: Emitted when current workflow changes
        error_occurred: Emitted when an error occurs
    """

    workflow_list_changed = Signal()
    execution_state_changed = Signal(int)  # ExecutionState enum value
    current_workflow_changed = Signal(str)  # WorkFlow name
    current_action_index_changed = Signal(int)  # Current action index during execution
    current_action_details_changed = Signal()
    workflow_actions_changed = Signal()
    loop_iteration_changed = Signal(int)  # Loop iteration number
    loop_enabled_changed = Signal(bool)  # Loop enabled state changed
    workflow_runtime_changed = Signal(int)
    loaded_workflow_reload_state_changed = Signal(bool)
    error_occurred = Signal(str)  # Error message

    def __init__(self, ros_node, hardware: HardwareControllers, logger=None, catalog: WorkflowCatalog | None = None):
        """
        Initialize workflow runner.

        Args:
            ros_node: ROS2 node instance
            hardware: Pre-built HardwareControllers with wired controller adapters
            logger: Optional logger (uses ros_node.get_logger() if None)
        """
        super().__init__()
        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        self.executor = WorkFlowExecutor(ros_node, hardware, self.logger)
        self._catalog = catalog or WorkflowCatalog(logger=self.logger)
        self._owns_catalog = catalog is None
        self._catalog.workflow_list_changed.connect(self.workflow_list_changed.emit)
        self._current_workflow_name = ""
        self._workflow_actions: List[dict[str, Any]] = []
        self._current_action_index = -1
        self._last_execution_state = -1  # Track last emitted state
        self._last_loop_iteration = 0  # Track last emitted loop iteration
        self._workflow_start_time = 0.0  # Track when workflow started running
        self._workflow_runtime_seconds = 0
        self._loaded_workflow_needs_reload = False

        # Timer to monitor execution state and action index
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._update_execution_state)
        self._monitor_timer.start(100)  # Update every 100ms

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self) -> List[str]:
        """Get list of available workflow names."""
        return self._catalog.workflow_list

    @Property(str, notify=current_workflow_changed)
    def current_workflow(self) -> str:
        """Get name of currently loaded workflow."""
        return self._current_workflow_name

    @Property(int, notify=execution_state_changed)
    def execution_state(self) -> int:
        """Get current execution state (ExecutionState enum value)."""
        return self.executor.current_state.value

    @Property(bool, notify=loop_enabled_changed)
    def is_loop_enabled(self) -> bool:
        """Check if current workflow has looping enabled."""
        return self.executor.is_loop_enabled()

    @Property(int, notify=loop_iteration_changed)
    def loop_iteration(self) -> int:
        """Get current loop iteration number (1-indexed, 0 if not looping)."""
        return self.executor.get_loop_iteration()

    @Property(int, notify=workflow_runtime_changed)
    def workflow_runtime(self) -> int:
        """Get workflow runtime in seconds (returns 0 if not running)."""
        return self._workflow_runtime_seconds

    @Property(list, notify=workflow_actions_changed)
    def workflow_actions(self) -> List[dict]:
        """Get cached workflow action summaries in workflow order."""
        return self._workflow_actions

    @Property(int, notify=workflow_actions_changed)
    def workflow_action_count(self) -> int:
        """Get number of actions in the currently loaded workflow."""
        return len(self._workflow_actions)

    @Property(str, notify=current_action_details_changed)
    def current_action_name(self) -> str:
        """Get the name of the currently executing action."""
        action = self._get_current_action()
        return action["name"] if action else ""

    @Property(str, notify=current_action_details_changed)
    def current_action_description(self) -> str:
        """Get the description of the currently executing action."""
        action = self._get_current_action()
        return action["description"] if action else ""

    @Property(int, notify=current_action_details_changed)
    def current_action_number(self) -> int:
        """Get the 1-based number of the current action, or 0 when idle."""
        action = self._get_current_action()
        return int(action["number"]) if action else 0

    @Property(str, notify=current_action_details_changed)
    def current_action_display(self) -> str:
        """Get numbered current-action text for operator display."""
        action = self._get_current_action()
        return action["display_name"] if action else ""

    @Property(str, notify=current_action_details_changed)
    def workflow_progress_text(self) -> str:
        """Get current workflow progress text for operator display."""
        action = self._get_current_action()
        if not action:
            return ""
        return f"{action['number']} / {len(self._workflow_actions)}"

    @Property(bool, notify=loaded_workflow_reload_state_changed)
    def loaded_workflow_needs_reload(self) -> bool:
        """Whether the loaded workflow document changed on disk and should be reloaded."""
        return self._loaded_workflow_needs_reload

    @Slot(str)
    def load_workflow(self, workflow_name: str) -> bool:
        """
        Load a workflow by name.

        Args:
            workflow_name: Name of workflow (without .yaml extension)

        Returns:
            True if loaded successfully, False otherwise
        """
        if self.executor.current_state in (ExecutionState.RUNNING, ExecutionState.PAUSED):
            error_msg = (
                "Cannot load a new workflow while execution is active; stop the current workflow first"
            )
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        if not self._catalog.contains(workflow_name):
            error_msg = f"WorkFlow not found: {workflow_name}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        workflow_path = self._catalog.resolve_workflow_path(workflow_name)
        if workflow_path is None:
            error_msg = f"WorkFlow file not found: {workflow_name}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        success = self.executor.load_workflow(workflow_path)

        if success:
            self._current_workflow_name = workflow_name
            self._rebuild_workflow_actions()
            self._set_current_action_index(-1)
            self._workflow_start_time = 0.0
            self._set_workflow_runtime_seconds(0)
            self._last_loop_iteration = 0
            self._set_loaded_workflow_needs_reload(False)
            self.current_workflow_changed.emit(workflow_name)
            self.loop_enabled_changed.emit(self.executor.is_loop_enabled())
            self.loop_iteration_changed.emit(0)  # Reset loop iteration on new load
        else:
            error_msg = f"Failed to load workflow: {workflow_name}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

        return success

    @Slot(result=list)
    def get_current_workflow_actions(self) -> List[dict]:
        """
        Compatibility wrapper for the deprecated direct action-summary read path.
        """
        return self._workflow_actions

    def can_save_workflow_document(self, workflow_name: str) -> tuple[bool, str | None]:
        """Return whether the named workflow document can be saved safely."""
        if workflow_name != self._current_workflow_name:
            return True, None

        if self.executor.current_state in (ExecutionState.RUNNING, ExecutionState.PAUSED):
            return False, (
                f"Cannot save workflow '{workflow_name}' while it is running or paused; "
                "stop it or load a different workflow first"
            )

        return True, None

    def can_delete_workflow_document(self, workflow_name: str) -> tuple[bool, str | None]:
        """Return whether the named workflow document can be deleted safely."""
        if workflow_name != self._current_workflow_name:
            return True, None

        return False, (
            f"Cannot delete workflow '{workflow_name}' while it is loaded; "
            "load a different workflow first"
        )

    def mark_workflow_document_saved(self, workflow_name: str) -> None:
        """Mark the loaded workflow snapshot stale after an editor save."""
        if workflow_name == self._current_workflow_name:
            self._set_loaded_workflow_needs_reload(True)

    def _get_current_action(self) -> dict[str, Any] | None:
        if self._current_action_index < 0:
            return None
        if self._current_action_index >= len(self._workflow_actions):
            return None
        return self._workflow_actions[self._current_action_index]

    def _rebuild_workflow_actions(self) -> None:
        actions = []
        workflow = self.executor.current_workflow or {}

        for index, action in enumerate(workflow.get("actions", [])):
            action_type = action.get("type", "Unknown")
            params = action.get("params", {})
            description = self._generate_action_description(action_type, params, action)
            name = action.get("name", action.get("id", f"Action {index + 1}"))

            actions.append(
                {
                    "action_id": action.get("id", f"action_{index}"),
                    "index": index,
                    "number": index + 1,
                    "name": name,
                    "display_name": f"{index + 1}. {name}",
                    "type": action_type,
                    "description": description,
                    "desc": description,
                }
            )

        self._workflow_actions = actions
        self.workflow_actions_changed.emit()
        self.current_action_details_changed.emit()

    def _set_current_action_index(self, new_index: int) -> None:
        if new_index == self._current_action_index:
            return
        self._current_action_index = new_index
        self.current_action_index_changed.emit(new_index)
        self.current_action_details_changed.emit()

    def _set_workflow_runtime_seconds(self, runtime_seconds: int) -> None:
        if runtime_seconds == self._workflow_runtime_seconds:
            return
        self._workflow_runtime_seconds = runtime_seconds
        self.workflow_runtime_changed.emit(runtime_seconds)

    def _set_loaded_workflow_needs_reload(self, needs_reload: bool) -> None:
        if needs_reload == self._loaded_workflow_needs_reload:
            return
        self._loaded_workflow_needs_reload = needs_reload
        self.loaded_workflow_reload_state_changed.emit(needs_reload)
    
    def _generate_action_description(self, action_type: str, params: dict, action: dict) -> str:
        """
        Generate human-readable description from action parameters.
        
        Args:
            action_type: Type of action
            params: Action parameters
            action: Full action config (for additional fields)
            
        Returns:
            Formatted description string with timing information
        """
        # Use explicit description if provided
        base_desc = action.get("description", "")
        
        if not base_desc:
            # Generate description based on action type
            if action_type in ("winch_absolute", "winch_move_absolute"):
                length = params.get("length", 0)
                speed = params.get("speed", 1)
                base_desc = f"Move to {length}mm at {speed}mm/s"
            
            elif action_type == "winch_increment":
                length = params.get("length", 0)
                speed = params.get("speed", 1)
                direction = "up" if length < 0 else "down"
                base_desc = f"Move {abs(length)}mm {direction} at {speed}mm/s"
            
            elif action_type == "valve_turn":
                turn_value = params.get("turn_value", 0.0)
                if turn_value == 0.0:
                    base_desc = "Close valve"
                else:
                    base_desc = f"Open valve to {turn_value:.1f}"
            
            elif action_type in ("spray_gimbal", "teensy_gimbal"):
                angle = params.get("angle", 0)
                speed = params.get("speed", 10)
                base_desc = f"Gimbal to {angle}° at {speed}°/s"
            
            elif action_type in ("arm_extend", "teensy_arm_extend"):
                distance = params.get("distance", 0)
                base_desc = f"Extend arm to {distance}mm"
            
            elif action_type == "ef_force":
                fx = params.get("fx", 0.0)
                fy = params.get("fy", 0.0)
                base_desc = f"Set force Fx={fx:.1f}, Fy={fy:.1f}"
            
            # Default: show all parameters
            elif params:
                param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                base_desc = param_str
            else:
                base_desc = "No parameters"
        
        # Add timing information
        timing_parts = []
        
        # Add estimated duration if present
        estimated_duration = action.get("estimated_duration")
        if estimated_duration is not None:
            duration_sec = estimated_duration / 1000.0
            if duration_sec < 1:
                timing_parts.append(f"~{estimated_duration}ms")
            else:
                timing_parts.append(f"~{duration_sec:.1f}s")
        
        # Add trigger/offset information if present
        trigger = action.get("trigger")
        if trigger:
            ref_action = trigger.get("reference_action", "?")
            timing_mode = trigger.get("timing_mode", "after_start")
            offset_ms = trigger.get("offset_ms", 0)
            
            # Build timing description
            if timing_mode == "before_complete":
                offset_sec = offset_ms / 1000.0
                if offset_sec < 1:
                    timing_parts.append(f"{offset_ms}ms before '{ref_action}' completes")
                else:
                    timing_parts.append(f"{offset_sec:.1f}s before '{ref_action}' completes")
            elif timing_mode == "after_complete":
                if offset_ms > 0:
                    offset_sec = offset_ms / 1000.0
                    if offset_sec < 1:
                        timing_parts.append(f"{offset_ms}ms after '{ref_action}' completes")
                    else:
                        timing_parts.append(f"{offset_sec:.1f}s after '{ref_action}' completes")
                else:
                    timing_parts.append(f"after '{ref_action}' completes")
            elif timing_mode == "after_start":
                if offset_ms > 0:
                    offset_sec = offset_ms / 1000.0
                    if offset_sec < 1:
                        timing_parts.append(f"{offset_ms}ms after '{ref_action}' starts")
                    else:
                        timing_parts.append(f"{offset_sec:.1f}s after '{ref_action}' starts")
                else:
                    timing_parts.append(f"with '{ref_action}'")
        
        # Combine base description with timing information
        if timing_parts:
            return f"{base_desc} ({', '.join(timing_parts)})"
        
        return base_desc

    @Slot()
    def play(self) -> bool:
        """Start workflow execution."""
        if not self._current_workflow_name:
            error_msg = "No workflow loaded"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        success = self.executor.play()

        if success:
            self._workflow_start_time = time.time()
            self.execution_state_changed.emit(self.executor.current_state.value)
        else:
            error_msg = "Failed to start workflow execution"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

        return success

    @Slot()
    def pause(self) -> bool:
        """Pause workflow execution."""
        success = self.executor.pause()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)
        else:
            error_msg = "Failed to pause workflow execution"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

        return success

    @Slot()
    def resume(self) -> bool:
        """Resume paused workflow execution."""
        success = self.executor.resume()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)
        else:
            error_msg = "Failed to resume workflow execution"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

        return success

    @Slot()
    def stop(self) -> bool:
        """Stop workflow execution and perform emergency shutdown."""
        success = self.executor.stop()

        if success:
            # Emergency shutdown: stop winch and close valve
            self._emergency_shutdown()
            self._workflow_start_time = 0.0
            self.execution_state_changed.emit(self.executor.current_state.value)
        else:
            error_msg = "Failed to stop workflow execution"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)

        return success
    
    def _emergency_shutdown(self) -> None:
        """Perform emergency shutdown of critical systems.
        
        Each controller is stopped independently so a failure in one
        does not prevent the others from being stopped.
        """
        hardware = self.executor.hardware

        # Stop winch immediately
        try:
            if hardware.winch:
                hardware.winch.move_absolute(0, 1)  # Move to 0mm at minimum speed
                self.logger.info("Emergency stop: Winch moving to retracted position")
        except Exception as e:
            self.logger.error(f"Emergency stop: Failed to stop winch: {e}")
        
        # Close valve immediately
        try:
            if hardware.teensy:
                hardware.teensy.set_valve_turn(0.0)
                self.logger.info("Emergency stop: Valve closed")
        except Exception as e:
            self.logger.error(f"Emergency stop: Failed to close valve: {e}")

    @Property(int, notify=current_action_index_changed)
    def current_action_index(self) -> int:
        """Get index of currently executing action (-1 if not running)."""
        return self._current_action_index

    def _update_execution_state(self) -> None:
        """Monitor and update execution state and action index."""
        # Update action index
        new_index = self.executor.current_action_index
        self._set_current_action_index(new_index)
        
        # Update loop iteration
        new_loop_iteration = self.executor.get_loop_iteration()
        if new_loop_iteration != self._last_loop_iteration:
            self._last_loop_iteration = new_loop_iteration
            self.loop_iteration_changed.emit(new_loop_iteration)
        
        # Update execution state
        current_state = self.executor.current_state.value
        if current_state != self._last_execution_state:
            self._last_execution_state = current_state
            self.execution_state_changed.emit(current_state)
            
            # Log state transitions
            state_names = {0: "Idle", 1: "Running", 2: "Paused", 3: "Completed", 4: "Error"}
            state_name = state_names.get(current_state, "Unknown")
            self.logger.info(f"Execution state changed to: {state_name}")

        runtime_seconds = 0
        if current_state == ExecutionState.RUNNING.value:
            runtime_seconds = int(time.time() - self._workflow_start_time)
        self._set_workflow_runtime_seconds(runtime_seconds)

    @Slot()
    def refresh_workflow_list(self) -> None:
        """Manually refresh workflow list (callable from QML)."""
        self._catalog.refresh_workflow_list()

    def cleanup(self) -> None:
        """Clean up runner resources."""
        self._monitor_timer.stop()
        if self._owns_catalog:
            self._catalog.cleanup()
        self.executor.cleanup()

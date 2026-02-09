#!/usr/bin/env python3
"""
WorkFlow Runner Node for paint controller.

Provides QML-accessible interface for workflow management (play, pause, stop, list).
"""

import os
import yaml
import json
import time
from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QFileSystemWatcher

from .workflow_executor import WorkFlowExecutor, ExecutionState


class WorkFlowRunner(QObject):
    """
    QML-accessible workflow management interface.

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
    loop_iteration_changed = Signal(int)  # Loop iteration number
    loop_enabled_changed = Signal(bool)  # Loop enabled state changed
    error_occurred = Signal(str)  # Error message

    def __init__(self, ros_node, logger=None):
        """
        Initialize workflow runner.

        Args:
            ros_node: ROS2 node instance (RobotController)
            logger: Optional logger (uses ros_node.get_logger() if None)
        """
        super().__init__()
        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        self.executor = WorkFlowExecutor(ros_node, self.logger)
        self._workflow_list: List[str] = []
        self._current_workflow_name = ""
        self._current_action_index = -1
        self._last_execution_state = -1  # Track last emitted state
        self._last_loop_iteration = 0  # Track last emitted loop iteration
        self._workflow_start_time = 0.0  # Track when workflow started running
        self._workflows_dir = self._find_workflows_dir()

        # Set up file system watcher to monitor workflow directory
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.addPath(self._workflows_dir)
        self._file_watcher.directoryChanged.connect(self._on_directory_changed)
        
        # Load available workflows
        self._refresh_workflow_list()

        # Timer to monitor execution state and action index
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._update_execution_state)
        self._monitor_timer.start(100)  # Update every 100ms



    def _find_workflows_dir(self) -> str:
        """Find workflows directory relative to package."""
        # Try common paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "resource", "workflows"),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resource", "workflows"
            ),
            "./workflows",
        ]

        for path in possible_paths:
            if os.path.isdir(path):
                self.logger.info(f"Found workflows directory: {path}")
                return path

        # Create default if not found
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "resource", "workflows"
        )
        os.makedirs(default_path, exist_ok=True)
        self.logger.warn(f"Created workflows directory: {default_path}")
        return default_path

    def _on_directory_changed(self, path: str) -> None:
        """Handle directory changes (file added/removed/modified)."""
        self.logger.info(f"WorkFlow directory changed: {path}")
        self._refresh_workflow_list()

    def _refresh_workflow_list(self) -> None:
        """Refresh list of available trajectories from disk."""
        try:
            new_list = [
                Path(f).stem
                for f in os.listdir(self._workflows_dir)
                if f.endswith(".yaml") or f.endswith(".yml")
            ]
            
            # Only update and emit if list actually changed
            if new_list != self._workflow_list:
                self._workflow_list = new_list
                self.logger.info(f"WorkFlow list updated: {len(self._workflow_list)} workflows found")
                self.workflow_list_changed.emit()
        except Exception as e:
            self.logger.error(f"Error refreshing workflow list: {e}")
            self._workflow_list = []

    @Property(list, notify=workflow_list_changed)
    def workflow_list(self) -> List[str]:
        """Get list of available workflow names."""
        return self._workflow_list

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

    @Property(int, constant=False)
    def workflow_runtime(self) -> int:
        """Get workflow runtime in seconds (returns 0 if not running)."""
        if self.executor.current_state.value == 1:  # RUNNING
            return int(time.time() - self._workflow_start_time)
        return 0

    @Slot(str)
    def load_workflow(self, workflow_name: str) -> bool:
        """
        Load a workflow by name.

        Args:
            workflow_name: Name of workflow (without .yaml extension)

        Returns:
            True if loaded successfully, False otherwise
        """
        if workflow_name not in self._workflow_list:
            error_msg = f"WorkFlow not found: {workflow_name}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yaml")

        if not os.path.exists(workflow_path):
            # Try .yml extension
            workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yml")

        if not os.path.exists(workflow_path):
            error_msg = f"WorkFlow file not found: {workflow_path}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        success = self.executor.load_workflow(workflow_path)

        if success:
            self._current_workflow_name = workflow_name
            self.current_workflow_changed.emit(workflow_name)
            self.loop_enabled_changed.emit(self.executor.is_loop_enabled())
            self.loop_iteration_changed.emit(0)  # Reset loop iteration on new load

        return success

    @Slot(result=list)
    def get_current_workflow_actions(self) -> List[dict]:
        """
        Get list of actions from currently loaded workflow.
        
        Returns:
            List of action dictionaries with name, type, and description with params
        """
        if not self.executor.current_workflow:
            return []
        
        actions = self.executor.current_workflow.get("actions", [])
        result = []
        
        for action in actions:
            action_type = action.get("type", "Unknown")
            params = action.get("params", {})
            
            # Generate dynamic description based on action type and parameters
            desc = self._generate_action_description(action_type, params, action)
            
            result.append({
                "name": action.get("name", "Unknown"),
                "type": action_type,
                "desc": desc
            })
        
        return result
    
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
            self.error_occurred.emit(error_msg)

        return success

    @Slot()
    def pause(self) -> bool:
        """Pause workflow execution."""
        success = self.executor.pause()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)

        return success

    @Slot()
    def resume(self) -> bool:
        """Resume paused workflow execution."""
        success = self.executor.resume()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)

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

        return success
    
    def _emergency_shutdown(self) -> None:
        """Perform emergency shutdown of critical systems."""
        try:
            # Stop winch immediately
            if hasattr(self.ros_node, 'winch_controller') and self.ros_node.winch_controller:
                self.ros_node.winch_controller.setSpeed(0.0)
                self.logger.info("Emergency stop: Winch speed set to 0")
            
            # Close valve immediately
            if hasattr(self.ros_node, 'esp32_valve_controller') and self.ros_node.esp32_valve_controller:
                self.ros_node.esp32_valve_controller.setValveTurn(0.0)
                self.logger.info("Emergency stop: Valve closed")
                
        except Exception as e:
            self.logger.error(f"Error during emergency shutdown: {e}")

    @Property(int, notify=current_action_index_changed)
    def current_action_index(self) -> int:
        """Get index of currently executing action (-1 if not running)."""
        return self._current_action_index

    def _update_execution_state(self) -> None:
        """Monitor and update execution state and action index."""
        # Update action index
        new_index = self.executor.current_action_index
        if new_index != self._current_action_index:
            self._current_action_index = new_index
            self.current_action_index_changed.emit(new_index)
        
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

    @Slot()
    def refresh_workflow_list(self) -> None:
        """Manually refresh workflow list (callable from QML)."""
        self._refresh_workflow_list()

    @Slot(str, result=str)
    def get_workflow_data(self, workflow_name: str) -> str:
        """
        Get full workflow data as JSON string.
        
        Args:
            workflow_name: Name of workflow (without .yaml extension)
            
        Returns:
            JSON string of workflow data or empty string on error
        """
        if workflow_name not in self._workflow_list:
            self.logger.error(f"WorkFlow not found: {workflow_name}")
            return ""
        
        workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yaml")
        if not os.path.exists(workflow_path):
            workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yml")
        
        if not os.path.exists(workflow_path):
            self.logger.error(f"WorkFlow file not found: {workflow_path}")
            return ""
        
        try:
            with open(workflow_path, 'r') as f:
                workflow_data = yaml.safe_load(f)
            return json.dumps(workflow_data)
        except Exception as e:
            self.logger.error(f"Error loading workflow data: {e}")
            return ""

    @Slot(str, str, result=bool)
    def save_workflow_data(self, workflow_name: str, workflow_json: str) -> bool:
        """
        Save workflow data from JSON string to YAML file.
        
        Args:
            workflow_name: Name for the workflow file (without extension)
            workflow_json: JSON string containing workflow data
            
        Returns:
            True if saved successfully
        """
        try:
            # Parse JSON to Python dict
            workflow_data = json.loads(workflow_json)
            
            # Ensure name matches
            workflow_data["name"] = workflow_name
            
            # Build file path
            workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yaml")
            
            # Save to YAML with better formatting
            with open(workflow_path, 'w') as f:
                yaml.dump(workflow_data, f, 
                         default_flow_style=False, 
                         sort_keys=False,
                         allow_unicode=True,
                         indent=2,
                         width=120)
            
            self.logger.info(f"Saved workflow: {workflow_path}")
            
            # Refresh list
            self._refresh_workflow_list()
            
            return True
            
        except Exception as e:
            error_msg = f"Error saving workflow: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    @Slot(str, result=bool)
    def delete_workflow(self, workflow_name: str) -> bool:
        """
        Delete a workflow file.
        
        Args:
            workflow_name: Name of workflow to delete (without extension)
            
        Returns:
            True if deleted successfully
        """
        if workflow_name not in self._workflow_list:
            error_msg = f"WorkFlow not found: {workflow_name}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False
        
        try:
            workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yaml")
            if not os.path.exists(workflow_path):
                workflow_path = os.path.join(self._workflows_dir, f"{workflow_name}.yml")
            
            if os.path.exists(workflow_path):
                os.remove(workflow_path)
                self.logger.info(f"Deleted workflow: {workflow_path}")
                self._refresh_workflow_list()
                return True
            else:
                error_msg = f"WorkFlow file not found: {workflow_name}"
                self.logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"Error deleting workflow: {e}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

    def cleanup(self) -> None:
        """Clean up runner resources."""
        self._monitor_timer.stop()
        if self._file_watcher:
            self._file_watcher.deleteLater()
        self.executor.cleanup()

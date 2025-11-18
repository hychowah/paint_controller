#!/usr/bin/env python3
"""
Trajectory Runner Node for paint controller.

Provides QML-accessible interface for trajectory management (play, pause, stop, list).
"""

import os
from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QFileSystemWatcher

from .trajectory_executor import TrajectoryExecutor, ExecutionState


class TrajectoryRunner(QObject):
    """
    QML-accessible trajectory management interface.

    Signals:
        trajectory_list_changed: Emitted when available trajectories change
        execution_state_changed: Emitted when execution state changes
        current_trajectory_changed: Emitted when current trajectory changes
        error_occurred: Emitted when an error occurs
    """

    trajectory_list_changed = Signal()
    execution_state_changed = Signal(int)  # ExecutionState enum value
    current_trajectory_changed = Signal(str)  # Trajectory name
    current_action_index_changed = Signal(int)  # Current action index during execution
    error_occurred = Signal(str)  # Error message

    def __init__(self, ros_node, logger=None):
        """
        Initialize trajectory runner.

        Args:
            ros_node: ROS2 node instance (RobotController)
            logger: Optional logger (uses ros_node.get_logger() if None)
        """
        super().__init__()
        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        self.executor = TrajectoryExecutor(ros_node, self.logger)
        self._trajectory_list: List[str] = []
        self._current_trajectory_name = ""
        self._current_action_index = -1
        self._last_execution_state = -1  # Track last emitted state
        self._trajectories_dir = self._find_trajectories_dir()

        # Set up file system watcher to monitor trajectory directory
        self._file_watcher = QFileSystemWatcher()
        self._file_watcher.addPath(self._trajectories_dir)
        self._file_watcher.directoryChanged.connect(self._on_directory_changed)
        
        # Load available trajectories
        self._refresh_trajectory_list()

        # Timer to monitor execution state and action index
        self._monitor_timer = QTimer()
        self._monitor_timer.timeout.connect(self._update_execution_state)
        self._monitor_timer.start(100)  # Update every 100ms



    def _find_trajectories_dir(self) -> str:
        """Find trajectories directory relative to package."""
        # Try common paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "resource", "trajectories"),
            os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resource", "trajectories"
            ),
            "./trajectories",
        ]

        for path in possible_paths:
            if os.path.isdir(path):
                self.logger.info(f"Found trajectories directory: {path}")
                return path

        # Create default if not found
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "..", "resource", "trajectories"
        )
        os.makedirs(default_path, exist_ok=True)
        self.logger.warn(f"Created trajectories directory: {default_path}")
        return default_path

    def _on_directory_changed(self, path: str) -> None:
        """Handle directory changes (file added/removed/modified)."""
        self.logger.info(f"Trajectory directory changed: {path}")
        self._refresh_trajectory_list()

    def _refresh_trajectory_list(self) -> None:
        """Refresh list of available trajectories from disk."""
        try:
            new_list = [
                Path(f).stem
                for f in os.listdir(self._trajectories_dir)
                if f.endswith(".yaml") or f.endswith(".yml")
            ]
            
            # Only update and emit if list actually changed
            if new_list != self._trajectory_list:
                self._trajectory_list = new_list
                self.logger.info(f"Trajectory list updated: {len(self._trajectory_list)} trajectories found")
                self.trajectory_list_changed.emit()
        except Exception as e:
            self.logger.error(f"Error refreshing trajectory list: {e}")
            self._trajectory_list = []

    @Property(list, notify=trajectory_list_changed)
    def trajectory_list(self) -> List[str]:
        """Get list of available trajectory names."""
        return self._trajectory_list

    @Property(str, notify=current_trajectory_changed)
    def current_trajectory(self) -> str:
        """Get name of currently loaded trajectory."""
        return self._current_trajectory_name

    @Property(int, notify=execution_state_changed)
    def execution_state(self) -> int:
        """Get current execution state (ExecutionState enum value)."""
        return self.executor.current_state.value

    @Slot(str)
    def load_trajectory(self, trajectory_name: str) -> bool:
        """
        Load a trajectory by name.

        Args:
            trajectory_name: Name of trajectory (without .yaml extension)

        Returns:
            True if loaded successfully, False otherwise
        """
        if trajectory_name not in self._trajectory_list:
            error_msg = f"Trajectory not found: {trajectory_name}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        trajectory_path = os.path.join(self._trajectories_dir, f"{trajectory_name}.yaml")

        if not os.path.exists(trajectory_path):
            # Try .yml extension
            trajectory_path = os.path.join(self._trajectories_dir, f"{trajectory_name}.yml")

        if not os.path.exists(trajectory_path):
            error_msg = f"Trajectory file not found: {trajectory_path}"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        success = self.executor.load_trajectory(trajectory_path)

        if success:
            self._current_trajectory_name = trajectory_name
            self.current_trajectory_changed.emit(trajectory_name)

        return success

    @Slot(result=list)
    def get_current_trajectory_actions(self) -> List[dict]:
        """
        Get list of actions from currently loaded trajectory.
        
        Returns:
            List of action dictionaries with name, type, and description with params
        """
        if not self.executor.current_trajectory:
            return []
        
        actions = self.executor.current_trajectory.get("actions", [])
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
            Formatted description string
        """
        # Use explicit description if provided
        if action.get("description"):
            return action["description"]
        
        # Generate description based on action type
        if action_type in ("winch_absolute", "winch_move_absolute"):
            length = params.get("length", 0)
            speed = params.get("speed", 1)
            return f"Move to {length}mm at {speed}mm/s"
        
        elif action_type == "winch_increment":
            length = params.get("length", 0)
            speed = params.get("speed", 1)
            direction = "up" if length < 0 else "down"
            return f"Move {abs(length)}mm {direction} at {speed}mm/s"
        
        elif action_type == "valve_turn":
            turn_value = params.get("turn_value", 0.0)
            if turn_value == 0.0:
                return "Close valve"
            else:
                return f"Open valve to {turn_value:.1f}"
        
        elif action_type in ("spray_gimbal", "teensy_gimbal"):
            angle = params.get("angle", 0)
            speed = params.get("speed", 10)
            return f"Gimbal to {angle}° at {speed}°/s"
        
        elif action_type in ("arm_extend", "teensy_arm_extend"):
            distance = params.get("distance", 0)
            return f"Extend arm to {distance}mm"
        
        elif action_type == "ef_force":
            fx = params.get("fx", 0.0)
            fy = params.get("fy", 0.0)
            return f"Set force Fx={fx:.1f}, Fy={fy:.1f}"
        
        # Default: show all parameters
        if params:
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            return param_str
        
        return "No parameters"

    @Slot()
    def play(self) -> bool:
        """Start trajectory execution."""
        if not self._current_trajectory_name:
            error_msg = "No trajectory loaded"
            self.logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            return False

        success = self.executor.play()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)
        else:
            error_msg = "Failed to start trajectory execution"
            self.error_occurred.emit(error_msg)

        return success

    @Slot()
    def pause(self) -> bool:
        """Pause trajectory execution."""
        success = self.executor.pause()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)

        return success

    @Slot()
    def resume(self) -> bool:
        """Resume paused trajectory execution."""
        success = self.executor.resume()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)

        return success

    @Slot()
    def stop(self) -> bool:
        """Stop trajectory execution and perform emergency shutdown."""
        success = self.executor.stop()

        if success:
            # Emergency shutdown: stop winch and close valve
            self._emergency_shutdown()
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
            if hasattr(self.ros_node, 'teensy_controller') and self.ros_node.teensy_controller:
                self.ros_node.teensy_controller.setValveTurn(0.0)
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
    def refresh_trajectory_list(self) -> None:
        """Manually refresh trajectory list (callable from QML)."""
        self._refresh_trajectory_list()

    def cleanup(self) -> None:
        """Clean up runner resources."""
        self._monitor_timer.stop()
        if self._file_watcher:
            self._file_watcher.deleteLater()
        self.executor.cleanup()

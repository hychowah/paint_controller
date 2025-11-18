#!/usr/bin/env python3
"""
Trajectory Runner Node for paint controller.

Provides QML-accessible interface for trajectory management (play, pause, stop, list).
"""

import os
from typing import List, Optional
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, Property

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
    error_occurred = Signal(str)  # Error message

    def __init__(self, ros_node, logger=None):
        """
        Initialize trajectory runner.

        Args:
            ros_node: ROS2 node instance
            logger: Optional logger (uses ros_node.get_logger() if None)
        """
        super().__init__()
        self.ros_node = ros_node
        self.logger = logger or ros_node.get_logger()

        self.executor = TrajectoryExecutor(ros_node, self.logger)
        self._trajectory_list: List[str] = []
        self._current_trajectory_name = ""
        self._trajectories_dir = self._find_trajectories_dir()

        # Load available trajectories
        self._refresh_trajectory_list()

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

    def _refresh_trajectory_list(self) -> None:
        """Refresh list of available trajectories from disk."""
        try:
            self._trajectory_list = [
                Path(f).stem
                for f in os.listdir(self._trajectories_dir)
                if f.endswith(".yaml") or f.endswith(".yml")
            ]
            self.logger.info(f"Found {len(self._trajectory_list)} trajectories: {self._trajectory_list}")
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
        """Stop trajectory execution."""
        success = self.executor.stop()

        if success:
            self.execution_state_changed.emit(self.executor.current_state.value)

        return success

    def cleanup(self) -> None:
        """Clean up runner resources."""
        self.executor.cleanup()

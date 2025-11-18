"""
Trajectory execution package for paint controller.

Provides YAML-based trajectory loading and execution with time-based sequencing.
"""

from .trajectory_executor import TrajectoryExecutor
from .trajectory_runner import TrajectoryRunner

__all__ = ['TrajectoryExecutor', 'TrajectoryRunner']

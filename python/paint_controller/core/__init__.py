"""Core application package.

Keep this package init lightweight so submodule imports do not pull PySide6,
ROS, or startup orchestration code through package-level re-exports.
"""

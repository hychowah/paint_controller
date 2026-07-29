"""Core application package.

Keep this package init lightweight so submodule imports do not pull PySide6,
ROS, or startup orchestration code through package-level re-exports.

Honesty (TD-055): ``core`` is composition + platform (runtime, settings, ROS
node, bridge wiring). Large QML façade construction lives in
``qml_context_composer`` for historical reasons — do not grow new business
rules here.
"""

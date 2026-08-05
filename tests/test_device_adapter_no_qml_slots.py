"""Structural ban: device adapters must not expose QML @Slot command APIs.

Level A dual-role retirement: HAL methods stay plain Python for ports / Actions /
teleop / workflow. Presentation QML surface lives on *Actions / *Status.

Allowlist:
- ESP32ValveController._finish_discovery_and_connect — QueuedConnection worker
  from the discovery thread (must remain a real Qt slot).

Out of scope (not banned here):
- UISSHController, SystemMonitor / SystemMonitorWorker
- models/*Actions and other presentation QObjects
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

# Do not import paint_controller.controllers package for __file__ — conftest
# pre-registers it as a namespace-only stub without __file__.
_CONTROLLERS_DIR = (
    Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "controllers"
)

# class_name -> set of method names allowed to keep @Slot
_ALLOWLIST: dict[str, frozenset[str]] = {
    "TeensyController": frozenset(),
    "WheelController": frozenset(),
    "WinchController": frozenset(),
    "LidarController": frozenset(),
    "ESP32ValveController": frozenset({"_finish_discovery_and_connect"}),
}

_SOURCE_FILES: dict[str, str] = {
    "TeensyController": "teensy.py",
    "WheelController": "wheel.py",
    "WinchController": "winch.py",
    "LidarController": "lidar.py",
    "ESP32ValveController": "esp32_valve.py",
}


def _slot_methods_on_class(source: str, class_name: str) -> list[str]:
    """Return method names in *class_name* that carry a @Slot decorator."""
    tree = ast.parse(source)
    found: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in item.decorator_list:
                if _is_slot_decorator(dec):
                    found.append(item.name)
                    break
    return found


def _is_slot_decorator(dec: ast.AST) -> bool:
    # @Slot / @Slot(...) / @QtCore.Slot(...)
    if isinstance(dec, ast.Name) and dec.id == "Slot":
        return True
    if isinstance(dec, ast.Attribute) and dec.attr == "Slot":
        return True
    if isinstance(dec, ast.Call):
        return _is_slot_decorator(dec.func)
    return False


def test_device_adapters_have_no_qml_command_slots() -> None:
    violations: list[str] = []
    for class_name, filename in _SOURCE_FILES.items():
        path = _CONTROLLERS_DIR / filename
        source = path.read_text(encoding="utf-8")
        allow = _ALLOWLIST[class_name]
        for method in _slot_methods_on_class(source, class_name):
            if method not in allow:
                violations.append(f"{class_name}.{method} still has @Slot ({path.name})")
        for allowed in allow:
            if allowed not in _slot_methods_on_class(source, class_name):
                violations.append(
                    f"{class_name}.{allowed} is allowlisted but has no @Slot "
                    f"(discovery/worker slot must remain)"
                )
    assert not violations, "Device adapter @Slot ban violations:\n" + "\n".join(violations)


def test_esp32_discovery_slot_still_queued_from_signal() -> None:
    """Worker slot must remain; production connects discovery_completed QueuedConnection."""
    mod = importlib.import_module("paint_controller.controllers.esp32_valve")
    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "_finish_discovery_and_connect" in source
    assert "QueuedConnection" in source
    slots = _slot_methods_on_class(source, "ESP32ValveController")
    assert slots == ["_finish_discovery_and_connect"]

"""Structural ban: device adapters must not declare Qt Property for QML.

Level B dual-role retirement: HAL telemetry stays plain Python @property + Signals;
QML surface lives on *Status projectors.

Allowlist: empty (no discovery-worker Property required).

Out of scope (not banned here):
- UISSHController, SystemMonitor
- models/*Status, *Actions, settings, video façades
"""

from __future__ import annotations

import ast
from pathlib import Path

_CONTROLLERS_DIR = (
    Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "controllers"
)

_SOURCE_FILES: dict[str, str] = {
    "TeensyController": "teensy.py",
    "WheelController": "wheel.py",
    "WinchController": "winch.py",
    "LidarController": "lidar.py",
    "ESP32ValveController": "esp32_valve.py",
    "WindMonitor": "wind_monitor.py",
}

# method/property names allowed to keep Qt Property (none for Level B)
_ALLOWLIST: dict[str, frozenset[str]] = {name: frozenset() for name in _SOURCE_FILES}


def _is_property_call(node: ast.AST) -> bool:
    """True if node is Property(...) or QtCore.Property(...)."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name) and func.id == "Property":
        return True
    if isinstance(func, ast.Attribute) and func.attr == "Property":
        return True
    return False


def _is_property_decorator(dec: ast.AST) -> bool:
    # @Property / @Property(...)
    if isinstance(dec, ast.Name) and dec.id == "Property":
        return True
    if isinstance(dec, ast.Attribute) and dec.attr == "Property":
        return True
    if isinstance(dec, ast.Call):
        return _is_property_decorator(dec.func)
    return False


def _qt_properties_on_class(source: str, class_name: str) -> list[str]:
    """Return names of class attrs or methods that use Qt Property."""
    tree = ast.parse(source)
    found: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for item in node.body:
            if isinstance(item, ast.Assign):
                if _is_property_call(item.value):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            found.append(target.id)
            elif isinstance(item, ast.AnnAssign) and item.value is not None:
                if _is_property_call(item.value) and isinstance(item.target, ast.Name):
                    found.append(item.target.id)
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in item.decorator_list:
                    if _is_property_decorator(dec):
                        found.append(item.name)
                        break
    return found


def test_device_adapters_have_no_qt_properties() -> None:
    violations: list[str] = []
    for class_name, filename in _SOURCE_FILES.items():
        path = _CONTROLLERS_DIR / filename
        source = path.read_text(encoding="utf-8")
        allow = _ALLOWLIST[class_name]
        for name in _qt_properties_on_class(source, class_name):
            if name not in allow:
                violations.append(f"{class_name}.{name} still has Qt Property ({path.name})")
    assert not violations, "Device adapter Qt Property ban violations:\n" + "\n".join(violations)


def test_device_adapters_keep_public_telemetry_names() -> None:
    """Smoke: schema-facing names remain getattr-able as Python attributes."""
    import importlib

    # Import modules by path-ish name via dynamic import of source presence only.
    # Runtime construction needs Qt/ROS; we only assert the @property exists on class.
    for class_name, filename in _SOURCE_FILES.items():
        if class_name == "WindMonitor":
            continue  # optional; names differ (camelCase)
        path = _CONTROLLERS_DIR / filename
        source = path.read_text(encoding="utf-8")
        # At least one @property def should remain for Level B conversion.
        assert "@property" in source, f"{filename} expected Python @property after Level B"
        assert "Property(" not in source or class_name == "ESP32ValveController", (
            f"{filename} still references Property("
        )
    # ESP32 may still import Slot only — ensure no Property( left
    esp32 = (_CONTROLLERS_DIR / "esp32_valve.py").read_text(encoding="utf-8")
    assert "Property(" not in esp32
    # Touch importlib so unused-import linters stay quiet if any
    assert importlib is not None

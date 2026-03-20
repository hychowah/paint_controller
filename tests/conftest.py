"""Fixtures shared across all tests.

Utils modules (crc.py, input.py) are pure Python with zero external
dependencies. We import them *directly* by pre-loading the utils subpackage
before paint_controller/__init__.py can trigger PySide6/ROS2 imports.
"""

import sys
import importlib
from pathlib import Path

# Add python/ directory to sys.path
_python_dir = Path(__file__).resolve().parent.parent / "python"
if str(_python_dir) not in sys.path:
    sys.path.insert(0, str(_python_dir))

# Pre-register the paint_controller package as a namespace-only module
# so that importing paint_controller.utils.* doesn't trigger __init__.py
import types
if "paint_controller" not in sys.modules:
    _pkg = types.ModuleType("paint_controller")
    _pkg.__path__ = [str(_python_dir / "paint_controller")]
    _pkg.__package__ = "paint_controller"
    sys.modules["paint_controller"] = _pkg

if "paint_controller.utils" not in sys.modules:
    _utils_pkg = types.ModuleType("paint_controller.utils")
    _utils_pkg.__path__ = [str(_python_dir / "paint_controller" / "utils")]
    _utils_pkg.__package__ = "paint_controller.utils"
    sys.modules["paint_controller.utils"] = _utils_pkg


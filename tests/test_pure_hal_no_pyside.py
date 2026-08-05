"""Structural ban: pure device HAL modules must not import PySide6 (Level C)."""

from __future__ import annotations

import ast
from pathlib import Path

_CONTROLLERS_DIR = (
    Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "controllers"
)

# Pure HAL modules (no Qt). Extended as Level C phases land.
_PURE_HAL_MODULES: tuple[str, ...] = (
    "lidar.py",
)


def _imports_pyside6(source: str) -> list[str]:
    tree = ast.parse(source)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("PySide6"):
                    found.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("PySide6"):
            found.append(node.module)
    return found


def test_pure_hal_modules_import_no_pyside6() -> None:
    violations: list[str] = []
    for name in _PURE_HAL_MODULES:
        path = _CONTROLLERS_DIR / name
        assert path.is_file(), f"missing pure HAL module {path}"
        hits = _imports_pyside6(path.read_text(encoding="utf-8"))
        for hit in hits:
            violations.append(f"{name}: imports {hit}")
    assert violations == [], "Pure HAL must not import PySide6:\n" + "\n".join(violations)

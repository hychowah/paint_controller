"""Qt runtime environment helpers."""

from __future__ import annotations

import os
from pathlib import Path

_DLL_DIR_HANDLES: list[object] = []


def ensure_pyside6_windows_dll_path() -> None:
    """Make PySide6's package DLLs visible to Windows before QML plugin loads."""
    if os.name != "nt" or not hasattr(os, "add_dll_directory"):
        return

    try:
        import PySide6
    except ModuleNotFoundError:
        return

    package_dir = Path(PySide6.__file__).resolve().parent
    package_dir_str = str(package_dir)
    if any(getattr(handle, "path", None) == package_dir_str for handle in _DLL_DIR_HANDLES):
        return

    _DLL_DIR_HANDLES.append(os.add_dll_directory(package_dir_str))
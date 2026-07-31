"""Integrity checks for the cross-layer action-key contract.

Ensures that action keys used in Python ``*Actions`` classes, the capability
catalog, and QML ``actionKey`` bindings stay in sync.
"""

from __future__ import annotations

import re
from pathlib import Path

from paint_controller.models.action_keys import ActionKey
from paint_controller.models.capability_catalog import _ACTION_CAPABILITIES

_MODELS_DIR = Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "models"
_QML_DIR = Path(__file__).resolve().parent.parent / "python" / "paint_controller" / "qml"

_ACTION_KEY_RE = re.compile(r"action_key\s*=\s*ActionKey\.([A-Z_]+)")
_CHECK_ACTION_RE = re.compile(r"check_action\(ActionKey\.([A-Z_]+)")
_QML_ACTION_KEY_RE = re.compile(r'actionKey:\s*"([^"]+)"')

_AUTHORITY_CLASS_MAP: dict[str, tuple[str, str]] = {
    "baseTopViewActions": ("base_top_view_actions", "BaseTopViewActions"),
    "tuningActions": ("tuning_actions", "TuningActions"),
    "wheelActions": ("wheel_actions", "WheelActions"),
    "winchActions": ("winch_actions", "WinchActions"),
    "teensyActions": ("teensy_actions", "TeensyActions"),
}


def _action_key_values() -> set[str]:
    return {member.value for member in ActionKey}


def _python_action_key_references() -> set[str]:
    """Collect ActionKey member names referenced in ``models/*_actions.py``."""
    references: set[str] = set()
    for path in _MODELS_DIR.glob("*_actions.py"):
        source = path.read_text()
        for match in _ACTION_KEY_RE.finditer(source):
            references.add(match.group(1))
        for match in _CHECK_ACTION_RE.finditer(source):
            references.add(match.group(1))
    return references


def _qml_action_key_values() -> set[str]:
    """Collect ``actionKey: "..."`` strings used in QML files."""
    values: set[str] = set()
    for path in _QML_DIR.rglob("*.qml"):
        source = path.read_text()
        for match in _QML_ACTION_KEY_RE.finditer(source):
            values.add(match.group(1))
    return values


def test_python_action_references_use_known_keys() -> None:
    known = {member.name for member in ActionKey}
    referenced = _python_action_key_references()
    unknown = referenced - known
    assert unknown == set(), f"Unknown ActionKey members referenced in models: {unknown}"


def test_python_action_keys_have_catalog_entries() -> None:
    catalog_keys = set(_ACTION_CAPABILITIES.keys())
    for member_name in _python_action_key_references():
        value = ActionKey[member_name].value
        assert value in catalog_keys, f"Action key {value!r} used in Python is missing from _ACTION_CAPABILITIES"


def test_catalog_keys_match_action_key_enum() -> None:
    catalog_keys = set(_ACTION_CAPABILITIES.keys())
    enum_values = _action_key_values()
    missing = catalog_keys - enum_values
    assert missing == set(), f"Catalog keys missing from ActionKey enum: {missing}"
    unused = enum_values - catalog_keys
    assert unused == set(), f"ActionKey enum values not present in catalog: {unused}"


def test_qml_action_keys_have_catalog_entries() -> None:
    catalog_keys = set(_ACTION_CAPABILITIES.keys())
    qml_keys = _qml_action_key_values()
    missing = qml_keys - catalog_keys
    assert missing == set(), f"QML actionKey values missing from _ACTION_CAPABILITIES: {missing}"


def test_catalog_authority_resolves_to_real_slot() -> None:
    """Every catalog authority string must resolve to a callable slot on the expected class.

    Authority may be either ``class.method`` or just ``class`` for actions that
    gate a whole family of property setters (e.g. base-top-view live adjustments).
    """
    for key, entry in _ACTION_CAPABILITIES.items():
        authority = entry.get("authority")
        assert isinstance(authority, str), f"{key}: authority must be a string"

        if "." in authority:
            class_name_qml, method_name = authority.split(".", 1)
        else:
            class_name_qml, method_name = authority, None

        mapping = _AUTHORITY_CLASS_MAP.get(class_name_qml)
        assert mapping is not None, f"{key}: unknown authority class {class_name_qml!r}"
        module_name, class_name_py = mapping

        module = __import__(f"paint_controller.models.{module_name}", fromlist=[class_name_py])
        cls = getattr(module, class_name_py, None)
        assert cls is not None, f"{key}: class {class_name_py} not found"

        if method_name is not None:
            method = getattr(cls, method_name, None)
            assert method is not None, f"{key}: method {method_name!r} not found on {class_name_py}"
            assert callable(method), f"{key}: {class_name_py}.{method_name} is not callable"

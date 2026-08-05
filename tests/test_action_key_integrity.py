"""Integrity checks for the cross-layer action-key contract.

Ensures that action keys used in Python ``*Actions`` classes, co-located
``ACTION_SCHEMAS``, the capability catalog, and QML ``actionKey`` bindings stay
in sync — including ``legalStateClass`` and ``authority`` parity.
"""

from __future__ import annotations

import re
from pathlib import Path

from paint_controller.handlers.policy.action_legality import ACTION_METADATA_OVERRIDES
from paint_controller.models.action_keys import ActionKey
from paint_controller.models.action_schema import ActionSchema
from paint_controller.models.base_top_view_actions import ACTION_SCHEMAS as BASE_TOP_SCHEMAS
from paint_controller.models.capability_catalog import _ACTION_CAPABILITIES
from paint_controller.models.teensy_actions import ACTION_SCHEMAS as TEENSY_SCHEMAS
from paint_controller.models.tuning_actions import ACTION_SCHEMAS as TUNING_SCHEMAS
from paint_controller.models.wheel_actions import ACTION_SCHEMAS as WHEEL_SCHEMAS
from paint_controller.models.winch_actions import ACTION_SCHEMAS as WINCH_SCHEMAS

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

_ALL_ACTION_SCHEMAS: dict[ActionKey, ActionSchema] = {}
for _part in (WINCH_SCHEMAS, WHEEL_SCHEMAS, TEENSY_SCHEMAS, TUNING_SCHEMAS, BASE_TOP_SCHEMAS):
    for _key, _schema in _part.items():
        assert _key not in _ALL_ACTION_SCHEMAS, f"Duplicate ACTION_SCHEMAS entry for {_key}"
        _ALL_ACTION_SCHEMAS[_key] = _schema

# Safety-class pins: resolved catalog base (before overrides) must keep these classes.
_PINNED_LEGAL_STATE_CLASSES: dict[str, str] = {
    ActionKey.WINCH_EMERGENCY_STOP.value: "emergency-exception",
    ActionKey.WINCH_MOVE_INCREMENT.value: "live-operational-motion",
    ActionKey.WINCH_MOVE_ABSOLUTE.value: "live-operational-motion",
    ActionKey.CAMERA_BASE_TOP_VIEW_LIVE_ADJUSTMENTS.value: "overlay-primary-calibration",
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


def test_every_gated_reference_has_action_schema() -> None:
    """Every ActionKey used at a gate site must have a co-located ActionSchema."""
    for member_name in _python_action_key_references():
        key = ActionKey[member_name]
        assert key in _ALL_ACTION_SCHEMAS, f"Gated ActionKey {key.value!r} missing from ACTION_SCHEMAS"


def test_schema_catalog_legal_state_and_authority_parity() -> None:
    """Schema authoring metadata must match catalog runtime base fields."""
    for key, schema in _ALL_ACTION_SCHEMAS.items():
        entry = _ACTION_CAPABILITIES.get(key.value)
        assert entry is not None, f"Schema key {key.value!r} missing from catalog"
        assert entry.get("legalStateClass") == schema.legal_state_class, (
            f"{key.value}: catalog legalStateClass {entry.get('legalStateClass')!r} "
            f"!= schema {schema.legal_state_class!r}"
        )
        assert entry.get("authority") == schema.authority, (
            f"{key.value}: catalog authority {entry.get('authority')!r} != schema {schema.authority!r}"
        )
        assert entry.get("title") == schema.title, (
            f"{key.value}: catalog title {entry.get('title')!r} != schema {schema.title!r}"
        )


def test_catalog_entries_have_matching_schemas() -> None:
    schema_values = {key.value for key in _ALL_ACTION_SCHEMAS}
    catalog_keys = set(_ACTION_CAPABILITIES.keys())
    missing = catalog_keys - schema_values
    assert missing == set(), f"Catalog keys without co-located ACTION_SCHEMAS: {missing}"


def test_pinned_safety_legal_state_classes() -> None:
    for action_key, expected_class in _PINNED_LEGAL_STATE_CLASSES.items():
        entry = _ACTION_CAPABILITIES[action_key]
        assert entry["legalStateClass"] == expected_class, (
            f"{action_key}: expected pinned legalStateClass {expected_class!r}, got {entry['legalStateClass']!r}"
        )


def test_overrides_win_over_catalog_for_known_keys() -> None:
    """Merge order: catalog base, then ACTION_METADATA_OVERRIDES last."""
    from paint_controller.handlers.policy.action_legality import resolve_action_metadata

    for action_key, override in ACTION_METADATA_OVERRIDES.items():
        catalog = _ACTION_CAPABILITIES.get(action_key, {})
        resolved = resolve_action_metadata(action_key, catalog_action=catalog)
        for field, value in override.items():
            assert resolved.get(field) == value, (
                f"Override for {action_key}.{field} did not win: got {resolved.get(field)!r}"
            )


def test_authority_class_map_covers_schema_authorities() -> None:
    for schema in _ALL_ACTION_SCHEMAS.values():
        class_name = schema.authority.split(".", 1)[0]
        assert class_name in _AUTHORITY_CLASS_MAP, (
            f"Schema authority class {class_name!r} missing from _AUTHORITY_CLASS_MAP"
        )


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


def test_gated_action_mixin_still_calls_check_action_explicitly() -> None:
    """Safety invariant: gate call remains visible in GatedActionMixin."""
    mixin_path = _MODELS_DIR / "gated_action_mixin.py"
    source = mixin_path.read_text()
    assert "check_action(action_key)" in source
    assert "def _run_gated" in source

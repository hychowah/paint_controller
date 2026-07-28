"""Schema integrity tests for paint_controller.core.settings."""

import ast
from pathlib import Path


_SETTINGS_PATH = Path(__file__).parent.parent / "python" / "paint_controller" / "core" / "settings.py"


def _read_settings_tree() -> ast.AST:
    return ast.parse(_SETTINGS_PATH.read_text())


def _get_schema() -> dict:
    tree = _read_settings_tree()
    for node in ast.walk(tree):
        target_name = None
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    value = node.value
        if target_name == "_SETTINGS_SCHEMA" and value is not None:
            return ast.literal_eval(value)
    raise RuntimeError("Could not find _SETTINGS_SCHEMA in settings.py")


def test_all_schema_entries_have_required_fields() -> None:
    schema = _get_schema()
    required = {"default", "type", "requires_restart", "description"}
    for key, meta in schema.items():
        missing = required - set(meta.keys())
        assert not missing, f"Setting '{key}' missing fields: {missing}"


def test_numeric_schema_entries_define_min_and_max() -> None:
    schema = _get_schema()
    for key, meta in schema.items():
        if meta["type"] in ("float", "int"):
            assert "min" in meta, f"Setting '{key}' (type={meta['type']}) missing 'min'"
            assert "max" in meta, f"Setting '{key}' (type={meta['type']}) missing 'max'"


def test_numeric_defaults_stay_within_declared_range() -> None:
    schema = _get_schema()
    for key, meta in schema.items():
        if meta["type"] in ("float", "int") and "min" in meta and "max" in meta:
            default = meta["default"]
            assert meta["min"] <= default <= meta["max"], (
                f"Setting '{key}': default {default} outside [{meta['min']}, {meta['max']}]"
            )


def test_schema_type_values_are_supported() -> None:
    schema = _get_schema()
    valid_types = {"float", "int", "bool", "dict", "list"}
    for key, meta in schema.items():
        assert meta["type"] in valid_types, f"Setting '{key}' has invalid type: {meta['type']}"


def test_signal_property_pairs_match_schema_entries() -> None:
    tree = _read_settings_tree()
    schema = _get_schema()
    signal_types = {"float", "int", "bool", "list"}

    generated_keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "_make_setting_pair":
                if node.args and isinstance(node.args[0], ast.Constant):
                    generated_keys.add(node.args[0].value)

    expected_keys = {key for key, meta in schema.items() if meta["type"] in signal_types}
    missing = expected_keys - generated_keys
    extra = generated_keys - expected_keys
    assert not missing, f"Schema entries without _make_setting_pair: {missing}"
    assert not extra, f"_make_setting_pair calls without schema entries: {extra}"


def test_legality_schema_defaults_off_for_development() -> None:
    """Development default: action legality enforcement off until hardening is done."""
    schema = _get_schema()
    assert schema["action_legality_enforced"]["default"] is False


def test_schema_source_has_no_duplicate_keys() -> None:
    tree = _read_settings_tree()
    for node in ast.walk(tree):
        target_name = None
        value = None
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target_name = node.target.id
            value = node.value
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    target_name = target.id
                    value = node.value
        if target_name == "_SETTINGS_SCHEMA" and isinstance(value, ast.Dict):
            keys = [key.value for key in value.keys if isinstance(key, ast.Constant)]
            assert len(keys) == len(set(keys)), "Duplicate schema keys found"
            return
    raise RuntimeError("Could not find _SETTINGS_SCHEMA dict literal")

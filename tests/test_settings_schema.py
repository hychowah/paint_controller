"""Tests for settings schema consistency and _make_setting_pair helper."""

import importlib
import sys
import types

# Import the module-level schema and helper directly (no PySide6 needed for schema tests)
# We need to test that schema keys match expected patterns


class TestSettingsSchema:
    """Verify settings schema integrity."""

    def _get_schema(self):
        """Load the schema dict by parsing the module source."""
        import ast
        from pathlib import Path

        settings_path = Path(__file__).parent.parent / "python" / "paint_controller" / "core" / "settings.py"
        source = settings_path.read_text()
        tree = ast.parse(source)

        # Find the _SETTINGS_SCHEMA assignment (annotated or plain)
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

    def test_all_entries_have_required_fields(self):
        schema = self._get_schema()
        required = {"default", "type", "requires_restart", "description"}
        for key, meta in schema.items():
            missing = required - set(meta.keys())
            assert not missing, f"Setting '{key}' missing fields: {missing}"

    def test_numeric_entries_have_min_max(self):
        schema = self._get_schema()
        for key, meta in schema.items():
            if meta["type"] in ("float", "int"):
                assert "min" in meta, f"Setting '{key}' (type={meta['type']}) missing 'min'"
                assert "max" in meta, f"Setting '{key}' (type={meta['type']}) missing 'max'"

    def test_defaults_within_range(self):
        schema = self._get_schema()
        for key, meta in schema.items():
            if meta["type"] in ("float", "int") and "min" in meta and "max" in meta:
                default = meta["default"]
                assert meta["min"] <= default <= meta["max"], (
                    f"Setting '{key}': default {default} outside [{meta['min']}, {meta['max']}]"
                )

    def test_type_values_are_valid(self):
        schema = self._get_schema()
        valid_types = {"float", "int", "bool", "dict", "list"}
        for key, meta in schema.items():
            assert meta["type"] in valid_types, f"Setting '{key}' has invalid type: {meta['type']}"

    def test_signal_property_pairs_match_schema(self):
        """Verify that every schema entry with a signal type has a corresponding
        _make_setting_pair call in the class body."""
        import ast
        from pathlib import Path

        settings_path = Path(__file__).parent.parent / "python" / "paint_controller" / "core" / "settings.py"
        source = settings_path.read_text()
        tree = ast.parse(source)

        schema = self._get_schema()
        signal_types = {"float", "int", "bool", "list"}

        # Find _make_setting_pair calls in the class body
        generated_keys = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id == "_make_setting_pair":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        generated_keys.add(node.args[0].value)

        # Every schema entry with a signal type should have a _make_setting_pair call
        expected_keys = {k for k, v in schema.items() if v["type"] in signal_types}
        missing = expected_keys - generated_keys
        extra = generated_keys - expected_keys
        assert not missing, f"Schema entries without _make_setting_pair: {missing}"
        assert not extra, f"_make_setting_pair calls without schema entries: {extra}"

    def test_no_duplicate_schema_keys(self):
        """Verify schema has no duplicate keys (Python dicts deduplicate, but check source)."""
        import ast
        from pathlib import Path

        settings_path = Path(__file__).parent.parent / "python" / "paint_controller" / "core" / "settings.py"
        source = settings_path.read_text()
        tree = ast.parse(source)

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
                keys = [k.value for k in value.keys if isinstance(k, ast.Constant)]
                assert len(keys) == len(set(keys)), f"Duplicate schema keys found"
                return
        raise RuntimeError("Could not find _SETTINGS_SCHEMA dict literal")

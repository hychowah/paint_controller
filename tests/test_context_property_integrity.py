"""Integrity checks for QML root-context property names and MainWindow aliases."""

from __future__ import annotations

import re
from pathlib import Path

from paint_controller.core.qml_context_composer import (
    CONTEXT_PROPERTIES,
    BundleProp,
    PortsProp,
    WrapperProp,
    _EXPECTED_CONTEXT_PROPERTY_NAMES,
)

_MAIN_WINDOW = (
    Path(__file__).resolve().parent.parent
    / "python"
    / "paint_controller"
    / "qml"
    / "core"
    / "MainWindow.qml"
)

_ALIAS_RE = re.compile(r"property\s+var\s+(\w+)Model\s*:\s*(\w+)")

# Root-context names used directly without a MainWindow *Model rebind.
_NO_MODEL_ALIAS = frozenset({"overlayHost"})


def test_expected_context_names_match_schema() -> None:
    assert _EXPECTED_CONTEXT_PROPERTY_NAMES == tuple(prop.name for prop in CONTEXT_PROPERTIES)


def test_context_property_names_unique() -> None:
    names = [prop.name for prop in CONTEXT_PROPERTIES]
    assert len(names) == len(set(names))


def test_mainwindow_model_aliases_match_context_properties() -> None:
    """MainWindow uses ``nameModel: name`` for injectible context roots."""
    source = _MAIN_WINDOW.read_text()
    aliases: dict[str, str] = {}
    for match in _ALIAS_RE.finditer(source):
        model_base, context_name = match.group(1), match.group(2)
        aliases[context_name] = model_base
        assert model_base == context_name, (
            f"MainWindow alias mismatch: property var {model_base}Model: {context_name}"
        )

    expected = set(_EXPECTED_CONTEXT_PROPERTY_NAMES) - _NO_MODEL_ALIAS
    missing = expected - set(aliases)
    extra = set(aliases) - set(_EXPECTED_CONTEXT_PROPERTY_NAMES)
    assert missing == set(), f"MainWindow missing *Model aliases for context props: {sorted(missing)}"
    assert extra == set(), f"MainWindow *Model aliases without CONTEXT_PROPERTIES: {sorted(extra)}"


def test_passthrough_props_are_bundle_or_ports() -> None:
    """Document the passthrough set used by smoke fake auto-wiring."""
    passthrough = [p.name for p in CONTEXT_PROPERTIES if isinstance(p, (BundleProp, PortsProp))]
    wrappers = [p.name for p in CONTEXT_PROPERTIES if isinstance(p, WrapperProp)]
    assert "wheelActions" in passthrough
    assert "videoRuntime" in wrappers
    assert "recordingStatus" in wrappers

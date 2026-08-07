"""Integrity checks for operator-guide catalog ↔ host ↔ input binding facts.

Keeps presentation copy from silently drifting away from Python-owned
double-press / exit-hold constants and from unknown guide context keys.
"""

from __future__ import annotations

import re
from pathlib import Path

from paint_controller.utils.constants import DEFAULT_EXIT_HOLD_DURATION_S
from paint_controller.utils.input import DEFAULT_DOUBLE_PRESS_THRESHOLD_S

_REPO = Path(__file__).resolve().parent.parent
_QML = _REPO / "python" / "paint_controller" / "qml"
_GUIDE_DIR = _QML / "overlays" / "guide"
_CATALOG = _GUIDE_DIR / "GuideCatalog.qml"
_GUIDE_HOST = _GUIDE_DIR / "GuideHost.qml"

_KNOWN_CONTEXTS = frozenset(
    {
        "ef",
        "base",
        "system_devices",
        "system_command",
        "system_settings",
        "system_workflow",
        "workflow_editor",
        "deck_buttons",
    }
)

# Hosts / catalog open paths — quoted string literals only.
_CONTEXT_STRING_RE = re.compile(
    r'openGuide\(\s*"([a-z_]+)"'
    r'|openOperatorGuideContext\(\s*"([a-z_]+)"'
    r'|"(system_[a-z_]+|workflow_editor|deck_buttons|ef|base)"'
)

_FEATURE_WORKSPACES = (
    _QML / "features" / "video" / "VideoFullscreenWorkspace.qml",
    _QML / "features" / "systemcontrol" / "SystemControlWorkspace.qml",
    _QML / "features" / "workflow" / "WorkflowEditorWorkspace.qml",
)


def _catalog_text() -> str:
    return _CATALOG.read_text(encoding="utf-8")


def _format_double_press_token(seconds: float) -> str:
    """Human token used in GuideCatalog bodies for the double-press window."""
    if seconds == int(seconds):
        return f"~{int(seconds)}s"
    return f"~{seconds}s"


def test_guide_host_owns_overlay_instantiation() -> None:
    """Feature roots mount GuideHost; only GuideHost creates OperatorGuideOverlay."""
    host_src = _GUIDE_HOST.read_text(encoding="utf-8")
    assert "OperatorGuideOverlay" in host_src
    assert "function openGuide" in host_src
    assert "function closeGuide" in host_src

    for path in _FEATURE_WORKSPACES:
        src = path.read_text(encoding="utf-8")
        assert "GuideHost" in src, f"{path.name} should use GuideHost"
        assert "OperatorGuideOverlay" not in src, (
            f"{path.name} must not instantiate OperatorGuideOverlay directly"
        )
        # Lifecycle belongs to GuideHost — no raw demand-load guide Loader blocks.
        assert "sourceComponent: operatorGuideComponent" not in src
        assert "sourceComponent: systemGuideComponent" not in src
        assert "sourceComponent: editorGuideComponent" not in src


def test_catalog_declares_all_known_context_packs() -> None:
    text = _catalog_text()
    for key in _KNOWN_CONTEXTS:
        assert f'"{key}"' in text, f"GuideCatalog missing context title/key {key!r}"
    # stepsFor switch arms for non-default packs
    for case in (
        "base",
        "system_devices",
        "system_command",
        "system_settings",
        "system_workflow",
        "workflow_editor",
        "deck_buttons",
    ):
        assert f'case "{case}":' in text, f"stepsFor missing case {case!r}"


def test_host_context_strings_are_known() -> None:
    found: set[str] = set()
    for path in _FEATURE_WORKSPACES:
        src = path.read_text(encoding="utf-8")
        for match in _CONTEXT_STRING_RE.finditer(src):
            value = next(g for g in match.groups() if g)
            found.add(value)

    unknown = found - _KNOWN_CONTEXTS
    assert not unknown, f"Host QML opens unknown guide context(s): {sorted(unknown)}"
    # At least the surface packs are referenced somewhere in hosts.
    for required in ("system_devices", "workflow_editor", "deck_buttons"):
        assert required in found, f"Expected host reference to context {required!r}"


def test_deck_binding_pins_match_python_sot() -> None:
    """Deck pack documents the same controls and double-press window as handlers."""
    text = _catalog_text()
    # Extract deck_buttons steps block roughly via property start → next major pack.
    start = text.find("readonly property var deckButtonSteps:")
    end = text.find("readonly property var workflowEditorSteps:")
    assert start >= 0 and end > start, "deckButtonSteps block not found"
    deck = text[start:end]

    for token in (
        'badge: "L1"',
        'badge: "L5 / R5"',
        'badge: "A ×2"',
        "Switch",
        "Double-press",
    ):
        assert token in deck, f"deck_buttons pack missing pin {token!r}"

    window_token = _format_double_press_token(DEFAULT_DOUBLE_PRESS_THRESHOLD_S)
    assert window_token in deck, (
        f"deck_buttons must mention double-press window {window_token!r} "
        f"(DEFAULT_DOUBLE_PRESS_THRESHOLD_S={DEFAULT_DOUBLE_PRESS_THRESHOLD_S})"
    )
    # Count: arm + base pos steps both document the window.
    assert deck.count(window_token) >= 2

    # Exit-hold duration is owned in Python; catalog must not invent a wrong number.
    # Allow omitting a numeric duration entirely (preferred) or matching the SOT.
    hold_matches = re.findall(
        r"(?:hold|holding)[^.]*?(\d+(?:\.\d+)?)\s*s",
        deck,
        flags=re.IGNORECASE,
    )
    for raw in hold_matches:
        value = float(raw)
        assert value == float(DEFAULT_EXIT_HOLD_DURATION_S), (
            f"Exit-hold duration in catalog ({value}) must match "
            f"DEFAULT_EXIT_HOLD_DURATION_S ({DEFAULT_EXIT_HOLD_DURATION_S})"
        )


def test_double_press_constant_is_positive() -> None:
    assert DEFAULT_DOUBLE_PRESS_THRESHOLD_S > 0
    assert DEFAULT_EXIT_HOLD_DURATION_S > 0

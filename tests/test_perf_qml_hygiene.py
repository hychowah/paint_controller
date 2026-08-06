"""Structural checks for QML performance hygiene slices (P-07, P-09)."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_QML = _REPO / "python" / "paint_controller" / "qml"


def test_digital_gauge_timer_gated_on_visible() -> None:
    """P-07: DigitalGauge history timer must not run when the item is hidden."""
    text = (_QML / "components" / "displays" / "DigitalGauge.qml").read_text(encoding="utf-8")
    assert "running: root.visible" in text
    assert "running: true" not in text.split("historyTimer")[1].split("onTriggered")[0]


def test_page_wheel_timer_gated_on_visible() -> None:
    """P-07: PageWheel decorative timer gated on page visibility."""
    text = (_QML / "pages" / "wheel" / "PageWheel.qml").read_text(encoding="utf-8")
    assert "running: page1Rect.visible" in text


def test_video_fullscreen_smooth_disabled() -> None:
    """P-09: live fullscreen video Image uses smooth: false."""
    text = (_QML / "features" / "video" / "VideoFullscreenWorkspace.qml").read_text(encoding="utf-8")
    # Ensure the live frame Image (not only unavailable icon) has smooth: false nearby.
    assert "id: videoFrame" in text
    frame_block = text.split("id: videoFrame", 1)[1].split("id: streamUnavailableIcon", 1)[0]
    assert "smooth: false" in frame_block

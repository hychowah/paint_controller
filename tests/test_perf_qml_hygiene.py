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


def test_page_wheel_rear_cam_demand_starts_stream() -> None:
    """P-02: PageWheel must call feeds.ensureStreamForImageUrl for rear/front switches."""
    text = (_QML / "pages" / "wheel" / "PageWheel.qml").read_text(encoding="utf-8")
    assert "ensureStreamForImageUrl" in text
    assert "onCamSourceChanged" in text
    assert "image://base_rear_live/frame" in text
    # REAR click path must not only set camSource without ensure (regression guard).
    rear_click = text.split("text: \"REAR\"", 1)[1].split("Rear camera button", 1)[0] if False else text
    # Both camSource assignment and ensure appear in the REAR onClicked block.
    rear_block = text.split('text: "REAR"', 1)[1].split("MouseArea", 1)[1].split("}", 4)[0]
    assert "base_rear_live" in rear_block
    assert "ensureStreamForImageUrl" in rear_block


def test_video_fullscreen_smooth_disabled() -> None:
    """P-09: live fullscreen dual Image layers use smooth: false."""
    text = (_QML / "features" / "video" / "VideoFullscreenWorkspace.qml").read_text(encoding="utf-8")
    for frame_id in ("efVideoFrame", "baseFrontVideoFrame", "baseRearVideoFrame"):
        assert f"id: {frame_id}" in text, f"missing live frame id {frame_id}"
        frame_block = text.split(f"id: {frame_id}", 1)[1].split("}", 1)[0]
        assert "smooth: false" in frame_block, f"{frame_id} must set smooth: false"

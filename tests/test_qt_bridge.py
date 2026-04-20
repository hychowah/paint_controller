"""Tests for paint_controller.core.qt_bridge.QtBridge.

QtBridge is the signal-based UI bridge that eliminates findChild() calls and
provides a clean Python→QML communication boundary.
"""

from __future__ import annotations

import importlib
from typing import Any, List, Tuple

from PySide6.QtCore import QObject


# ---------------------------------------------------------------------------
# Minimal fakes
# ---------------------------------------------------------------------------

class FakeEngine:
    """Minimal QQmlApplicationEngine double — only rootContext() is needed."""

    class _FakeContext:
        def setContextProperty(self, name, obj) -> None:
            pass

    def rootContext(self) -> "_FakeContext":
        return self._FakeContext()


class FakeStateStore(QObject):
    """Minimal StateStore double backed by actual QObject so signals work."""

    def __init__(self) -> None:
        super().__init__()
        self.control_mode: str = "base"

    @property
    def control_mode(self) -> str:
        return self._control_mode

    @control_mode.setter
    def control_mode(self, value: str) -> None:
        self._control_mode = value

    def __init__(self) -> None:
        super().__init__()
        self._control_mode = "base"


class FakeLogger:
    def debug(self, *args): pass
    def info(self, *args): pass
    def warning(self, *args): pass
    def error(self, *args): pass


class FakeBaseTopViewService:
    def __init__(self) -> None:
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value


class FakeInputHandler:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _qt_bridge_class():
    return importlib.import_module("paint_controller.core.qt_bridge").QtBridge


def _make_bridge(state_store=None, control_mode: str = "base") -> Any:
    """Create a QtBridge with all-fake dependencies."""
    ss = state_store or FakeStateStore()
    ss._control_mode = control_mode
    QtBridge = _qt_bridge_class()
    return QtBridge(engine=FakeEngine(), state_store=ss, logger=FakeLogger())


def _collect_signal(bridge: Any, signal_name: str) -> List:
    """Attach a slot to *signal_name* on *bridge* and return the capture list."""
    events: list = []
    getattr(bridge, signal_name).connect(lambda *args: events.append(args))
    return events


# ---------------------------------------------------------------------------
# Popup signals
# ---------------------------------------------------------------------------

def test_show_popup_emits_signal_with_correct_args(qt_app) -> None:
    bridge = _make_bridge()
    events: List[Tuple] = []
    bridge.showPopupRequested.connect(lambda title, msg, typ, delay: events.append((title, msg, typ, delay)))

    bridge.show_popup("My Title", "My Message", "warning", 500)

    assert len(events) == 1
    title, msg, typ, delay = events[0]
    assert title == "My Title"
    assert msg == "My Message"
    assert typ == "warning"
    assert delay == 500


def test_show_popup_default_args(qt_app) -> None:
    bridge = _make_bridge()
    events: List[Tuple] = []
    bridge.showPopupRequested.connect(lambda title, msg, typ, delay: events.append((title, msg, typ, delay)))

    bridge.show_popup("T", "M")

    assert len(events) == 1
    _, _, typ, delay = events[0]
    assert typ == "info"
    assert delay == 500  # default dismiss_delay from QtBridge.show_popup signature


def test_close_popup_emits_signal(qt_app) -> None:
    bridge = _make_bridge()
    closed: list = []
    bridge.closePopupRequested.connect(lambda: closed.append(True))

    bridge.close_popup()

    assert closed == [True]


# ---------------------------------------------------------------------------
# Sidebar signal
# ---------------------------------------------------------------------------

def test_toggle_sidebar_emits_signal(qt_app) -> None:
    bridge = _make_bridge()
    events = _collect_signal(bridge, "toggleSidebarRequested")

    bridge.toggle_sidebar()

    assert len(events) == 1


# ---------------------------------------------------------------------------
# Fullscreen / video source
# ---------------------------------------------------------------------------

def test_toggle_fullscreen_emits_ef_source_when_mode_is_ef(qt_app) -> None:
    """In EF mode, toggle_fullscreen must request the EF camera feed."""
    bridge = _make_bridge(control_mode="ef")
    events: list = []
    bridge.toggleVideoOverlayRequested.connect(lambda active, src: events.append((active, src)))

    bridge.toggle_fullscreen()

    assert len(events) == 1
    _, source = events[0]
    assert "ef" in source.lower() or "ef_live" in source


def test_toggle_fullscreen_emits_base_source_when_mode_is_base(qt_app) -> None:
    """In base mode, toggle_fullscreen must request the base front camera feed."""
    bridge = _make_bridge(control_mode="base")
    events: list = []
    bridge.toggleVideoOverlayRequested.connect(lambda active, src: events.append((active, src)))

    bridge.toggle_fullscreen()

    assert len(events) == 1
    _, source = events[0]
    assert "base" in source.lower() or "base_front" in source


def test_update_fullscreen_video_source_emits_correct_source_for_ef(qt_app) -> None:
    bridge = _make_bridge(control_mode="ef")
    events: list = []
    bridge.updateVideoSourceRequested.connect(lambda src: events.append(src))

    bridge.update_fullscreen_video_source()

    assert len(events) == 1
    assert "ef" in events[0].lower()


def test_update_fullscreen_video_source_emits_correct_source_for_base(qt_app) -> None:
    bridge = _make_bridge(control_mode="base")
    events: list = []
    bridge.updateVideoSourceRequested.connect(lambda src: events.append(src))

    bridge.update_fullscreen_video_source()

    assert len(events) == 1
    assert "base" in events[0].lower()


# ---------------------------------------------------------------------------
# Null-safe deferred wiring
# ---------------------------------------------------------------------------

def test_set_base_top_view_service_accepts_none_without_crash(qt_app) -> None:
    bridge = _make_bridge()
    bridge.set_base_top_view_service(None)  # must not raise


def test_set_input_handler_accepts_none_without_crash(qt_app) -> None:
    bridge = _make_bridge()
    bridge.set_input_handler(None)  # must not raise


def test_set_base_top_view_service_stores_instance(qt_app) -> None:
    bridge = _make_bridge()
    service = FakeBaseTopViewService()
    bridge.set_base_top_view_service(service)
    assert bridge._base_top_view_service is service


def test_set_input_handler_stores_instance(qt_app) -> None:
    bridge = _make_bridge()
    handler = FakeInputHandler()
    bridge.set_input_handler(handler)
    assert bridge._input_handler is handler


# ---------------------------------------------------------------------------
# toggle_lidar_overlay
# ---------------------------------------------------------------------------

def test_toggle_lidar_overlay_does_not_crash_without_base_top_view_service(qt_app) -> None:
    """toggle_lidar_overlay must guard against _base_top_view_service being None."""
    bridge = _make_bridge()
    assert bridge._base_top_view_service is None
    bridge.toggle_lidar_overlay()  # must not raise

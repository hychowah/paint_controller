"""Direct tests for SignalWiring."""

from __future__ import annotations

from paint_controller.core.signal_wiring import SignalWiring
from tests.controller_factory_runtime_support import (
    _ControlProcessorRecorder,
    _EmergencyHandlerRecorder,
    _InputHandlerRecorder,
    _QtBridgeRecorder,
    _SafetyCoordinatorRecorder,
    _StatusTimerRecorder,
    _SteamDeckHandlerRecorder,
    _SystemMonitorRecorder,
    _VideoHandlerRecorder,
    _WheelControllerRecorder,
)


def _make_runtime() -> object:
    """Return a minimal runtime-like object with the attributes SignalWiring needs."""
    runtime = type("Runtime", (), {})()
    runtime.node = type("Node", (), {"get_logger": lambda self: type("Logger", (), {"error": lambda *args: None})()})()
    runtime.state_store = _StateStoreRecorderForWiring()
    runtime.qt_bridge = _QtBridgeRecorder()
    runtime.video_stream_handler = _VideoHandlerRecorder()
    runtime.steam_deck_handler = _SteamDeckHandlerRecorder()
    runtime.overlay_host = _OverlayHostRecorderForWiring()
    runtime.video_runtime = _VideoRuntimeRecorderForWiring()
    runtime.config = type("Config", (), {"update_rate": 30.0})()
    runtime.status_timer = None
    runtime._deferred_video_startup = lambda: None

    runtime.bundle = type(
        "Bundle",
        (),
        {
            "input_handler": _InputHandlerRecorder(),
            "emergency_handler": _EmergencyHandlerRecorder(),
            "control_processor": _ControlProcessorRecorder(),
            "wheel_controller": _WheelControllerRecorder(),
            "safety_coordinator": _SafetyCoordinatorRecorder(),
            "system_monitor": _SystemMonitorRecorder(),
        },
    )()

    return runtime


class _StateStoreRecorderForWiring:
    def __init__(self) -> None:
        self.control_mode_changed = _SignalRecorderForWiring()
        self.control_mode = "ef"
        self.display_message = ""


class _SignalRecorderForWiring:
    def __init__(self) -> None:
        self.connections: list[tuple[object, tuple]] = []

    def connect(self, callback, *args) -> None:
        self.connections.append((callback, args))


class _OverlayHostRecorderForWiring:
    def __init__(self) -> None:
        self.sources: list[str] = []
        self.toggles: list[tuple[bool, str]] = []

    def set_video_fullscreen_source(self, source: str) -> None:
        self.sources.append(source)

    def toggle_video_fullscreen(self, source: str) -> None:
        self.toggles.append((True, source))


class _VideoRuntimeRecorderForWiring:
    def __init__(self) -> None:
        self.topBar = _VideoRuntimeTopBarRecorderForWiring()


class _VideoRuntimeTopBarRecorderForWiring:
    def __init__(self) -> None:
        self.endEffectorVideoRequested = _SignalRecorderForWiring()
        self.baseVideoRequested = _SignalRecorderForWiring()


def test_wire_registers_steam_deck_callbacks() -> None:
    runtime = _make_runtime()
    SignalWiring(runtime).wire()

    buttons = [button for button, _ in runtime.steam_deck_handler.callbacks]
    assert buttons == [
        "up", "down", "left", "right", "r4", "l4", "menu", "switch",
        "l5", "r5", "dot", "a", "l1",
    ]


def test_wire_connects_emergency_and_video_signals() -> None:
    runtime = _make_runtime()
    SignalWiring(runtime).wire()

    assert len(runtime.state_store.control_mode_changed.connections) == 1
    assert len(runtime.qt_bridge.status_updated.connections) == 1
    assert len(runtime.bundle.emergency_handler.overlay_changed.connections) == 1
    assert len(runtime.bundle.emergency_handler.emergency_triggered.connections) == 1
    assert len(runtime.video_stream_handler.endEffectorFrameReady.connections) == 1
    assert len(runtime.bundle.wheel_controller.error_state_changed.connections) == 1


def test_wire_without_ros_thread_stays_valid() -> None:
    """TD-039: fixtures may omit ros_thread; wiring must remain null-safe."""
    runtime = _make_runtime()
    assert not hasattr(runtime, "ros_thread") or runtime.ros_thread is None
    SignalWiring(runtime).wire()


def test_wire_connects_ros_thread_error_to_display_message(qt_app) -> None:
    """TD-039: RosThread.error_occurred surfaces on StateStore.display_message."""
    from PySide6.QtCore import QObject, Signal

    class _FakeRosThread(QObject):
        error_occurred = Signal(str)

    runtime = _make_runtime()
    runtime.ros_thread = _FakeRosThread()
    wiring = SignalWiring(runtime)
    wiring.wire()

    runtime.ros_thread.error_occurred.emit("spin failed once")
    qt_app.processEvents()

    assert runtime.state_store.display_message == "ROS: spin failed once"

    # Identical text is suppressed by the wiring throttle/dedupe.
    runtime.ros_thread.error_occurred.emit("spin failed once")
    qt_app.processEvents()
    assert runtime.state_store.display_message == "ROS: spin failed once"


def test_wire_connects_video_top_bar_requests() -> None:
    runtime = _make_runtime()
    SignalWiring(runtime).wire()

    assert len(runtime.video_runtime.topBar.endEffectorVideoRequested.connections) == 1
    assert len(runtime.video_runtime.topBar.baseVideoRequested.connections) == 1


def test_start_timers_creates_status_timer_and_starts_monitor(monkeypatch) -> None:
    from paint_controller.core import signal_wiring as signal_wiring_module

    timer_recorder = _StatusTimerRecorder()

    class _FakeQTimer:
        def __init__(self):
            nonlocal timer_recorder
            return None

        @staticmethod
        def singleShot(_ms: int, _callback) -> None:
            return None

    def fake_qtimer_factory():
        return timer_recorder
    fake_qtimer_factory.singleShot = lambda _ms, _callback: None
    monkeypatch.setattr(signal_wiring_module, "QTimer", fake_qtimer_factory)

    runtime = _make_runtime()
    SignalWiring(runtime).start_timers()

    assert runtime.status_timer is timer_recorder
    assert timer_recorder.started is True
    assert runtime.bundle.system_monitor.monitoring_started is True


def test_start_timers_requires_bundle() -> None:
    runtime = _make_runtime()
    runtime.bundle = None
    try:
        SignalWiring(runtime).start_timers()
        assert False, "start_timers() should require a bundle"
    except RuntimeError as exc:
        assert "ControllerBundle" in str(exc)
